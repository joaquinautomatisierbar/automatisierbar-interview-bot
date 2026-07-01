#!/usr/bin/env python3
"""
render_n8n_workflow_diagram.py — Deterministic n8n-style workflow diagram renderer.

Built for the Automatisierbar Build Pipeline (AUT-46, D2).
NOT an LLM — pure SVG layout from JSON input, rasterised via cairosvg.

Usage:
    python3 tools/render_n8n_workflow_diagram.py --input spec.json --output-dir ./out/

Output files in --output-dir:
    diagram_landscape.png  — 2400×1200 px
    diagram_square.png     — 1200×1200 px (left-crop from landscape)

Input JSON schema:
{
  "title": "string",
  "subtitle": "optional string",
  "phases": [
    {
      "label": "string",
      "color": "blue | yellow | red | green",
      "steps": [
        {
          "label": "string",
          "kind": "trigger | action | decision | manual",
          "icon": "optional unicode char (ignored — kind drives display)",
          "endpoint": "optional URL shown as footnote"
        }
      ]
    }
  ],
  "error_path": {
    "label": "string",
    "steps": [...]
  }
}
"""

from __future__ import annotations

import argparse
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
PRIMARY_DEEP = "#063D25"
PRIMARY_LIGHT = "#D4F7E9"
OFF_WHITE = "#F4FCF8"
NEUTRAL_BLACK = "#0C1410"
NEUTRAL_MID = "#4A6358"
NEUTRAL_LIGHT = "#A8C4B8"

PHASE_COLORS = {
    "blue":   "#3B82F6",
    "yellow": "#F59E0B",
    "red":    "#EF4444",
    "green":  "#15C97A",
}
PHASE_TEXT_COLORS = {
    "blue":   "#FFFFFF",
    "yellow": "#1A1A1A",
    "red":    "#FFFFFF",
    "green":  "#063D25",
}
KIND_BG = {
    "trigger":  "#15C97A",
    "action":   "#3B82F6",
    "decision": "#F59E0B",
    "manual":   "#8B5CF6",
}
KIND_TEXT = {
    "trigger":  "#063D25",
    "action":   "#FFFFFF",
    "decision": "#1A1A1A",
    "manual":   "#FFFFFF",
}

# ---------------------------------------------------------------------------
# Layout constants — design space 1200×600
# ---------------------------------------------------------------------------
DESIGN_W = 1200
DESIGN_H = 600

TITLE_H = 48
PHASE_LABEL_H = 22
CARD_AREA_TOP = 70
CARD_TOP_PAD = TITLE_H + PHASE_LABEL_H + 8   # = 78
CARD_H = 160
CARD_H_COMPACT = 130
MARGIN_X = 40
CARD_GAP = 16

# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def _t(x: float, y: float, content: str, *,
       size: int = 11,
       color: str = NEUTRAL_BLACK,
       weight: str = "normal",
       anchor: str = "middle",
       font_style: str = "normal",
       family: str = "Helvetica, Arial, sans-serif") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
        f'font-size="{size}" fill="{color}" font-weight="{weight}" '
        f'text-anchor="{anchor}" font-style="{font_style}">{escape(content)}</text>'
    )


def _rect(x: float, y: float, w: float, h: float, *,
          fill: str,
          rx: float = 0,
          opacity: float = 1.0,
          stroke: str = "none",
          stroke_width: float = 0) -> str:
    attrs = (
        f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{rx:.1f}" fill="{fill}" opacity="{opacity:.2f}"'
    )
    if stroke != "none":
        attrs += f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect {attrs}/>'


def _wrap(text: str, max_chars: int) -> list[str]:
    """Word-wrap text into lines no longer than max_chars (max 2 lines returned)."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur = f"{cur} {w}"
        else:
            lines.append(cur)
            cur = w
            if len(lines) == 1:
                # Only allow 2 lines; fold remaining words into second line
                remaining = " ".join(words[words.index(w):])
                if len(remaining) > max_chars:
                    remaining = remaining[: max_chars - 1] + "…"
                lines.append(remaining)
                return lines
    if cur:
        lines.append(cur)
    return lines[:2]


def _trunc(url: str, limit: int = 32) -> str:
    if len(url) > limit:
        return url[: limit - 1] + "…"
    return url


# ---------------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------------

def _card(parts: list[str], step: dict, cx: float, card_top: float,
          card_h: float, card_w: float, phase_color: str) -> None:
    """Render one step card centred at cx, top-left = (cx - card_w/2, card_top)."""
    x = cx - card_w / 2
    kind = step.get("kind", "action")
    label = step.get("label", "")
    endpoint = step.get("endpoint", "")

    # Card background
    parts.append(_rect(x, card_top, card_w, card_h, fill=OFF_WHITE,
                       rx=8, stroke=NEUTRAL_LIGHT, stroke_width=1))

    # Number badge — top-centre of card
    badge_cy = card_top + 16
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{badge_cy:.1f}" r="11" fill="{phase_color}"/>'
    )

    # Label — up to 2 lines, bold 11px
    lines = _wrap(label, 16)
    label_start_y = card_top + 36
    line_h = 14
    for i, line in enumerate(lines):
        parts.append(_t(cx, label_start_y + i * line_h, line,
                        size=11, color=NEUTRAL_BLACK, weight="bold"))

    # Kind badge — pill 60×14, centred
    kind_bg = KIND_BG.get(kind, KIND_BG["action"])
    kind_fg = KIND_TEXT.get(kind, KIND_TEXT["action"])
    pill_w = 60
    pill_h = 14
    pill_x = cx - pill_w / 2
    pill_y = card_top + card_h - (30 if endpoint else 22)
    parts.append(_rect(pill_x, pill_y, pill_w, pill_h,
                       fill=kind_bg, rx=7))
    parts.append(_t(cx, pill_y + 10, kind.upper(),
                    size=8, color=kind_fg, weight="bold"))

    # Endpoint footnote
    if endpoint:
        parts.append(_t(cx, card_top + card_h - 8,
                        _trunc(endpoint),
                        size=9, color=NEUTRAL_MID, font_style="italic"))


# ---------------------------------------------------------------------------
# Arrow rendering
# ---------------------------------------------------------------------------

def _arrow(parts: list[str], x1: float, x2: float, y: float) -> None:
    """Draw a horizontal arrow from x1 to x2 at vertical centre y."""
    x_start = x1 + 2
    x_end = x2 - 8
    if x_end <= x_start:
        return
    parts.append(
        f'<line x1="{x_start:.1f}" y1="{y:.1f}" x2="{x_end:.1f}" y2="{y:.1f}" '
        f'stroke="{NEUTRAL_LIGHT}" stroke-width="1.5" '
        f'marker-end="url(#arrowhead)"/>'
    )


# ---------------------------------------------------------------------------
# Main layout helpers
# ---------------------------------------------------------------------------

def _compute_card_geometry(all_steps: list[dict]) -> tuple[float, float, list[float]]:
    """Return (actual_card_w, spacing, [cx_i]) for the flat list of all steps."""
    n = len(all_steps)
    avail_w = DESIGN_W - 2 * MARGIN_X
    if n == 0:
        return 100.0, 0.0, []
    actual_card_w = max(80, min(130, (avail_w - (n - 1) * CARD_GAP) // n))
    if n > 1:
        spacing = (avail_w - actual_card_w) / (n - 1)
    else:
        spacing = 0.0
    first_cx = MARGIN_X + actual_card_w / 2
    cxs = [first_cx + i * spacing for i in range(n)]
    return float(actual_card_w), spacing, cxs


def _phase_x_range(cxs: list[float], start_idx: int, end_idx: int,
                   card_w: float) -> tuple[float, float]:
    """x_start, x_end for a phase spanning [start_idx, end_idx] inclusive."""
    x_start = cxs[start_idx] - card_w / 2 - 8
    x_end = cxs[end_idx] + card_w / 2 + 8
    return x_start, x_end


# ---------------------------------------------------------------------------
# Core SVG builder
# ---------------------------------------------------------------------------

def render_svg(data: dict) -> str:
    title = data.get("title") or "Workflow Diagram"
    subtitle = data.get("subtitle", "")
    phases = data.get("phases") or []
    error_path = data.get("error_path")

    # Flatten all main-flow steps so we can compute global cx positions
    all_steps: list[dict] = []
    step_phase_map: list[tuple[int, str, str]] = []  # (global_idx, phase_color, phase_label)
    for ph in phases:
        ph_steps = ph.get("steps") or []
        if not ph_steps:
            continue
        ph_color_key = ph.get("color", "blue")
        ph_color = PHASE_COLORS.get(ph_color_key, PHASE_COLORS["blue"])
        for s in ph_steps:
            step_phase_map.append((len(all_steps), ph_color, ph.get("label", "")))
            all_steps.append(s)

    has_error = bool(error_path and error_path.get("steps"))
    card_h = CARD_H_COMPACT if has_error else CARD_H
    card_top = CARD_TOP_PAD  # = 78

    actual_card_w, spacing, cxs = _compute_card_geometry(all_steps)

    parts: list[str] = []

    # ---- SVG root + defs ----
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {DESIGN_W} {DESIGN_H}">'
    )
    parts.append(
        "<defs>"
        '<marker id="arrowhead" markerWidth="8" markerHeight="6" '
        'refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0, 8 3, 0 6" fill="{NEUTRAL_LIGHT}"/>'
        "</marker>"
        "</defs>"
    )

    # Background
    parts.append(_rect(0, 0, DESIGN_W, DESIGN_H, fill=OFF_WHITE))

    # ---- Title bar ----
    parts.append(_rect(0, 0, DESIGN_W, TITLE_H, fill=PRIMARY_DEEP))
    title_y = 28 if subtitle else 30
    parts.append(_t(DESIGN_W / 2, title_y, title,
                    size=20, color=OFF_WHITE, weight="bold"))
    if subtitle:
        parts.append(_t(DESIGN_W / 2, 42, subtitle,
                        size=13, color=PRIMARY_LIGHT))

    if not all_steps:
        parts.append("</svg>")
        return "\n".join(parts)

    # ---- Phase zones (background tint + label strip) ----
    idx = 0
    for ph in phases:
        ph_steps = ph.get("steps") or []
        if not ph_steps:
            continue
        n_ph = len(ph_steps)
        start_idx = idx
        end_idx = idx + n_ph - 1
        idx += n_ph

        ph_color_key = ph.get("color", "blue")
        ph_color = PHASE_COLORS.get(ph_color_key, PHASE_COLORS["blue"])
        ph_text = PHASE_TEXT_COLORS.get(ph_color_key, "#FFFFFF")
        ph_label = ph.get("label", "")

        x_start, x_end = _phase_x_range(cxs, start_idx, end_idx, actual_card_w)
        zone_top = TITLE_H
        zone_bottom = card_top + card_h + 8

        # Tinted background rectangle (opacity 0.12)
        parts.append(_rect(x_start, zone_top,
                           x_end - x_start, zone_bottom - zone_top,
                           fill=ph_color, rx=4, opacity=0.12))

        # Solid label strip
        parts.append(_rect(x_start, zone_top,
                           x_end - x_start, PHASE_LABEL_H,
                           fill=ph_color, rx=4))
        strip_cx = (x_start + x_end) / 2
        parts.append(_t(strip_cx, zone_top + 15, ph_label,
                        size=11, color=ph_text, weight="bold"))

    # ---- Arrows between all consecutive main-flow cards ----
    y_arrow = card_top + card_h / 2
    for i in range(len(all_steps) - 1):
        x1 = cxs[i] + actual_card_w / 2
        x2 = cxs[i + 1] - actual_card_w / 2
        _arrow(parts, x1, x2, y_arrow)

    # ---- Main-flow step cards ----
    for (global_idx, ph_color, _ph_label) in step_phase_map:
        step = all_steps[global_idx]
        cx = cxs[global_idx]
        _card(parts, step, cx, card_top, card_h, actual_card_w, ph_color)

    # ---- Error path ----
    if has_error:
        err_steps = error_path.get("steps") or []
        err_label = error_path.get("label", "Error Path")
        err_color = "#EF4444"

        error_zone_top = card_top + card_h + 25
        err_label_h = 20
        err_card_top = error_zone_top + err_label_h + 8
        err_card_h = max(50, DESIGN_H - err_card_top - 15)

        # Compute geometry for error steps independently
        _, _, err_cxs = _compute_card_geometry(err_steps)
        err_card_w, _, _ = _compute_card_geometry(err_steps)
        # Recompute cleanly
        n_err = len(err_steps)
        avail_w_err = DESIGN_W - 2 * MARGIN_X
        err_card_w = float(max(80, min(130, (avail_w_err - (n_err - 1) * CARD_GAP) // n_err))) if n_err else 100.0
        if n_err > 1:
            err_spacing = (avail_w_err - err_card_w) / (n_err - 1)
        else:
            err_spacing = 0.0
        first_err_cx = MARGIN_X + err_card_w / 2
        err_cxs = [first_err_cx + i * err_spacing for i in range(n_err)]

        if n_err > 0:
            x_err_start = err_cxs[0] - err_card_w / 2 - 8
            x_err_end = err_cxs[-1] + err_card_w / 2 + 8
        else:
            x_err_start = MARGIN_X
            x_err_end = DESIGN_W - MARGIN_X

        # Tinted zone for error
        parts.append(_rect(x_err_start, error_zone_top,
                           x_err_end - x_err_start,
                           DESIGN_H - error_zone_top - 5,
                           fill=err_color, rx=4, opacity=0.08))

        # Error label strip
        parts.append(_rect(x_err_start, error_zone_top,
                           x_err_end - x_err_start, err_label_h,
                           fill=err_color, rx=4))
        strip_cx = (x_err_start + x_err_end) / 2
        parts.append(_t(strip_cx, error_zone_top + 14,
                        f"↳ {err_label}",
                        size=11, color="#FFFFFF", weight="bold"))

        # Arrows between error cards
        y_err_arrow = err_card_top + err_card_h / 2
        for i in range(n_err - 1):
            x1 = err_cxs[i] + err_card_w / 2
            x2 = err_cxs[i + 1] - err_card_w / 2
            _arrow(parts, x1, x2, y_err_arrow)

        # Error step cards
        for i, step in enumerate(err_steps):
            _card(parts, step, err_cxs[i], err_card_top,
                  err_card_h, err_card_w, err_color)

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# PNG export
# ---------------------------------------------------------------------------

def export_pngs(svg_text: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    landscape_path = output_dir / "diagram_landscape.png"
    square_path = output_dir / "diagram_square.png"

    # Render landscape at 2400×1200 directly via cairosvg
    png_bytes = cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        output_width=2400,
        output_height=1200,
    )
    landscape_path.write_bytes(png_bytes)
    print(f"wrote {landscape_path} (2400×1200)", file=sys.stderr)

    # Square crop: take the left 1200×1200 from the 2400×1200 image
    import io
    img = Image.open(io.BytesIO(png_bytes))
    square = img.crop((0, 0, 1200, 1200))
    square.save(square_path, format="PNG")
    print(f"wrote {square_path} (1200×1200)", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_input(path: str | None) -> dict:
    if path and path != "-":
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render an n8n-style workflow diagram to PNG (2400×1200 + 1200×1200 square)."
    )
    parser.add_argument("--input", "-i", default="-",
                        help="JSON input file path, or '-' for stdin")
    parser.add_argument("--output-dir", "-o", default=".",
                        help="Directory for output PNGs (created if absent)")
    args = parser.parse_args()

    try:
        data = _read_input(args.input)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON input: {exc}", file=sys.stderr)
        return 2

    svg_text = render_svg(data)
    export_pngs(svg_text, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
