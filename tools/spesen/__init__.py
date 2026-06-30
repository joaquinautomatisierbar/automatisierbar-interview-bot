"""KnowSpesen — Swiss expense/per-diem capture & reporting for KnowGravity.

A self-contained Flask-served PWA (routes live in api.py, host-sniffed to
knowspesen.automatisierbar.ch). This package holds all the deterministic logic
so api.py stays thin and every piece is offline-testable:

  config.py      single edit-point: categories, payment methods, Pauschaltarife
  db.py          sqlite3 schema + seed + query helpers (SPESEN_DB_PATH)
  pauschalen.py  per-diem engine (CHF 50 min, Kaffeekasse flag, placeholder guard)
  currency.py    foreign-currency -> CHF (frankfurter.dev + manual fallback)
  ocr.py         Claude Vision receipt extraction (advisory; human always confirms)
  capture.py     validate + normalise a beleg + persist the receipt image
  report_pdf.py  Spesenabrechnung PDF (reportlab, navy theme)
  report_excel.py Excel summary (openpyxl)
  month_close.py PDF + Excel + renamed receipts -> ZIP (stdlib zipfile)
  email_draft.py ready-to-send accountant mail (subject + body + mailto)
  reminder.py    monthly "noch offen" reminder (VPS cron, dry-run by default)
"""
