#!/usr/bin/env python3
"""generate_pdf.py — automatisierbar branded PDF generator

Generates Bedarfsanalyse (discovery) or Weiterführende Fragen (followup) PDFs
following the automatisierbar Brand Guide Theme 02 (Prozess & Workflow).

Usage:
  python3 generate_pdf.py '<json>'
  echo '<json>' | python3 generate_pdf.py

Input JSON:
  {
    "type": "discovery" | "followup",
    "client_problem": "...",
    "questions": { "Kategorie": ["Frage 1", "Frage 2"], ... },
    "metadata": { "date": "2026-04-22" }
  }

Output: prints the absolute file path of the generated PDF to stdout.
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.utils import simpleSplit
except ImportError:
    print("ERROR: reportlab not installed. Run: pip3 install reportlab", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Brand colours (Theme 02 · Violett · Blueprint)
# ---------------------------------------------------------------------------
PRIMARY        = HexColor("#7C3ABD")
PRIMARY_DARK   = HexColor("#5B21B6")
PRIMARY_DEEP   = HexColor("#2E1065")
PRIMARY_LIGHT  = HexColor("#EDE8FF")
COL_BLACK      = HexColor("#0C1410")
COL_DARK       = HexColor("#1E2B24")
COL_MID        = HexColor("#4A6358")
OFF_WHITE      = HexColor("#F4FCF8")
WHITE          = white

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pt

MARGIN_X = 48
MARGIN_Y = 40

PHASES = ["INTERVIEW", "MAPPING", "PROTOTYPE", "PILOT"]

PHASE_FOR_TYPE = {
    "discovery": "INTERVIEW",
    "followup":  "MAPPING",
}

DOC_TITLES = {
    "discovery": "Bedarfsanalyse",
    "followup":  "Weiterführende Fragen",
}

DOC_SUBTITLES = {
    "discovery": "Discovery-Fragebogen für die Automatisierungsplanung",
    "followup":  "Offene Punkte & Ergänzungen vor dem Build",
}

OUTPUT_DIR = Path(__file__).parent.parent / ".tmp"


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def set_font(c: canvas.Canvas, style: str, size: float):
    """style: 'regular' | 'bold' | 'mono'"""
    if style == "bold":
        c.setFont("Helvetica-Bold", size)
    elif style == "mono":
        c.setFont("Courier", size)
    else:
        c.setFont("Helvetica", size)


def draw_corner_markers(c: canvas.Canvas, color, size: float = 10, thickness: float = 1.5):
    """Draw blueprint-style corner markers on all four corners."""
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    pad = 20
    for x, y, xdir, ydir in [
        (pad,          PAGE_H - pad,  1,  -1),  # top-left
        (PAGE_W - pad, PAGE_H - pad, -1,  -1),  # top-right
        (pad,          pad,            1,   1),  # bottom-left
        (PAGE_W - pad, pad,           -1,   1),  # bottom-right
    ]:
        c.line(x, y, x + xdir * size, y)
        c.line(x, y, x, y + ydir * size)


def draw_flow_bar(c: canvas.Canvas, active_phase: str, y: float) -> float:
    """Draw INTERVIEW → MAPPING → PROTOTYPE → PILOT bar. Returns new y."""
    box_w = 72
    box_h = 16
    arrow_w = 18
    total = len(PHASES) * box_w + (len(PHASES) - 1) * arrow_w
    x = MARGIN_X

    for i, phase in enumerate(PHASES):
        is_active = phase == active_phase

        if is_active:
            c.setFillColor(PRIMARY)
            c.setStrokeColor(PRIMARY)
            c.rect(x, y - box_h, box_w, box_h, fill=1, stroke=1)
            c.setFillColor(WHITE)
        else:
            c.setFillColor(PRIMARY_DEEP if is_active else HexColor("#FFFFFF00"))
            c.setStrokeColor(PRIMARY)
            c.setFillAlpha(0)
            c.rect(x, y - box_h, box_w, box_h, fill=0, stroke=1)
            c.setFillAlpha(1)
            c.setFillColor(PRIMARY)

        set_font(c, "mono", 6.5)
        c.setFillColor(WHITE if is_active else PRIMARY)
        c.drawCentredString(x + box_w / 2, y - box_h + 4.5, phase)

        if i < len(PHASES) - 1:
            c.setFillColor(PRIMARY)
            set_font(c, "mono", 8)
            c.drawString(x + box_w + 5, y - box_h + 3.5, "→")

        x += box_w + arrow_w

    return y - box_h - 8


def draw_blueprint_grid(c: canvas.Canvas, opacity: float = 0.08):
    """Draw subtle dot grid in the background."""
    c.saveState()
    c.setFillColor(PRIMARY)
    c.setFillAlpha(opacity)
    spacing = 22  # ~7.7mm
    r = 0.8
    x = MARGIN_X
    while x < PAGE_W - MARGIN_X:
        y = MARGIN_Y
        while y < PAGE_H - MARGIN_Y:
            c.circle(x, y, r, fill=1, stroke=0)
            y += spacing
        x += spacing
    c.restoreState()


def draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_style: str,
    font_size: float,
    color,
    line_height: float = None,
) -> float:
    """Draw text with word-wrap. Returns the y position after the last line."""
    if line_height is None:
        line_height = font_size * 1.4
    set_font(c, font_style, font_size)
    c.setFillColor(color)
    lines = simpleSplit(text, "Helvetica" if font_style != "mono" else "Courier", font_size, max_width)
    for line in lines:
        if y < MARGIN_Y + 20:
            break
        c.drawString(x, y, line)
        y -= line_height
    return y


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def draw_cover(c: canvas.Canvas, doc_type: str, problem: str, date_str: str):
    active_phase = PHASE_FOR_TYPE.get(doc_type, "INTERVIEW")
    title = DOC_TITLES.get(doc_type, "Analyse")
    subtitle = DOC_SUBTITLES.get(doc_type, "")

    # Full-bleed deep violet background
    c.setFillColor(PRIMARY_DEEP)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Corner markers (light color on dark background)
    draw_corner_markers(c, PRIMARY_LIGHT, size=10, thickness=1.2)

    # Top meta row
    y = PAGE_H - 28
    set_font(c, "mono", 7.5)
    c.setFillColor(PRIMARY_LIGHT)
    c.setFillAlpha(0.6)
    c.drawString(MARGIN_X, y, "automatisierbar.ch")
    version_text = f"v1.0 · {date_str[:4]}"
    c.drawRightString(PAGE_W - MARGIN_X, y, version_text)
    c.setFillAlpha(1)

    # Thin divider
    y -= 10
    c.setStrokeColor(PRIMARY)
    c.setStrokeAlpha(0.35)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    c.setStrokeAlpha(1)

    # Big logo
    y -= 60
    set_font(c, "regular", 30)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X, y, "automatisierbar")

    # Title
    y -= 28
    set_font(c, "regular", 22)
    c.setFillColor(OFF_WHITE)
    c.drawString(MARGIN_X, y, title)

    # Theme subtitle
    y -= 14
    set_font(c, "mono", 7.5)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X, y, "// THEME 02 · VIOLETT · BLUEPRINT")

    # Document subtitle
    y -= 20
    set_font(c, "regular", 10)
    c.setFillColor(PRIMARY_LIGHT)
    c.setFillAlpha(0.75)
    c.drawString(MARGIN_X, y, subtitle)
    c.setFillAlpha(1)

    # Flow connector bar
    y -= 32
    draw_flow_bar(c, active_phase, y)
    y -= 22

    # Problem statement label
    set_font(c, "mono", 7.5)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X, y, "// CLIENT PROBLEM STATEMENT")

    # Left accent bar for problem
    y -= 10
    c.setFillColor(PRIMARY)
    c.rect(MARGIN_X, y - 60, 2.5, 70, fill=1, stroke=0)

    # Problem text (truncated)
    safe_problem = problem[:280] + ("…" if len(problem) > 280 else "")
    set_font(c, "regular", 9.5)
    c.setFillColor(PRIMARY_LIGHT)
    c.setFillAlpha(0.85)
    lines = simpleSplit(safe_problem, "Helvetica", 9.5, PAGE_W - MARGIN_X * 2 - 12)
    text_y = y
    for line in lines[:5]:
        c.drawString(MARGIN_X + 10, text_y, line)
        text_y -= 13
    c.setFillAlpha(1)

    # Bottom metadata block
    bottom_y = MARGIN_Y + 40
    c.setStrokeColor(PRIMARY)
    c.setStrokeAlpha(0.25)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, bottom_y + 12, PAGE_W - MARGIN_X, bottom_y + 12)
    c.setStrokeAlpha(1)

    set_font(c, "mono", 7.5)
    c.setFillColor(PRIMARY_LIGHT)
    c.setFillAlpha(0.45)
    meta_lines = [
        f"// use_for: {title}, Fragebogen, Automatisierungsplanung",
        "// team: automatisierbar internal",
        f"// date: {date_str}",
        f"// type: {doc_type}",
    ]
    meta_y = bottom_y
    for ml in meta_lines:
        c.drawString(MARGIN_X, meta_y, ml)
        meta_y -= 11
    c.setFillAlpha(1)


# ---------------------------------------------------------------------------
# Content page
# ---------------------------------------------------------------------------

def draw_content_header(c: canvas.Canvas, title: str, page_num: int, total_pages: int, active_phase: str):
    y = PAGE_H - MARGIN_Y

    # Header line
    set_font(c, "mono", 7.5)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X, y, f"automatisierbar · {title}")
    c.setFillColor(COL_MID)
    c.drawRightString(PAGE_W - MARGIN_X, y, f"Seite {page_num} / {total_pages}")

    y -= 6
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(0.8)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)

    y -= 16
    draw_flow_bar(c, active_phase, y)
    return y - 20


def draw_problem_box(c: canvas.Canvas, problem: str, y: float) -> float:
    """Draw the client problem summary box. Returns new y."""
    max_w = PAGE_W - MARGIN_X * 2
    safe = problem[:180] + ("…" if len(problem) > 180 else "")
    lines = simpleSplit(safe, "Helvetica", 9, max_w - 24)
    box_h = len(lines) * 13 + 20

    # Background
    c.setFillColor(PRIMARY_LIGHT)
    c.setFillAlpha(0.6)
    c.roundRect(MARGIN_X, y - box_h, max_w, box_h, 2, fill=1, stroke=0)
    c.setFillAlpha(1)

    # Left accent
    c.setFillColor(PRIMARY)
    c.rect(MARGIN_X, y - box_h, 3, box_h, fill=1, stroke=0)

    # Label
    set_font(c, "mono", 7)
    c.setFillColor(PRIMARY_DARK)
    c.drawString(MARGIN_X + 10, y - 12, "// PROBLEM STATEMENT")

    # Text
    set_font(c, "regular", 9)
    c.setFillColor(COL_DARK)
    text_y = y - 24
    for line in lines:
        c.drawString(MARGIN_X + 10, text_y, line)
        text_y -= 13

    return y - box_h - 14


def draw_node_ref_box(c: canvas.Canvas, tag: str, category: str, q_count: int, y: float) -> float:
    """Draw a Node Reference Box for a category header. Returns new y."""
    box_h = 36
    box_w = 180

    c.setStrokeColor(PRIMARY)
    c.setLineWidth(0.8)
    c.rect(MARGIN_X, y - box_h, box_w, box_h, fill=0, stroke=1)

    # Tag (small, mono, violet)
    set_font(c, "mono", 7)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X + 8, y - 12, tag)

    # Category name (bold)
    set_font(c, "bold", 11)
    c.setFillColor(COL_DARK)
    c.drawString(MARGIN_X + 8, y - 24, category)

    # Meta (count)
    set_font(c, "mono", 7)
    c.setFillColor(COL_MID)
    label = f"// {q_count} Frage{'n' if q_count != 1 else ''}"
    c.drawString(MARGIN_X + 8, y - 33, label)

    return y - box_h - 10


def draw_question_item(c: canvas.Canvas, num: int, text: str, y: float) -> float:
    """Draw a single question row. Returns new y after the item."""
    max_w = PAGE_W - MARGIN_X * 2 - 32
    lines = simpleSplit(text, "Helvetica", 9.5, max_w)
    item_h = len(lines) * 13 + 10

    # Subtle separator
    c.setStrokeColor(PRIMARY)
    c.setStrokeAlpha(0.12)
    c.setLineWidth(0.4)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    c.setStrokeAlpha(1)

    # Number
    set_font(c, "mono", 8)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN_X + 2, y - 12, f"{num:02d}")

    # Question text
    set_font(c, "regular", 9.5)
    c.setFillColor(COL_DARK)
    text_y = y - 12
    for line in lines:
        c.drawString(MARGIN_X + 28, text_y, line)
        text_y -= 13

    return y - item_h - 4


def draw_content_footer(c: canvas.Canvas, total_qs: int, date_str: str):
    y = MARGIN_Y + 4
    c.setStrokeColor(PRIMARY)
    c.setStrokeAlpha(0.2)
    c.setLineWidth(0.4)
    c.line(MARGIN_X, y + 10, PAGE_W - MARGIN_X, y + 10)
    c.setStrokeAlpha(1)

    set_font(c, "mono", 7)
    c.setFillColor(COL_MID)
    c.drawString(MARGIN_X, y, "// automatisierbar.ch · Theme 02 · Prozess & Workflow")
    c.drawRightString(
        PAGE_W - MARGIN_X, y,
        f"// total_questions: {total_qs:02d} · date: {date_str}"
    )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate(data: dict) -> str:
    doc_type     = data.get("type", "discovery")
    problem      = data.get("client_problem", "")
    questions    = data.get("questions", {})
    metadata     = data.get("metadata", {})
    date_str     = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))

    if not questions:
        raise ValueError("'questions' dict is empty — nothing to generate.")

    active_phase = PHASE_FOR_TYPE.get(doc_type, "INTERVIEW")
    title = DOC_TITLES.get(doc_type, "Analyse")
    total_qs = sum(len(v) for v in questions.values())

    # Flatten all questions for pagination (7 per content page)
    flat: list[tuple[str, str]] = []
    for cat, qs in questions.items():
        for q in qs:
            flat.append((cat, q))

    QUESTIONS_PER_PAGE = 7
    chunks = [flat[i:i + QUESTIONS_PER_PAGE] for i in range(0, len(flat), QUESTIONS_PER_PAGE)]
    total_pages = len(chunks) + 1  # +1 for cover

    # Output path
    safe_date = re.sub(r"[^0-9\-]", "", date_str)
    prefix = "bedarfsanalyse" if doc_type == "discovery" else "weiterfuehrende_fragen"
    filename = f"{prefix}_{safe_date}.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = str(OUTPUT_DIR / filename)

    # Create PDF
    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(f"automatisierbar · {title}")
    c.setAuthor("automatisierbar.ch")
    c.setSubject(f"{title} · {date_str}")

    # ── Cover page ──────────────────────────────────────────────────────────
    draw_cover(c, doc_type, problem, date_str)
    c.showPage()

    # ── Content pages ───────────────────────────────────────────────────────
    global_q_index = 1

    for page_idx, chunk in enumerate(chunks):
        page_num = page_idx + 2  # page 1 is cover

        draw_blueprint_grid(c)
        draw_corner_markers(c, PRIMARY)

        y = draw_content_header(c, title, page_num, total_pages, active_phase)

        # Problem box only on first content page
        if page_idx == 0:
            y = draw_problem_box(c, problem, y)

        # Re-group chunk by category
        cat_groups: dict[str, list[str]] = {}
        for cat, q in chunk:
            cat_groups.setdefault(cat, []).append(q)

        for cat, qs in cat_groups.items():
            # Check if we have enough space for the category header
            if y < MARGIN_Y + 80:
                c.showPage()
                page_num += 1
                total_pages += 1
                draw_blueprint_grid(c)
                draw_corner_markers(c, PRIMARY)
                y = draw_content_header(c, title, page_num, total_pages, active_phase)

            y = draw_node_ref_box(c, "KATEGORIE", cat, len(qs), y)

            for q in qs:
                if y < MARGIN_Y + 50:
                    draw_content_footer(c, total_qs, date_str)
                    c.showPage()
                    page_num += 1
                    total_pages += 1
                    draw_blueprint_grid(c)
                    draw_corner_markers(c, PRIMARY)
                    y = draw_content_header(c, title, page_num, total_pages, active_phase)

                y = draw_question_item(c, global_q_index, q, y)
                global_q_index += 1

            y -= 8

        draw_content_footer(c, total_qs, date_str)
        c.showPage()

    c.save()
    return out_path


def main():
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read().strip()

    if not raw:
        print("ERROR: No input JSON provided.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    try:
        path = generate(data)
        print(path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
