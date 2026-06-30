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

NAVY = "1B2A4A"
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

    wb.save(out_path)
    return out_path
