"""report_pdf.py — the monthly Spesenabrechnung PDF (reportlab canvas, navy theme).

generate_spesen_pdf(month_data) -> path to a PDF in the output dir. Self-contained
(own palette, Helvetica core fonts so no font registration needed). Paginates the
line-item table; ends with category subtotals, the CHF total, and a separate
"Weiterverrechenbar" section the accountant can bill on to the client.

month_data shape (built by month_close.build_month_data):
  knowbody:        {"name": str, "email": str}
  jahr_monat:      "YYYY-MM"
  erstellt_am:     "YYYY-MM-DD"
  belege:          [ {datum,kategorie,unterkategorie,haendler,betrag_original,
                      waehrung,betrag_chf,zahlungsart,projekt,weiterverrechenbar,
                      wechselkurs,notiz}, ... ]  (already Kaffeekasse-excluded)
  total_chf:       float
  kategorie_summen:{kat: float}
  weiterverrechenbar: [belege subset]
  summe_weiter_chf: float
  anzahl:          int
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas

# --- KnowGravity-ish palette: clean, navy, professional -------------------------
NAVY = HexColor("#1B2A4A")
NAVY_DEEP = HexColor("#11203B")
INK = HexColor("#1F2933")
MUTED = HexColor("#6B7785")
LINE = HexColor("#D9DEE6")
ZEBRA = HexColor("#F4F6FA")
ACCENT = HexColor("#2E6BE6")
GREEN = HexColor("#0F7B4F")

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pt
MARGIN_X = 42
TOP = PAGE_H - 44
BOTTOM = 64

# Column layout (sums to content width = PAGE_W - 2*MARGIN_X ≈ 511pt)
COLS = [
    ("Datum", 58, "l"),
    ("Kategorie", 74, "l"),
    ("Beschreibung", 150, "l"),
    ("Zahlung", 86, "l"),
    ("Original", 64, "r"),
    ("CHF", 70, "r"),
]


def _output_dir() -> str:
    d = os.environ.get("SPESEN_OUTPUT_DIR") or str(Path(__file__).resolve().parents[2] / ".tmp")
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


def chf(n) -> str:
    """Swiss-style amount: 1'234.50 (apostrophe thousands)."""
    try:
        v = float(n or 0)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}".replace(",", "'")
    return s


def _clip(c: canvas.Canvas, text: str, width: float, font: str, size: float) -> str:
    """Truncate text with an ellipsis so it fits `width`."""
    text = text or ""
    if c.stringWidth(text, font, size) <= width:
        return text
    ell = "…"
    while text and c.stringWidth(text + ell, font, size) > width:
        text = text[:-1]
    return text + ell


def _wrap(c: canvas.Canvas, text: str, width: float, font: str, size: float) -> list:
    """Greedy word-wrap into lines that each fit `width`."""
    words = (text or "").split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if c.stringWidth(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _header_band(c: canvas.Canvas, d: dict):
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 96, PAGE_W, 96, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN_X, PAGE_H - 50, "Spesenabrechnung")
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#AEBBD4"))
    c.drawString(MARGIN_X, PAGE_H - 68, "KnowGravity Inc.  ·  KnowSpesen")
    # right side: person + month
    name = (d.get("knowbody") or {}).get("name", "")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 48, name)
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#AEBBD4"))
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 66, _month_label(d.get("jahr_monat", "")))


_MONTHS_DE = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
              "August", "September", "Oktober", "November", "Dezember"]


def _month_label(jm: str) -> str:
    try:
        y, m = jm.split("-")
        return f"{_MONTHS_DE[int(m)]} {y}"
    except Exception:
        return jm


def _table_header(c: canvas.Canvas, y: float) -> float:
    c.setFillColor(NAVY_DEEP)
    c.rect(MARGIN_X, y - 16, PAGE_W - 2 * MARGIN_X, 18, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8.5)
    x = MARGIN_X + 6
    for label, w, align in COLS:
        if align == "r":
            c.drawRightString(x + w - 8, y - 11, label)
        else:
            c.drawString(x, y - 11, label)
        x += w
    return y - 16


def _row(c: canvas.Canvas, y: float, beleg: dict, zebra: bool) -> float:
    rh = 18
    if zebra:
        c.setFillColor(ZEBRA)
        c.rect(MARGIN_X, y - rh, PAGE_W - 2 * MARGIN_X, rh, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica", 8.5)
    # (weiterverrechenbar items get their own section below; no inline glyph — the
    # core Helvetica font has no ↗, which would render as tofu.)
    desc_bits = [beleg.get("haendler") or beleg.get("unterkategorie") or beleg.get("notiz") or "—"]
    if beleg.get("projekt"):
        desc_bits.append("· " + str(beleg["projekt"]))
    desc = " ".join(str(b) for b in desc_bits)
    orig = ""
    if beleg.get("waehrung") and beleg.get("waehrung") != "CHF" and beleg.get("betrag_original") is not None:
        orig = f"{chf(beleg['betrag_original'])} {beleg['waehrung']}"
    vals = [
        (beleg.get("beleg_datum") or beleg.get("datum") or "", "l"),
        (beleg.get("kategorie") or "", "l"),
        (desc, "l"),
        (beleg.get("zahlungsart") or "", "l"),
        (orig, "r"),
        (chf(beleg.get("betrag_chf")), "r"),
    ]
    x = MARGIN_X + 6
    for (text, _), (_, w, align) in zip(vals, COLS):
        t = _clip(c, str(text), w - 10, "Helvetica", 8.5)
        if align == "r":
            c.drawRightString(x + w - 8, y - 12.5, t)
        else:
            c.drawString(x, y - 12.5, t)
        x += w
    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    c.line(MARGIN_X, y - rh, PAGE_W - MARGIN_X, y - rh)
    return y - rh


def _footer(c: canvas.Canvas, page_no: int):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, BOTTOM - 6, PAGE_W - MARGIN_X, BOTTOM - 6)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.2)
    c.drawString(MARGIN_X, BOTTOM - 18,
                 "Fremdwährungen zum Tageskurs (frankfurter.dev / EZB). "
                 "Pauschalen gemäss KnowGravity-Spesenreglement.")
    c.drawRightString(PAGE_W - MARGIN_X, BOTTOM - 18,
                      f"Erstellt mit KnowSpesen · Seite {page_no}")


def generate_spesen_pdf(month_data: dict) -> str:
    d = month_data
    name = (d.get("knowbody") or {}).get("name", "KnowBody").replace(" ", "_")
    jm = d.get("jahr_monat", "")
    out_path = os.path.join(_output_dir(), f"Spesenabrechnung_{name}_{jm}.pdf")

    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(f"Spesenabrechnung {name} {jm}")
    c.setAuthor("KnowSpesen")

    page_no = 1
    _header_band(c, d)

    # meta line
    y = PAGE_H - 118
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_X, y, f"Erstellt am {d.get('erstellt_am', '')}   ·   "
                              f"{d.get('anzahl', 0)} Belege   ·   "
                              f"Total CHF {chf(d.get('total_chf'))}")
    y -= 20

    y = _table_header(c, y)
    belege = d.get("belege") or []
    for i, b in enumerate(belege):
        if y < BOTTOM + 24:
            _footer(c, page_no)
            c.showPage()
            page_no += 1
            y = TOP
            y = _table_header(c, y)
        y = _row(c, y, b, zebra=(i % 2 == 1))

    # --- totals block ---
    if y < BOTTOM + 150:
        _footer(c, page_no)
        c.showPage()
        page_no += 1
        y = TOP
    y -= 14

    # category subtotals (left) + grand total (right box)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN_X, y, "Zusammenfassung nach Kategorie")
    y -= 6
    c.setStrokeColor(LINE)
    c.line(MARGIN_X, y, MARGIN_X + 250, y)
    y -= 16
    c.setFont("Helvetica", 9.5)
    for kat, summe in (d.get("kategorie_summen") or {}).items():
        c.setFillColor(INK)
        c.drawString(MARGIN_X + 4, y, str(kat))
        c.drawRightString(MARGIN_X + 250, y, "CHF " + chf(summe))
        y -= 15

    # total box (right)
    box_y = y + 15
    c.setFillColor(NAVY)
    c.rect(PAGE_W - MARGIN_X - 200, box_y - 6, 200, 40, fill=1, stroke=0)
    c.setFillColor(HexColor("#AEBBD4"))
    c.setFont("Helvetica", 9)
    c.drawString(PAGE_W - MARGIN_X - 190, box_y + 18, "TOTAL SPESEN")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(PAGE_W - MARGIN_X - 10, box_y + 2, "CHF " + chf(d.get("total_chf")))

    # weiterverrechenbar section
    weiter = d.get("weiterverrechenbar") or []
    if weiter:
        y -= 18
        if y < BOTTOM + 80:
            _footer(c, page_no)
            c.showPage()
            page_no += 1
            y = TOP
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN_X, y, "Weiterverrechenbare Spesen (an Kunden)")
        y -= 6
        c.setStrokeColor(LINE)
        c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
        y -= 15
        c.setFont("Helvetica", 9)
        for b in weiter:
            c.setFillColor(INK)
            line = f"{b.get('beleg_datum') or b.get('datum') or ''}  ·  " \
                   f"{b.get('haendler') or b.get('unterkategorie') or b.get('kategorie') or ''}"
            if b.get("projekt"):
                line += f"  ({b['projekt']})"
            c.drawString(MARGIN_X + 4, y, _clip(c, line, 380, "Helvetica", 9))
            c.drawRightString(PAGE_W - MARGIN_X, y, "CHF " + chf(b.get("betrag_chf")))
            y -= 14
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(PAGE_W - MARGIN_X, y - 2, "Summe weiterverrechenbar: CHF " + chf(d.get("summe_weiter_chf")))
        y -= 14

    # --- Kontroll-Bestätigung (typed attestation, name + timestamp) ---
    attest = d.get("attest") or {}
    if attest.get("text"):
        y -= 22
        if y < BOTTOM + 70:
            _footer(c, page_no)
            c.showPage()
            page_no += 1
            y = TOP
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
        y -= 15
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN_X, y, "Bestätigung")
        y -= 15
        c.setFillColor(INK)
        c.setFont("Helvetica-Oblique", 9)
        for line in _wrap(c, "«" + attest["text"] + "»", PAGE_W - 2 * MARGIN_X, "Helvetica-Oblique", 9):
            if y < BOTTOM + 14:  # robust to any future (longer) attestation wording
                _footer(c, page_no)
                c.showPage()
                page_no += 1
                y = TOP
                c.setFillColor(INK)
                c.setFont("Helvetica-Oblique", 9)
            c.drawString(MARGIN_X, y, line)
            y -= 13
        y -= 3
        if y < BOTTOM + 14:
            _footer(c, page_no)
            c.showPage()
            page_no += 1
            y = TOP
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        _von = attest.get("von", "")
        _am = attest.get("am", "")
        c.drawString(MARGIN_X, y, f"{_von}   ·   {_am}".strip(" ·"))

    _footer(c, page_no)
    c.save()
    return out_path
