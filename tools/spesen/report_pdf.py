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

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas

# --- KnowGravity brand palette: deep petrol + teal, professional ----------------
NAVY = HexColor("#004040")        # deep petrol (headers, totals) — brand primary
NAVY_DEEP = HexColor("#00302F")   # table-header band
INK = HexColor("#132422")
MUTED = HexColor("#5B7370")
LINE = HexColor("#D9E4E2")
ZEBRA = HexColor("#F1F6F5")
ACCENT = HexColor("#00897B")      # teal accent
GREEN = HexColor("#0F7B4F")
BRAND_SUB = HexColor("#9DC3BE")   # light petrol tint for header subtitles

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pt
MARGIN_X = 42
TOP = PAGE_H - 44
BOTTOM = 64

STATIC = Path(__file__).resolve().parents[2] / "static"
# Opaque petrol tile + white feather: its petrol edges blend into the petrol header
# band, so drawn on the band only the white feather shows (no alpha handling needed).
_BRAND_BADGE = STATIC / "spesen-icon-maskable.png"

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
    tx = MARGIN_X
    if _BRAND_BADGE.exists():
        c.drawImage(str(_BRAND_BADGE), MARGIN_X, PAGE_H - 78, width=46, height=46,
                    preserveAspectRatio=True)
        tx = MARGIN_X + 58
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(tx, PAGE_H - 50, "Spesenabrechnung")
    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_SUB)
    c.drawString(tx, PAGE_H - 68, "KnowGravity Inc.  ·  KnowSpesen")
    # right side: person + month
    name = (d.get("knowbody") or {}).get("name", "")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 48, name)
    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_SUB)
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
    _verpflegung_page(c, d)   # optional landscape Verpflegungs-/Kilometerblatt
    c.save()
    return out_path


# --- Verpflegungs- & Kilometerblatt (landscape page, mirrors the client sheet) --

_VMONTH_DAYS = None  # set per-call


def _grid_has_data(summary: dict | None) -> bool:
    if not summary:
        return False
    if any((summary.get("meals", {}).get(s, {}) or {}).get("count") for s in ("fruehstueck", "mittag", "nacht")):
        return True
    return bool((summary.get("km") or {}).get("total"))


def _verpflegung_page(c: canvas.Canvas, d: dict):
    """Append a landscape Verpflegungs- & Kilometerblatt page if the month has any
    grid data. Placeholder rates print a count but 'Tarif folgt', never a guess."""
    import calendar
    from datetime import date

    v = d.get("verpflegung") or {}
    summary = v.get("summary")
    if not _grid_has_data(summary):
        return

    jm = d.get("jahr_monat", "")
    try:
        y_, m_ = int(jm[:4]), int(jm[5:7])
        ndays = calendar.monthrange(y_, m_)[1]
    except Exception:
        return
    stored = {r.get("tag_datum"): r for r in (v.get("days") or [])}
    wd = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    c.showPage()
    c.setPageSize(landscape(A4))
    LW, LH = landscape(A4)                       # 841.89 x 595.27
    mx = 42
    content_w = LW - 2 * mx

    # header band
    c.setFillColor(NAVY)
    c.rect(0, LH - 70, LW, 70, fill=1, stroke=0)
    tx = mx
    if _BRAND_BADGE.exists():
        c.drawImage(str(_BRAND_BADGE), mx, LH - 58, width=38, height=38, preserveAspectRatio=True)
        tx = mx + 48
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(tx, LH - 34, "Verpflegungs- & Kilometerspesen")
    c.setFillColor(BRAND_SUB)
    c.setFont("Helvetica", 10)
    c.drawString(tx, LH - 50, "KnowGravity Inc.  ·  KnowSpesen")
    name = (d.get("knowbody") or {}).get("name", "")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(LW - mx, LH - 34, name)
    c.setFillColor(BRAND_SUB)
    c.setFont("Helvetica", 10)
    c.drawRightString(LW - mx, LH - 50, _month_label(jm))

    # columns: label, width, align
    cols = [("Tag", 52, "l"), ("Wtg", 40, "l"),
            ("Frühstück", 92, "l"), ("Mittag", 92, "l"), ("Nacht", 92, "l"),
            ("V", 26, "c"), ("N", 26, "c"), (">19:30", 46, "c"), ("<07:30", 46, "c"),
            ("Bemerkung", 0, "l")]
    fixed = sum(w for _, w, _ in cols if w)
    cols[-1] = ("Bemerkung", content_w - fixed, "l")

    def _draw_header(y):
        c.setFillColor(NAVY_DEEP)
        c.rect(mx, y - 15, content_w, 16, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        x = mx + 5
        for label, w, align in cols:
            if align == "c":
                c.drawCentredString(x + w / 2, y - 11, label)
            else:
                c.drawString(x, y - 11, label)
            x += w
        return y - 15

    meals = summary.get("meals", {})

    def _meal_cell(slot, row):
        claim = row.get({"fruehstueck": "fr_claimed", "mittag": "mi_claimed", "nacht": "na_claimed"}[slot])
        if not claim:
            return ""
        deck = row.get({"fruehstueck": "fr_deckung", "mittag": "mi_deckung", "nacht": "na_deckung"}[slot]) or ""
        m = meals.get(slot, {})
        amt = "?" if m.get("is_placeholder") else chf(m.get("rate_chf"))
        return f"{amt}  {deck}".strip()

    y = LH - 84
    y = _draw_header(y)
    rh = 13.0
    c.setFont("Helvetica", 8)
    for dd in range(1, ndays + 1):
        dt = date(y_, m_, dd)
        iso = dt.isoformat()
        row = stored.get(iso, {})
        is_we = dt.weekday() >= 5
        if y < 50:   # ultra-safety spill (31 rows at rh=13 fit one page; never trips normally)
            c.setFillColor(MUTED); c.setFont("Helvetica", 7.2)
            c.drawRightString(LW - mx, 40, f"Erstellt mit KnowSpesen · {_month_label(jm)}")
            c.showPage(); c.setPageSize(landscape(A4))
            y = LH - 60
            y = _draw_header(y)
            c.setFont("Helvetica", 8)
        if is_we:
            c.setFillColor(ZEBRA)
            c.rect(mx, y - rh, content_w, rh, fill=1, stroke=0)
        vals = [
            (dt.strftime("%d.%m."), "l"), (wd[dt.weekday()], "l"),
            (_meal_cell("fruehstueck", row), "l"), (_meal_cell("mittag", row), "l"),
            (_meal_cell("nacht", row), "l"),
            ("X" if row.get("arb_vormittag") else "", "c"), ("X" if row.get("arb_nachmittag") else "", "c"),
            ("X" if row.get("arb_spaet") else "", "c"), ("X" if row.get("arb_frueh") else "", "c"),
            (row.get("bemerkung") or "", "l"),
        ]
        c.setFillColor(INK)
        x = mx + 5
        for (text, _), (_, w, align) in zip(vals, cols):
            t = _clip(c, str(text), w - 6, "Helvetica", 8)
            if align == "c":
                c.drawCentredString(x + w / 2, y - 10, t)
            else:
                c.drawString(x, y - 10, t)
            x += w
        c.setStrokeColor(LINE); c.setLineWidth(0.3)
        c.line(mx, y - rh, LW - mx, y - rh)
        y -= rh

    # --- per-meal totals row --- (needs ~200pt for totals + km + signature)
    if y < 210:
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.2)
        c.drawRightString(LW - mx, 40, f"Erstellt mit KnowSpesen · {_month_label(jm)}")
        c.showPage(); c.setPageSize(landscape(A4))
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 12)
        c.drawString(mx, LH - 50, f"Verpflegungs- & Kilometerspesen — Zusammenfassung · {_month_label(jm)}")
        y = LH - 84
    y -= 4
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 8.5)
    x = mx + 5
    labels = {"fruehstueck": cols[2][1], "mittag": cols[3][1], "nacht": cols[4][1]}
    # Tag+Wtg span -> "Total"
    c.drawString(x, y - 10, "Total")
    x += cols[0][1] + cols[1][1]
    for slot in ("fruehstueck", "mittag", "nacht"):
        m = meals.get(slot, {})
        w = labels[slot]
        if m.get("count"):
            txt = "Tarif folgt" if m.get("is_placeholder") else f"{m['count']}× = CHF {chf(m.get('total_chf'))}"
        else:
            txt = "–"
        c.drawString(x, y - 10, _clip(c, txt, w - 6, "Helvetica-Bold", 8.5))
        x += w
    # Gesamttotal Verpflegung on the right
    vt = summary.get("verpflegung_total_chf")
    vt_txt = "Tarif folgt" if vt is None else "CHF " + chf(vt)
    c.drawRightString(LW - mx, y - 10, "Ausw. Verpflegung: " + vt_txt)
    y -= 34

    # --- Kilometer block ---
    km = summary.get("km") or {}
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 10)
    c.drawString(mx, y, "Kilometerspesen")
    y -= 4
    c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(mx, y, mx + 320, y)
    y -= 16
    c.setFont("Helvetica", 9); c.setFillColor(INK)

    def _km_line(label, value):
        nonlocal y
        c.setFillColor(MUTED); c.drawString(mx + 4, y, label)
        c.setFillColor(INK); c.drawString(mx + 220, y, value)
        y -= 14

    def _n(x):
        return "—" if x is None else (f"{x:.0f}" if float(x).is_integer() else f"{x}")

    _km_line("Kilometerstand Anfang / Ende", f"{_n(km.get('start'))}  /  {_n(km.get('end'))} km")
    _km_line("Gefahrene Kilometer (Total)", f"{_n(km.get('total'))} km")
    firma_lbl = "Geschäftlich (manuell)" if km.get("firma_is_override") else "Geschäftlich (5/7)"
    _km_line(firma_lbl, f"{_n(km.get('firma'))} km")
    rate_txt = "Tarif folgt" if km.get("is_placeholder") else f"CHF {chf(km.get('rate_chf'))}/km"
    _km_line("Ansatz", rate_txt)
    ent = km.get("entschaedigung_chf")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 10)
    c.drawString(mx + 4, y, "Km-Entschädigung")
    c.drawString(mx + 220, y, ("Tarif folgt" if ent is None else "CHF " + chf(ent)))
    y -= 26

    # combined payout + signature line
    tot = d.get("total_auszahlung_chf")
    if tot is not None:
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 11)
        c.drawRightString(LW - mx, y, "Total zur Auszahlung (Spesen + Verpflegung + Km): CHF " + chf(tot))
        y -= 26
    y = max(y, 70)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(mx, y, mx + 240, y)
    c.setFillColor(MUTED); c.setFont("Helvetica", 8.5)
    c.drawString(mx, y - 12, "Datum und Unterschrift")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.2)
    c.drawRightString(LW - mx, 40, f"Erstellt mit KnowSpesen · {_month_label(jm)}")
