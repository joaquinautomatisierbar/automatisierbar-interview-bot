#!/usr/bin/env python3
"""
render_linkedin_image.py — Deterministic LinkedIn brand-card renderer.

NOT an LLM. Pure Pillow layout from a JSON spec, in the Automatisierbar terminal
aesthetic (dark green-black, #15C97A accent, JetBrains Mono, corner brackets).
Originally an SVG+cairosvg tool (branch AUT-46); reimplemented in Pillow because
this machine's .venv is x86_64 and brew's Cairo is arm64 (incompatible), so
cairosvg cannot load libcairo here. Pillow needs no system libs and matches the
brand from bundled JetBrains Mono fonts.

Usage:
    python3 tools/render_linkedin_image.py --input spec.json --output ./out.png
    echo '{"headline":"3000 Franken"}' | python3 tools/render_linkedin_image.py -o out.png

Input JSON schema:
{
  "kind":     "hero-card",                          (optional)
  "headline": "≤6 words, the load-bearing claim/number",   (required)
  "subtitle": "≤10 words, sector/context",          (optional)
  "label":    "top-left // meta, e.g. AUTOMATISIERBAR or the pillar",  (optional)
  "tag":      "top-right small tag, e.g. KW-27",    (optional)
  "palette":  "green-on-deep | white-on-black | deep-on-light | light-on-green",  (default green-on-deep)
  "aspect":   "square | portrait | landscape",      (default portrait)
  "branding": "none | wordmark | logo"              (default logo)
}

Output resolutions (native LinkedIn): square 1200x1200, portrait 1080x1350,
landscape 1200x627. Rendered at 2x then LANCZOS-downsampled for crisp text.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
LOGO_PNG = REPO_ROOT / "static" / "automatisierbar-logo-email.png"

# ---------------------------------------------------------------------------
# Brand palette — Automatisierbar_Brand_Guide EXTERN v1.0 + deck design-system
# ---------------------------------------------------------------------------
PRIMARY_GREEN = "#15C97A"
PRIMARY_DEEP  = "#063D25"
PRIMARY_LIGHT = "#D4F7E9"
OFF_WHITE     = "#F4FCF8"
NEUTRAL_BLACK = "#0C1410"
TEXT_MUTE     = "#6F8A7C"

DIMENSIONS: dict[str, tuple[int, int]] = {
    "square":    (1200, 1200),
    "portrait":  (1080, 1350),
    "landscape": (1200, 627),
}

# palette -> (bg, headline, subtitle, muted/meta, accent)
PALETTES: dict[str, tuple[str, str, str, str, str]] = {
    "green-on-deep":  (NEUTRAL_BLACK, PRIMARY_GREEN, PRIMARY_LIGHT, TEXT_MUTE,  PRIMARY_GREEN),
    "white-on-black": (NEUTRAL_BLACK, OFF_WHITE,     PRIMARY_GREEN, TEXT_MUTE,  PRIMARY_GREEN),
    "deep-on-light":  (OFF_WHITE,     PRIMARY_DEEP,  "#2C5A45",     "#4A6358",  PRIMARY_GREEN),
    "light-on-green": (PRIMARY_GREEN, PRIMARY_DEEP,  PRIMARY_DEEP,  "#0A8F54",  PRIMARY_DEEP),
}
# aliases for the PR Director auto-svg vocabulary
PALETTES["green-on-offwhite"] = PALETTES["deep-on-light"]

SCALE = 2  # supersample factor for anti-aliasing


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def _font_candidates(weight: str) -> list[str]:
    jb = {
        "regular":   "JetBrainsMono-Regular.ttf",
        "medium":    "JetBrainsMono-Medium.ttf",
        "bold":      "JetBrainsMono-Bold.ttf",
        "extrabold": "JetBrainsMono-ExtraBold.ttf",
    }[weight]
    out = [str(FONT_DIR / jb)]
    # system fallbacks (kept on-brand: monospace first)
    out += [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    return out


@lru_cache(maxsize=128)
def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for path in _font_candidates(weight):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Text helpers (width-based wrapping + auto-fit)
# ---------------------------------------------------------------------------

def _text_w(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=font)


def _wrap(draw, text: str, font, max_w: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        if _text_w(draw, f"{cur} {w}", font) <= max_w:
            cur = f"{cur} {w}"
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _fit(draw, text, weight, max_w, max_h, hi, lo, line_ratio=1.18):
    """Largest size in [lo, hi] whose wrapped text fits max_w x max_h."""
    best = None
    for size in range(hi, lo - 1, -2):
        font = _font(weight, size)
        lines = _wrap(draw, text, font, max_w)
        line_h = size * line_ratio
        total_h = len(lines) * line_h
        widest = max((_text_w(draw, ln, font) for ln in lines), default=0)
        if total_h <= max_h and widest <= max_w:
            best = (font, lines, line_h, size)
            break
    if best is None:
        font = _font(weight, lo)
        best = (font, _wrap(draw, text, font, max_w), lo * line_ratio, lo)
    return best


def _corner_brackets(draw, x0, y0, x1, y1, length, width, color):
    for (cx, cy, dx, dy) in (
        (x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1),
    ):
        draw.line([(cx, cy), (cx + dx * length, cy)], fill=color, width=width)
        draw.line([(cx, cy), (cx, cy + dy * length)], fill=color, width=width)


def _blend(hex_fg: str, hex_bg: str, alpha: float) -> tuple[int, int, int]:
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    f, b = rgb(hex_fg), rgb(hex_bg)
    return tuple(int(b[i] + (f[i] - b[i]) * alpha) for i in range(3))


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def build_card(spec: dict) -> Image.Image:
    aspect = spec.get("aspect") or "portrait"
    if aspect not in DIMENSIONS:
        aspect = "portrait"
    palette = spec.get("palette") or "green-on-deep"
    if palette not in PALETTES:
        palette = "green-on-deep"
    branding = spec.get("branding") or "logo"
    headline = str(spec.get("headline", "")).strip()
    subtitle = str(spec.get("subtitle", "") or "").strip()
    label = str(spec.get("label", "") or "").strip()
    tag = str(spec.get("tag", "") or "").strip()

    Wn, Hn = DIMENSIONS[aspect]
    W, H = Wn * SCALE, Hn * SCALE
    bg, hl_c, sub_c, mute_c, acc_c = PALETTES[palette]

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    m = int(W * 0.075)              # safe-area margin
    faint = _blend(acc_c, bg, 0.45)  # dim accent for brackets

    # corner brackets
    inset = int(W * 0.038)
    _corner_brackets(d, inset, inset, W - inset, H - inset,
                     length=int(W * 0.045), width=max(2, int(W * 0.0035)),
                     color=faint)

    # top meta line  // LABEL
    meta_size = max(16, int(H * 0.020))
    meta_font = _font("medium", meta_size)
    top_y = m
    if label:
        d.text((m, top_y), f"// {label.upper()}", font=meta_font, fill=mute_c)
    if tag:
        tw = _text_w(d, tag.upper(), meta_font)
        d.text((W - m - tw, top_y), tag.upper(), font=meta_font, fill=mute_c)
    band_top = top_y + meta_size * 1.6

    # bottom brand band
    brand_h = int(H * 0.055)
    band_bottom = H - m - brand_h

    # ---- middle content block (accent bar + headline + subtitle) ----
    content_w = W - 2 * m
    avail_h = band_bottom - band_top
    bar_h = max(4, int(H * 0.009))
    bar_w = int(W * 0.10)
    gap_bar = int(H * 0.025)
    gap_sub = int(H * 0.030)

    is_land = aspect == "landscape"
    hl_hi = int(H * (0.085 if is_land else 0.115))
    hl_lo = int(H * 0.045)
    hl_font, hl_lines, hl_lh, _ = _fit(
        d, headline, "extrabold", content_w, avail_h * 0.62, hl_hi, hl_lo)

    sub_lines, sub_lh, sub_font = [], 0, None
    if subtitle:
        sub_size = max(16, int(hl_font.size * 0.42))
        sub_font = _font("medium", sub_size)
        sub_lines = _wrap(d, subtitle, sub_font, content_w)
        sub_lh = sub_size * 1.3

    total_hl = len(hl_lines) * hl_lh
    total_sub = len(sub_lines) * sub_lh
    block_h = bar_h + gap_bar + total_hl + (gap_sub + total_sub if sub_lines else 0)
    block_top = band_top + (avail_h - block_h) / 2

    # accent bar
    y = block_top
    d.rectangle([m, y, m + bar_w, y + bar_h], fill=acc_c)
    y += bar_h + gap_bar

    # headline (left-aligned, ExtraBold)
    for ln in hl_lines:
        d.text((m, y), ln, font=hl_font, fill=hl_c)
        y += hl_lh
    # subtitle
    if sub_lines:
        y = block_top + bar_h + gap_bar + total_hl + gap_sub
        for ln in sub_lines:
            d.text((m, y), ln, font=sub_font, fill=sub_c)
            y += sub_lh

    # ---- bottom brand ----
    if branding in ("wordmark", "logo"):
        by = band_bottom + int(brand_h * 0.1)
        wx = m
        if branding == "logo" and LOGO_PNG.exists():
            try:
                logo = Image.open(LOGO_PNG).convert("RGBA")
                lh = brand_h
                lw = int(logo.width * (lh / logo.height))
                logo = logo.resize((lw, lh), Image.LANCZOS)
                img.paste(logo, (m, band_bottom), logo)
                wx = m + lw + int(W * 0.018)
            except Exception:
                pass
        wm_font = _font("bold", max(16, int(H * 0.022)))
        wm_y = band_bottom + (brand_h - (max(16, int(H * 0.022)))) / 2
        d.text((wx, wm_y), "automatisierbar.ch", font=wm_font, fill=hl_c)

    return img.resize((Wn, Hn), Image.LANCZOS)


def render(spec: dict, output_path: str) -> tuple[int, int]:
    out = build_card(spec)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(output_path, format="PNG", optimize=True)
    kb = Path(output_path).stat().st_size // 1024
    print(f"wrote {output_path}  ({out.width}x{out.height} px, {kb} KB)", file=sys.stderr)
    return out.size


def _read_input(path: str | None) -> dict:
    if path and path != "-":
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--input", "-i", default="-", help="JSON file path, or '-' for stdin")
    p.add_argument("--output", "-o", required=True, help="PNG output path")
    args = p.parse_args()
    try:
        spec = _read_input(args.input)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        print(f"ERROR: bad input: {exc}", file=sys.stderr)
        return 2
    if not str(spec.get("headline", "")).strip():
        print("ERROR: 'headline' is required", file=sys.stderr)
        return 2
    try:
        render(spec, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: render failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
