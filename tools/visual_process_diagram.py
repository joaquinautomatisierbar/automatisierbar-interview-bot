#!/usr/bin/env python3
"""
visual_process_diagram.py — Deterministic SVG generator for before/after process diagrams.

Built for the Presentation Designer agent in the Automatisierbar Build Pipeline.
NOT an LLM — pure layout from JSON input. Brand colors hardcoded from
Automatisierbar_Brand_Guide EXTERN copy.pdf (Version 1.0, 2026).

Usage:
    python tools/visual_process_diagram.py --input steps.json --output process.svg
    cat steps.json | python tools/visual_process_diagram.py > process.svg

Input JSON schema:
{
  "title": "Priority Inbox Automation",
  "customer_quote": "Wir wollen keine wichtigen Mandanten-Mails mehr verpassen.",
  "steps": [
    {
      "who": "Mitarbeiter",
      "action": "Posteingang prüfen",
      "tool": "Outlook",
      "data_in": "100+ Mails / Tag",
      "data_out": "5 wichtige markiert",
      "time_minutes_before": 25,
      "time_minutes_after": 2
    },
    ...
  ],
  "hourly_rate_chf": 70,
  "cycles_per_week": 5
}

Output: A4-landscape SVG (842 x 595 pt), brand-aligned, printable.
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

# Brand palette — from Automatisierbar_Brand_Guide EXTERN copy.pdf v1.0
PRIMARY_GREEN = "#15C97A"
PRIMARY_DARK = "#0A8F54"
PRIMARY_DEEP = "#063D25"
PRIMARY_LIGHT = "#D4F7E9"
NEUTRAL_BLACK = "#0C1410"
NEUTRAL_DARK = "#1E2B24"
NEUTRAL_MID = "#4A6358"
NEUTRAL_LIGHT = "#A8C4B8"
OFF_WHITE = "#F4FCF8"

# A4 landscape in pt (1pt = 1.333px @ 96dpi)
PAGE_W = 842
PAGE_H = 595
MARGIN = 32

# Layout constants
HEADER_H = 80
FOOTER_H = 70
COLUMN_GAP = 24
STEP_ROW_MIN_H = 56

# Font sizes (matching brand guide hierarchy)
FONT_DISPLAY = 24
FONT_H1 = 18
FONT_H2 = 14
FONT_BODY = 11
FONT_SMALL = 9
FONT_MONO = 9


def _svg_text(x: float, y: float, content: str, *,
              size: int = FONT_BODY, color: str = NEUTRAL_BLACK,
              weight: str = "normal", anchor: str = "start",
              family: str = "Helvetica, Arial, sans-serif") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
        f'font-size="{size}" fill="{color}" font-weight="{weight}" '
        f'text-anchor="{anchor}">{escape(content)}</text>'
    )


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Word-wrap text into lines no longer than max_chars."""
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
    if cur:
        lines.append(cur)
    return lines


def _format_duration(minutes: float) -> str:
    if minutes < 1:
        return "<1 min"
    if minutes < 60:
        return f"{int(round(minutes))} min"
    h = minutes / 60
    return f"{h:.1f} h" if h < 10 else f"{int(round(h))} h"


def render_diagram(data: dict) -> str:
    title = data.get("title") or "Prozess-Übersicht"
    quote = data.get("customer_quote", "")
    steps = data.get("steps", [])
    hourly_rate = float(data.get("hourly_rate_chf", 70))
    cycles_per_week = float(data.get("cycles_per_week", 1))

    # Totals
    total_before = sum(float(s.get("time_minutes_before", 0)) for s in steps)
    total_after = sum(float(s.get("time_minutes_after", 0)) for s in steps)
    minutes_saved_per_cycle = max(total_before - total_after, 0)
    hours_saved_week = minutes_saved_per_cycle * cycles_per_week / 60
    chf_saved_week = hours_saved_week * hourly_rate
    chf_saved_month = chf_saved_week * 4.33
    chf_saved_year = chf_saved_week * 52

    # Geometry
    body_top = MARGIN + HEADER_H
    body_bottom = PAGE_H - MARGIN - FOOTER_H
    body_h = body_bottom - body_top
    col_w = (PAGE_W - 2 * MARGIN - COLUMN_GAP) / 2
    left_col_x = MARGIN
    right_col_x = MARGIN + col_w + COLUMN_GAP

    # Row layout — fit all steps within body_h
    n = max(len(steps), 1)
    row_h = max(STEP_ROW_MIN_H, body_h / n)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {PAGE_W} {PAGE_H}" '
        f'width="{PAGE_W}pt" height="{PAGE_H}pt">'
    )

    # Page background
    parts.append(f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{OFF_WHITE}"/>')

    # Header — title + quote
    parts.append(
        f'<rect x="0" y="0" width="{PAGE_W}" height="{HEADER_H + MARGIN}" '
        f'fill="{PRIMARY_DEEP}"/>'
    )
    parts.append(_svg_text(MARGIN, 38, title,
                           size=FONT_DISPLAY, color=OFF_WHITE, weight="bold"))
    if quote:
        wrapped = _wrap_text(f'„{quote}"', max_chars=110)
        for i, line in enumerate(wrapped[:2]):
            parts.append(_svg_text(MARGIN, 62 + i * 14, line,
                                   size=FONT_SMALL, color=PRIMARY_LIGHT))

    # Column headers
    col_header_y = body_top - 10
    parts.append(_svg_text(left_col_x + col_w / 2, col_header_y, "VORHER · Manuell",
                           size=FONT_H1, color=NEUTRAL_MID, weight="bold",
                           anchor="middle"))
    parts.append(_svg_text(right_col_x + col_w / 2, col_header_y, "NACHHER · Automatisiert",
                           size=FONT_H1, color=PRIMARY_DARK, weight="bold",
                           anchor="middle"))

    # Step rows
    for i, step in enumerate(steps):
        y = body_top + i * row_h
        row_center_y = y + row_h / 2

        # Step number badge (centered between columns)
        badge_x = MARGIN + col_w + COLUMN_GAP / 2
        parts.append(
            f'<circle cx="{badge_x:.1f}" cy="{row_center_y:.1f}" r="11" '
            f'fill="{PRIMARY_GREEN}" stroke="{OFF_WHITE}" stroke-width="2"/>'
        )
        parts.append(_svg_text(badge_x, row_center_y + 4, str(i + 1),
                               size=FONT_BODY, color=NEUTRAL_BLACK,
                               weight="bold", anchor="middle"))

        # Left (VORHER) row
        _render_step_card(parts, step, left_col_x, y, col_w, row_h,
                          fill=OFF_WHITE, accent=NEUTRAL_MID, mode="before")
        # Right (NACHHER) row
        _render_step_card(parts, step, right_col_x, y, col_w, row_h,
                          fill=PRIMARY_LIGHT, accent=PRIMARY_DARK, mode="after")

    # Footer — totals + ROI
    footer_y = PAGE_H - FOOTER_H
    parts.append(f'<rect x="0" y="{footer_y}" width="{PAGE_W}" height="{FOOTER_H}" '
                 f'fill="{NEUTRAL_BLACK}"/>')

    saved_line = (
        f'Gespart pro Zyklus: {_format_duration(minutes_saved_per_cycle)} '
        f'(vorher {_format_duration(total_before)} / nachher {_format_duration(total_after)})'
    )
    parts.append(_svg_text(MARGIN, footer_y + 22, saved_line,
                           size=FONT_BODY, color=OFF_WHITE))

    chf_line = (
        f'Bei CHF {int(hourly_rate)}/h × {cycles_per_week:g} Zyklen/Woche: '
        f'CHF {chf_saved_week:,.0f}/Woche · '
        f'CHF {chf_saved_month:,.0f}/Monat · '
        f'CHF {chf_saved_year:,.0f}/Jahr'
    )
    parts.append(_svg_text(MARGIN, footer_y + 44, chf_line,
                           size=FONT_BODY, color=PRIMARY_GREEN, weight="bold"))

    # Honesty note
    if total_after > 0:
        parts.append(_svg_text(MARGIN, footer_y + 60,
                               f'Hinweis: Mensch-Kontrollzeit von {_format_duration(total_after)} pro Zyklus bleibt erhalten.',
                               size=FONT_SMALL, color=NEUTRAL_LIGHT))

    parts.append('</svg>')
    return "\n".join(parts)


def _render_step_card(parts: list[str], step: dict, x: float, y: float,
                      w: float, h: float, *,
                      fill: str, accent: str, mode: str) -> None:
    """Render a single step inside a column row (VORHER or NACHHER)."""
    pad = 10
    inner_w = w - 2 * pad

    # Card background
    parts.append(
        f'<rect x="{x:.1f}" y="{y + 4:.1f}" width="{w:.1f}" height="{h - 8:.1f}" '
        f'rx="6" ry="6" fill="{fill}" stroke="{accent}" stroke-width="0.5"/>'
    )

    text_x = x + pad
    line_y = y + pad + 14

    # Who + action (one line, ellipsis if needed)
    who = step.get("who", "?")
    action = step.get("action", "?")
    headline = f"{who} → {action}"[:80]
    parts.append(_svg_text(text_x, line_y, headline,
                           size=FONT_BODY, color=NEUTRAL_BLACK, weight="bold"))

    # Tool / data line
    tool = step.get("tool", "?")
    data_in = step.get("data_in", "")
    data_out = step.get("data_out", "")
    detail = f"{tool}"
    if data_in:
        detail += f" · {data_in}"
    if data_out:
        detail += f" → {data_out}"
    parts.append(_svg_text(text_x, line_y + 16, detail[:90],
                           size=FONT_SMALL, color=NEUTRAL_MID))

    # Time badge (right-aligned)
    minutes = float(step.get(f"time_minutes_{mode}", 0))
    label = _format_duration(minutes)
    badge_w = 56
    badge_x = x + w - pad - badge_w
    badge_y = y + h / 2 - 12
    badge_color = NEUTRAL_LIGHT if mode == "before" else PRIMARY_GREEN
    parts.append(
        f'<rect x="{badge_x:.1f}" y="{badge_y:.1f}" width="{badge_w}" height="22" '
        f'rx="11" ry="11" fill="{badge_color}"/>'
    )
    parts.append(_svg_text(badge_x + badge_w / 2, badge_y + 15, label,
                           size=FONT_SMALL, color=NEUTRAL_BLACK,
                           weight="bold", anchor="middle"))


def _read_input(path: str | None) -> dict:
    if path and path != "-":
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--input", "-i", default="-",
                        help="JSON input file path, or '-' for stdin")
    parser.add_argument("--output", "-o", default="-",
                        help="SVG output path, or '-' for stdout")
    args = parser.parse_args()

    try:
        data = _read_input(args.input)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON input: {e}", file=sys.stderr)
        return 2

    svg = render_diagram(data)

    if args.output == "-":
        sys.stdout.write(svg)
    else:
        Path(args.output).write_text(svg, encoding="utf-8")
        print(f"wrote {args.output} ({len(svg)} bytes)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
