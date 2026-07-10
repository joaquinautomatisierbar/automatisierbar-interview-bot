"""report_excel.py — the monthly Spesen Excel (openpyxl).

generate_spesen_xlsx(month_data) -> path. Two sheets:
  "Spesen"          one row per beleg, numeric CHF column the accountant can sum
  "Zusammenfassung" category subtotals + grand total + weiterverrechenbar total

Same month_data shape as report_pdf.generate_spesen_pdf.
"""

from __future__ import annotations

import os
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

NAVY = "004040"   # KnowGravity deep petrol
NAVY_FONT = Font(color="FFFFFF", bold=True, size=11)
HEAD_FILL = PatternFill("solid", fgColor=NAVY)
BOLD = Font(bold=True)
RIGHT = Alignment(horizontal="right")
THIN = Side(style="thin", color="D9DEE6")
BORDER = Border(bottom=THIN)

_HEADERS = [
    ("Datum", 12), ("Kategorie", 16), ("Unterkategorie", 22), ("Beschreibung", 26),
    ("Betrag Original", 14), ("Währung", 9), ("Kurs", 9), ("Betrag CHF", 13),
    ("Zahlungsart", 18), ("Projekt/Kunde", 20), ("Weiterverr.", 11),
]


def _output_dir() -> str:
    d = os.environ.get("SPESEN_OUTPUT_DIR") or str(Path(__file__).resolve().parents[2] / ".tmp")
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


def generate_spesen_xlsx(month_data: dict) -> str:
    d = month_data
    name = (d.get("knowbody") or {}).get("name", "KnowBody").replace(" ", "_")
    jm = d.get("jahr_monat", "")
    out_path = os.path.join(_output_dir(), f"Spesenabrechnung_{name}_{jm}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Spesen"

    # header
    for col, (label, width) in enumerate(_HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = NAVY_FONT
        cell.fill = HEAD_FILL
        ws.column_dimensions[cell.column_letter].width = width

    r = 2
    for b in (d.get("belege") or []):
        ws.cell(row=r, column=1, value=b.get("beleg_datum") or b.get("datum") or "")
        ws.cell(row=r, column=2, value=b.get("kategorie") or "")
        ws.cell(row=r, column=3, value=b.get("unterkategorie") or "")
        ws.cell(row=r, column=4, value=b.get("haendler") or b.get("notiz") or "")
        ws.cell(row=r, column=5, value=b.get("betrag_original"))
        ws.cell(row=r, column=6, value=b.get("waehrung") or "")
        ws.cell(row=r, column=7, value=b.get("wechselkurs"))
        chf_cell = ws.cell(row=r, column=8, value=round(float(b.get("betrag_chf") or 0), 2))
        chf_cell.number_format = "#,##0.00"
        ws.cell(row=r, column=9, value=b.get("zahlungsart") or "")
        ws.cell(row=r, column=10, value=b.get("projekt") or "")
        ws.cell(row=r, column=11, value="ja" if b.get("weiterverrechenbar") else "")
        r += 1

    # total row
    ws.cell(row=r, column=7, value="Total CHF").font = BOLD
    total_cell = ws.cell(row=r, column=8, value=round(float(d.get("total_chf") or 0), 2))
    total_cell.font = BOLD
    total_cell.number_format = "#,##0.00"
    ws.freeze_panes = "A2"

    # summary sheet
    ws2 = wb.create_sheet("Zusammenfassung")
    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["B"].width = 16
    ws2.cell(row=1, column=1, value=f"Spesenabrechnung {name} {jm}").font = Font(bold=True, size=13)
    ws2.cell(row=2, column=1, value=f"Erstellt am {d.get('erstellt_am', '')}  ·  {d.get('anzahl', 0)} Belege")
    row = 4
    ws2.cell(row=row, column=1, value="Kategorie").font = NAVY_FONT
    ws2.cell(row=row, column=1).fill = HEAD_FILL
    ws2.cell(row=row, column=2, value="Total CHF").font = NAVY_FONT
    ws2.cell(row=row, column=2).fill = HEAD_FILL
    row += 1
    for kat, summe in (d.get("kategorie_summen") or {}).items():
        ws2.cell(row=row, column=1, value=str(kat))
        cc = ws2.cell(row=row, column=2, value=round(float(summe), 2))
        cc.number_format = "#,##0.00"
        row += 1
    row += 1
    ws2.cell(row=row, column=1, value="TOTAL SPESEN").font = BOLD
    tc = ws2.cell(row=row, column=2, value=round(float(d.get("total_chf") or 0), 2))
    tc.font = BOLD
    tc.number_format = "#,##0.00"
    row += 1
    ws2.cell(row=row, column=1, value="davon weiterverrechenbar")
    wc = ws2.cell(row=row, column=2, value=round(float(d.get("summe_weiter_chf") or 0), 2))
    wc.number_format = "#,##0.00"

    _verpflegung_sheet(wb, d)

    wb.save(out_path)
    return out_path


_V_HEADERS = [
    ("Datum", 12), ("Wtg", 6),
    ("Frühstück CHF", 14), ("F-Deckung", 11),
    ("Mittag CHF", 12), ("M-Deckung", 11),
    ("Nacht CHF", 12), ("N-Deckung", 11),
    ("V", 5), ("N", 5), (">19:30", 8), ("<07:30", 8), ("Bemerkung", 26),
]


def _verpflegung_sheet(wb, d: dict) -> None:
    """Third sheet 'Verpflegung': one numeric row per calendar day + totals + km,
    so the accountant can sum. Skipped when the month has no grid data."""
    import calendar
    from datetime import date
    v = d.get("verpflegung") or {}
    summary = v.get("summary")
    if not summary:
        return
    meals = summary.get("meals", {})
    has = any((meals.get(s, {}) or {}).get("count") for s in ("fruehstueck", "mittag", "nacht")) \
        or bool((summary.get("km") or {}).get("total"))
    if not has:
        return

    jm = d.get("jahr_monat", "")
    try:
        y_, m_ = int(jm[:4]), int(jm[5:7])
        ndays = calendar.monthrange(y_, m_)[1]
    except Exception:
        return
    stored = {r.get("tag_datum"): r for r in (v.get("days") or [])}
    wd = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    ws = wb.create_sheet("Verpflegung")
    for col, (label, width) in enumerate(_V_HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = NAVY_FONT
        cell.fill = HEAD_FILL
        ws.column_dimensions[cell.column_letter].width = width

    def _rate(slot):
        m = meals.get(slot, {})
        return None if m.get("is_placeholder") else m.get("rate_chf")

    r = 2
    for dd in range(1, ndays + 1):
        dt = date(y_, m_, dd)
        row = stored.get(dt.isoformat(), {})
        ws.cell(row=r, column=1, value=dt.strftime("%d.%m.%Y"))
        ws.cell(row=r, column=2, value=wd[dt.weekday()])
        for (claim_k, deck_k, slot, cchf, cdeck) in [
            ("fr_claimed", "fr_deckung", "fruehstueck", 3, 4),
            ("mi_claimed", "mi_deckung", "mittag", 5, 6),
            ("na_claimed", "na_deckung", "nacht", 7, 8),
        ]:
            if row.get(claim_k):
                cc = ws.cell(row=r, column=cchf, value=_rate(slot))
                cc.number_format = "#,##0.00"
                ws.cell(row=r, column=cdeck, value=row.get(deck_k) or "")
        ws.cell(row=r, column=9, value="X" if row.get("arb_vormittag") else "")
        ws.cell(row=r, column=10, value="X" if row.get("arb_nachmittag") else "")
        ws.cell(row=r, column=11, value="X" if row.get("arb_spaet") else "")
        ws.cell(row=r, column=12, value="X" if row.get("arb_frueh") else "")
        ws.cell(row=r, column=13, value=row.get("bemerkung") or "")
        r += 1

    # totals row
    ws.cell(row=r, column=1, value="Total").font = BOLD
    for slot, col in (("fruehstueck", 3), ("mittag", 5), ("nacht", 7)):
        m = meals.get(slot, {})
        tc = ws.cell(row=r, column=col, value=(None if m.get("total_chf") is None else round(m["total_chf"], 2)))
        tc.font = BOLD
        tc.number_format = "#,##0.00"
    vt = summary.get("verpflegung_total_chf")
    ws.cell(row=r, column=8, value="Ausw. Verpf.").font = BOLD
    vtc = ws.cell(row=r, column=9, value=(None if vt is None else round(vt, 2)))
    vtc.font = BOLD
    vtc.number_format = "#,##0.00"
    ws.freeze_panes = "A2"

    # km block
    km = summary.get("km") or {}
    r += 2
    ws.cell(row=r, column=1, value="Kilometerspesen").font = Font(bold=True, size=12)
    rows = [
        ("Kilometerstand Anfang", km.get("start")),
        ("Kilometerstand Ende", km.get("end")),
        ("Gefahrene km (Total)", km.get("total")),
        ("Geschäftlich" + (" (manuell)" if km.get("firma_is_override") else " (5/7)"), km.get("firma")),
        ("Ansatz CHF/km", None if km.get("is_placeholder") else km.get("rate_chf")),
        ("Km-Entschädigung CHF", km.get("entschaedigung_chf")),
    ]
    for label, val in rows:
        r += 1
        ws.cell(row=r, column=1, value=label)
        cc = ws.cell(row=r, column=3, value=val)
        if isinstance(val, (int, float)):
            cc.number_format = "#,##0.00"
    ws.cell(row=r, column=1).font = BOLD
    ws.cell(row=r, column=3).font = BOLD
