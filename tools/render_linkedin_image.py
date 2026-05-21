#!/usr/bin/env python3
"""
render_linkedin_image.py — Deterministic LinkedIn hero card renderer.

Built for the Marketing / Presentation Designer agents in the Automatisierbar
Build Pipeline.  NOT an LLM — pure SVG layout from JSON input, rasterised via
cairosvg + Pillow.  Brand colours hardcoded from Automatisierbar_Brand_Guide
EXTERN copy.pdf (Version 1.0, 2026).

Usage:
    python tools/render_linkedin_image.py --input spec.json --output ./out.png

Input JSON schema:
{
  "kind":     "hero-card",                         (optional, default hero-card)
  "headline": "≤6 words",                          (required)
  "subtitle": "optional, ≤10 words",               (optional)
  "palette":  "green-on-deep | deep-on-light | light-on-green",  (default green-on-deep)
  "aspect":   "square | portrait | landscape",     (default square)
  "branding": "none | wordmark | logo"             (default none)
}

Output resolutions (native LinkedIn):
    square    1200 × 1200
    portrait  1080 × 1350
    landscape 1200 × 627

Render pipeline:
    Build SVG at native dimensions → cairosvg 2× → Pillow LANCZOS downsample
    → write PNG to --output.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from html import escape
from pathlib import Path

import cairosvg
from PIL import Image

# ---------------------------------------------------------------------------
# Brand palette — Automatisierbar_Brand_Guide EXTERN copy.pdf v1.0
# ---------------------------------------------------------------------------
PRIMARY_GREEN = "#15C97A"
PRIMARY_DARK  = "#0A8F54"
PRIMARY_DEEP  = "#063D25"
PRIMARY_LIGHT = "#D4F7E9"
OFF_WHITE     = "#F4FCF8"
NEUTRAL_BLACK = "#0C1410"

# ---------------------------------------------------------------------------
# Output dimensions keyed by aspect
# ---------------------------------------------------------------------------
DIMENSIONS: dict[str, tuple[int, int]] = {
    "square":    (1200, 1200),
    "portrait":  (1080, 1350),
    "landscape": (1200, 627),
}

# ---------------------------------------------------------------------------
# Palette mappings: (bg, headline_color, subtitle_color)
# ---------------------------------------------------------------------------
PALETTES: dict[str, tuple[str, str, str]] = {
    "green-on-deep": (PRIMARY_DEEP,  PRIMARY_GREEN, PRIMARY_LIGHT),
    "deep-on-light": (PRIMARY_LIGHT, PRIMARY_DEEP,  PRIMARY_DEEP),
    "light-on-green": (PRIMARY_GREEN, PRIMARY_DEEP,  PRIMARY_DEEP),
}

# ---------------------------------------------------------------------------
# Font sizes in design space (= native resolution)
# ---------------------------------------------------------------------------
FONT_HEADLINE_DEFAULT  = 80
FONT_HEADLINE_LANDSCAPE = 72
FONT_SUBTITLE_DEFAULT  = 52
FONT_SUBTITLE_LANDSCAPE = 44
FONT_BRANDING          = 24


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wrap_text(text: str, max_chars: int = 20) -> list[str]:
    """Word-wrap *text* into lines no longer than *max_chars*."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur = f"{cur} {word}"
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _svg_text(x: float, y: float, content: str, *,
              size: int,
              color: str,
              weight: str = "normal",
              anchor: str = "middle",
              family: str = "Helvetica Neue, Helvetica, Arial, sans-serif") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" '
        f'font-family="{family}" font-size="{size}" '
        f'fill="{color}" font-weight="{weight}" '
        f'text-anchor="{anchor}" dominant-baseline="auto">'
        f'{escape(content)}</text>'
    )


# ---------------------------------------------------------------------------
# SVG builder
# ---------------------------------------------------------------------------

def _build_svg(spec: dict) -> tuple[str, int, int]:
    """Return (svg_string, width, height) for the given spec dict."""
    aspect   = spec.get("aspect", "square") or "square"
    palette  = spec.get("palette", "green-on-deep") or "green-on-deep"
    branding = spec.get("branding", "none") or "none"
    headline = str(spec.get("headline", ""))
    subtitle = str(spec.get("subtitle", "") or "")

    # Validate / fall back to known keys
    if aspect not in DIMENSIONS:
        aspect = "square"
    if palette not in PALETTES:
        palette = "green-on-deep"
    if branding not in ("none", "wordmark", "logo"):
        branding = "none"

    W, H = DIMENSIONS[aspect]
    bg_color, hl_color, sub_color = PALETTES[palette]

    is_landscape = aspect == "landscape"
    font_hl  = FONT_HEADLINE_LANDSCAPE  if is_landscape else FONT_HEADLINE_DEFAULT
    font_sub = FONT_SUBTITLE_LANDSCAPE  if is_landscape else FONT_SUBTITLE_DEFAULT

    # Text padding — at least 5% of canvas width, minimum 40 px
    pad_x = max(40, int(W * 0.05))

    # Wrap headline at 20 chars
    hl_lines = _wrap_text(headline, max_chars=20)
    has_subtitle = bool(subtitle.strip())

    # Vertical layout
    # Line height approximation: font_size * 1.25
    hl_line_h = font_hl * 1.25
    sub_gap   = H * 0.08          # 8% of canvas height
    sub_line_h = font_sub * 1.25

    total_hl_h  = len(hl_lines) * hl_line_h
    total_sub_h = sub_line_h if has_subtitle else 0
    total_gap   = sub_gap    if has_subtitle else 0
    block_h     = total_hl_h + total_gap + total_sub_h

    # Centre block slightly above vertical centre (shift up by 3% of H)
    block_top = (H - block_h) / 2 - H * 0.03

    # SVG assembly
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {H}">'
    )

    # Full-bleed background
    parts.append(f'<rect width="{W}" height="{H}" fill="{bg_color}"/>')

    # Headline lines — centred horizontally
    cx = W / 2
    for i, line in enumerate(hl_lines):
        # Baseline offset: move down by (i+1) line heights, then up half a line
        # for visual balance (dominant-baseline auto → baseline at y)
        y = block_top + (i + 1) * hl_line_h
        parts.append(_svg_text(cx, y, line, size=font_hl, color=hl_color, weight="bold"))

    # Subtitle
    if has_subtitle:
        sub_y = block_top + total_hl_h + sub_gap + sub_line_h
        parts.append(_svg_text(cx, sub_y, subtitle.strip(),
                               size=font_sub, color=sub_color))

    # Decorative accent line at very bottom, 25% opacity
    accent_y = H - 2  # 2px from bottom edge so stroke is fully visible
    accent_color = hl_color  # matches headline accent
    parts.append(
        f'<line x1="0" y1="{accent_y}" x2="{W}" y2="{accent_y}" '
        f'stroke="{accent_color}" stroke-width="3.5" '
        f'stroke-opacity="0.25"/>'
    )

    # Branding (bottom-right corner)
    if branding in ("wordmark", "logo"):
        brand_margin_x = max(40, int(W * 0.04))
        brand_margin_y = max(40, int(H * 0.04))
        bx = W - brand_margin_x
        by = H - brand_margin_y
        brand_color = hl_color  # same as accent line

        if branding == "wordmark":
            parts.append(_svg_text(bx, by, "Automatisierbar",
                                   size=FONT_BRANDING, color=brand_color,
                                   weight="bold", anchor="end"))
        else:  # logo — small "A" monogram
            mono_r = FONT_BRANDING
            parts.append(
                f'<circle cx="{bx - mono_r:.1f}" cy="{by - mono_r * 0.35:.1f}" '
                f'r="{mono_r}" fill="none" '
                f'stroke="{brand_color}" stroke-width="2" '
                f'stroke-opacity="0.7"/>'
            )
            parts.append(_svg_text(bx - mono_r, by - mono_r * 0.35 + FONT_BRANDING * 0.38,
                                   "A", size=FONT_BRANDING, color=brand_color,
                                   weight="bold", anchor="middle"))

    parts.append("</svg>")
    return "\n".join(parts), W, H


# ---------------------------------------------------------------------------
# Render pipeline
# ---------------------------------------------------------------------------

def render(spec: dict, output_path: str) -> None:
    """Build SVG, rasterise at 2×, downsample to native, write PNG."""
    svg, W, H = _build_svg(spec)

    # Rasterise at 2× for anti-aliasing quality
    png_2x = cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        output_width=W * 2,
        output_height=H * 2,
    )

    # Downsample to native resolution with LANCZOS
    img = Image.open(io.BytesIO(png_2x)).resize((W, H), Image.LANCZOS)
    img.save(output_path, format="PNG", optimize=True)

    size_kb = Path(output_path).stat().st_size // 1024
    print(f"wrote {output_path}  ({W}×{H} px, {size_kb} KB)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Input reader
# ---------------------------------------------------------------------------

def _read_input(path: str | None) -> dict:
    if path and path != "-":
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input",  "-i", default="-",
                        help="JSON input file path, or '-' for stdin (default: stdin)")
    parser.add_argument("--output", "-o", required=True,
                        help="PNG output file path (e.g. ./out.png)")
    args = parser.parse_args()

    try:
        spec = _read_input(args.input)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid JSON input: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        return 2

    # Normalise missing 'kind' — don't fail
    spec.setdefault("kind", "hero-card")

    try:
        render(spec, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: render failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
