#!/usr/bin/env python3
"""Offline integration test for the month-close pipeline (DB -> PDF+Excel+ZIP).

Run: python3 tools/test_spesen_month_close.py   (exit 0 = pass). Uses a temp DB,
temp receipt dir and temp output dir; no network. Exercises real reportlab/openpyxl
+ zipfile, so it proves the deliverable actually builds.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_DBDIR = tempfile.mkdtemp(prefix="spesen_db_")
os.environ["SPESEN_DB_PATH"] = os.path.join(_DBDIR, "knowspesen.db")
os.environ["SPESEN_RECEIPT_DIR"] = tempfile.mkdtemp(prefix="spesen_rcpt_")
os.environ["SPESEN_OUTPUT_DIR"] = tempfile.mkdtemp(prefix="spesen_out_")

from spesen import db, capture, month_close

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


db.init_db()
kb = db.upsert_knowbody("Markus Schacher", "markus@knowgravity.com", "tok-markus")

jpeg = b"\xff\xd8\xff\xe0" + b"0" * 80
img1 = capture.save_receipt_image("Markus", jpeg, "image/jpeg")
img2 = capture.save_receipt_image("Markus", jpeg, "image/jpeg")
img3 = capture.save_receipt_image("Markus", jpeg, "image/jpeg")

# included: normal CHF
db.insert_beleg({"knowbody_id": kb, "art": "beleg", "haendler": "Hiltl",
                 "beleg_datum": "2026-06-10", "betrag_original": 87.50, "waehrung": "CHF",
                 "betrag_chf": 87.50, "kategorie": "Mahlzeit", "zahlungsart": "Firmenkreditkarte",
                 "weiterverrechenbar": 0, "ist_kaffeekasse": 0, "bild_pfad": img1})
# included: EUR converted, weiterverrechenbar
db.insert_beleg({"knowbody_id": kb, "art": "beleg", "haendler": "Hotel Berlin",
                 "beleg_datum": "2026-06-20", "betrag_original": 142.00, "waehrung": "EUR",
                 "wechselkurs": 0.95, "kurs_quelle": "frankfurter.dev", "betrag_chf": 134.90,
                 "kategorie": "Unterkunft", "zahlungsart": "Privat-Kreditkarte",
                 "projekt": "Kunde Berlin", "weiterverrechenbar": 1, "ist_kaffeekasse": 0,
                 "bild_pfad": img2})
# excluded: Kaffeekasse (< 50)
db.insert_beleg({"knowbody_id": kb, "art": "beleg", "haendler": "Coop",
                 "beleg_datum": "2026-06-22", "betrag_original": 12.00, "waehrung": "CHF",
                 "betrag_chf": 12.00, "kategorie": "Material", "zahlungsart": "Privat-Cash",
                 "weiterverrechenbar": 0, "ist_kaffeekasse": 1, "bild_pfad": img3})
# different month -> must not appear
db.insert_beleg({"knowbody_id": kb, "art": "beleg", "haendler": "Mai-Beleg",
                 "beleg_datum": "2026-05-05", "betrag_original": 99.0, "waehrung": "CHF",
                 "betrag_chf": 99.0, "kategorie": "Mahlzeit", "zahlungsart": "Firmenkreditkarte",
                 "weiterverrechenbar": 0, "ist_kaffeekasse": 0})

res = month_close.close_month(kb, "2026-06", accountant_email="buchhaltung@gubser-kalt.ch")

check("close ok", res.get("ok") is True)
check("anzahl = 2 (Kaffeekasse + anderer Monat raus)", res.get("anzahl") == 2)
check("total = 222.40", abs(res.get("total_chf", 0) - 222.40) < 0.001)
check("weiterverrechenbar = 134.90", abs(res.get("summe_weiter_chf", 0) - 134.90) < 0.001)

check("PDF existiert + nicht leer", os.path.getsize(res["pdf_path"]) > 800)
check("Excel existiert + nicht leer", os.path.getsize(res["xlsx_path"]) > 800)
check("ZIP existiert", os.path.isfile(res["zip_path"]))

names = zipfile.ZipFile(res["zip_path"]).namelist()
check("ZIP enthält PDF", any(n.endswith(".pdf") for n in names))
check("ZIP enthält Excel", any(n.endswith(".xlsx") for n in names))
check("ZIP enthält Begleitmail.txt", "Begleitmail.txt" in names)
belege_imgs = [n for n in names if n.startswith("Belege/")]
check("ZIP enthält 2 Belege (Kaffeekasse ausgeschlossen)", len(belege_imgs) == 2)

# email draft
check("Email-Betreff enthält Namen + Monat",
      "Markus" in res["email"]["subject"] and "Juni 2026" in res["email"]["subject"])
check("Email mailto an Buchhaltung", res["email"]["mailto"].startswith("mailto:buchhaltung@gubser-kalt.ch"))
check("Email-Text ohne Gedankenstrich", "—" not in res["email"]["body"] and "–" not in res["email"]["body"])

# locking
rows = db.list_belege(kb, "2026-06")
locked = [r for r in rows if r["monatsabschluss_id"] is not None]
kaffee = [r for r in rows if r["ist_kaffeekasse"] == 1]
check("2 Belege gesperrt", len(locked) == 2)
check("Kaffeekasse NICHT gesperrt", kaffee and kaffee[0]["monatsabschluss_id"] is None)

# locked beleg can't be edited/deleted
locked_id = locked[0]["id"]
check("gesperrter Beleg nicht editierbar", db.update_beleg(locked_id, {"haendler": "x"}) is False)
check("gesperrter Beleg nicht löschbar", db.delete_beleg(locked_id) is False)

# re-close is idempotent (regenerates, no crash, same count)
res2 = month_close.close_month(kb, "2026-06", accountant_email="buchhaltung@gubser-kalt.ch")
check("re-close ok + gleiche Anzahl", res2.get("ok") and res2.get("anzahl") == 2)

# --- reopen unlocks the month again ---
check("reopen ok", db.reopen_close(kb, "2026-06") is True)
rows2 = db.list_belege(kb, "2026-06")
check("nach reopen: keine Sperre mehr", all(r["monatsabschluss_id"] is None for r in rows2))
check("nach reopen: get_close None", db.get_close(kb, "2026-06") is None)
check("nach reopen: Beleg wieder editierbar", db.update_beleg(locked_id, {"haendler": "Hiltl neu"}) is True)
check("reopen ohne Abschluss -> False", db.reopen_close(kb, "2030-01") is False)

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (month_close)")
sys.exit(0)
