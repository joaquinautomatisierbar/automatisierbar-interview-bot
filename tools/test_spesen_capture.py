#!/usr/bin/env python3
"""Offline tests for spesen.capture — validation, image save, field assembly.

Run: python3 tools/test_spesen_capture.py   (exit 0 = pass). No network, no DB.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Point the receipt dir at a temp folder BEFORE importing the module.
_TMP = tempfile.mkdtemp(prefix="spesen_receipts_")
os.environ["SPESEN_RECEIPT_DIR"] = _TMP

from spesen import capture

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- validation --------------------------------------------------------------
good = {"art": "beleg", "datum": "2026-06-15", "kategorie": "Mahlzeit",
        "betrag_original": 42.5, "waehrung": "CHF", "zahlungsart": "Firmenkreditkarte"}
check("gültiger Beleg -> keine Fehler", capture.validate_beleg_payload(good) == [])

check("fehlendes Datum erkannt", "datum" in capture.validate_beleg_payload({**good, "datum": ""}))
check("falsches Datumsformat erkannt", "datum" in capture.validate_beleg_payload({**good, "datum": "15.06.2026"}))
check("fehlende Kategorie erkannt", "kategorie" in capture.validate_beleg_payload({**good, "kategorie": ""}))
check("Betrag <= 0 erkannt", "betrag_original" in capture.validate_beleg_payload({**good, "betrag_original": 0}))
check("ungültige Währung erkannt", "waehrung" in capture.validate_beleg_payload({**good, "waehrung": "Franken"}))

paus = {"art": "pauschale", "datum": "2026-06-15", "kategorie": "Mahlzeit", "pauschale_code": ""}
check("Pauschale ohne Code erkannt", "pauschale_code" in capture.validate_beleg_payload(paus))
check("Pauschale mit Code ok",
      capture.validate_beleg_payload({**paus, "pauschale_code": "mittagessen_kunde"}) == [])

# --- image save --------------------------------------------------------------
jpeg = b"\xff\xd8\xff\xe0" + b"0" * 64  # bytes don't need to be a real image to store
base = capture.save_receipt_image("Markus", jpeg, "image/jpeg", "beleg.jpg")
check("Bild gespeichert -> .jpg basename", base.endswith(".jpg") and "Markus" in base)
check("Bild liegt im Receipt-Dir", os.path.isfile(os.path.join(_TMP, base)))
check("abs_path_for stimmt", capture.abs_path_for(base) == os.path.join(_TMP, base))

try:
    capture.save_receipt_image("Markus", b"", "image/jpeg")
    check("leeres Bild -> ValueError", False)
except ValueError:
    check("leeres Bild -> ValueError", True)

try:
    capture.save_receipt_image("Markus", jpeg, "application/zip", "x.zip")
    check("unsupported type abgelehnt -> ValueError", False)
except ValueError:
    check("unsupported type abgelehnt -> ValueError", True)

# --- field assembly ----------------------------------------------------------
resolved = {"art": "beleg", "betrag_original": 142.0, "waehrung": "EUR",
            "wechselkurs": 0.95, "kurs_quelle": "frankfurter.dev", "betrag_chf": 134.90,
            "ist_kaffeekasse": False, "bild_pfad": base, "ocr_confidence": 0.91}
payload = {"haendler": "Hotel Berlin", "datum": "2026-06-15", "kategorie": "Unterkunft",
           "zahlungsart": "Privat-Kreditkarte", "weiterverrechenbar": "true", "projekt": "Kunde X"}
f = capture.build_beleg_fields(payload, knowbody_id=3, resolved=resolved)
check("fields: knowbody_id", f["knowbody_id"] == 3)
check("fields: betrag_chf durchgereicht", f["betrag_chf"] == 134.90)
check("fields: waehrung uppercase", f["waehrung"] == "EUR")
check("fields: weiterverrechenbar -> 1", f["weiterverrechenbar"] == 1)
check("fields: bild_pfad gesetzt", f["bild_pfad"] == base)
check("fields: ist_kaffeekasse -> 0", f["ist_kaffeekasse"] == 0)

# --- PDF receipts (SBB-Billett / Revolut) ---
check("PDF mime -> .pdf ext", capture.ext_for_image_mime("application/pdf", "sbb.pdf") == ".pdf")
check("octet-stream + .pdf name -> .pdf", capture.ext_for_image_mime("application/octet-stream", "x.pdf") == ".pdf")
pdf_base = capture.save_receipt_image("Markus", b"%PDF-1.4 fake", "application/pdf", "billet.pdf")
check("PDF gespeichert -> .pdf", pdf_base.endswith(".pdf") and os.path.isfile(os.path.join(_TMP, pdf_base)))
check("PDF-Payload validiert (mit Betrag)", capture.validate_beleg_payload(
    {"art": "beleg", "datum": "2026-06-15", "kategorie": "Transport",
     "betrag_original": 56, "waehrung": "CHF"}) == [])

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (capture)")
sys.exit(0)
