#!/usr/bin/env python3
"""Offline tests for walkin_card_ocr — sanitiser + fail-safe returns.

Run: python3 tools/test_walkin_card_ocr.py   (exit 0 = pass). No network, no API.
Only the pure logic is exercised; the Claude Vision call itself is never made.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import walkin_card_ocr as card
from walkin_capture import ROLE_OPTIONS

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- media type normalisation -----------------------------------------------
check("image/jpg -> image/jpeg", card._normalise_media_type("image/jpg") == "image/jpeg")
check("image/JPEG;charset -> image/jpeg", card._normalise_media_type("image/JPEG; x=1") == "image/jpeg")
check("image/png durch", card._normalise_media_type("image/png") == "image/png")
check("'' -> ''", card._normalise_media_type("") == "")

# --- _sanitise: role mapping (the enum guard) -------------------------------
kept = card._sanitise({"role": "Founder / Inhaber"})
check("gültige Rolle bleibt", kept["role"] == "Founder / Inhaber")
dropped = card._sanitise({"role": "Marketing Manager", "title": "Marketing Manager"})
check("Freitext-Rolle -> None", dropped["role"] is None)
check("aber title bleibt erhalten", dropped["title"] == "Marketing Manager")
check("jede ROLE_OPTION überlebt _sanitise",
      all(card._sanitise({"role": r})["role"] == r for r in ROLE_OPTIONS))

# --- _sanitise: email -------------------------------------------------------
check("E-Mail lowercased", card._sanitise({"email": "Anna@Firma.CH"})["email"] == "anna@firma.ch")
check("ungültige E-Mail -> None", card._sanitise({"email": "keine-email"})["email"] is None)
check("leere E-Mail -> None", card._sanitise({"email": ""})["email"] is None)

# --- _sanitise: website (strip scheme) --------------------------------------
check("https:// entfernt", card._sanitise({"website": "https://firma.ch"})["website"] == "firma.ch")
check("http:// + trailing slash entfernt", card._sanitise({"website": "http://firma.ch/"})["website"] == "firma.ch")
check("nackte Domain bleibt", card._sanitise({"website": "firma.ch"})["website"] == "firma.ch")
check("leere Website -> None", card._sanitise({"website": ""})["website"] is None)

# --- _sanitise: confidence clamp --------------------------------------------
check("confidence 2.0 -> 1.0", card._sanitise({"confidence": 2.0})["confidence"] == 1.0)
check("confidence -1 -> 0.0", card._sanitise({"confidence": -1})["confidence"] == 0.0)
check("confidence 'abc' -> 0.0", card._sanitise({"confidence": "abc"})["confidence"] == 0.0)
check("confidence 0.7 durch", card._sanitise({"confidence": 0.7})["confidence"] == 0.7)

# --- _sanitise: strings + shape ---------------------------------------------
s = card._sanitise({"name": "  Anna Meier  ", "company": " Furness AG ", "phone": " 044 111 22 33 ",
                    "city": "Baden", "postal_code": "5400", "address": "Bahnhofstrasse 1"})
check("name getrimmt", s["name"] == "Anna Meier")
check("company getrimmt", s["company"] == "Furness AG")
check("phone getrimmt", s["phone"] == "044 111 22 33")
check("city/plz/adresse durch", s["city"] == "Baden" and s["postal_code"] == "5400" and s["address"] == "Bahnhofstrasse 1")
empty = card._sanitise({})
check("leeres dict -> alle Felder None/0", all(empty[k] is None for k in
      ("name", "company", "title", "role", "email", "phone", "website", "city", "postal_code", "address"))
      and empty["confidence"] == 0.0)
check("_sanitise liefert genau die erwarteten Keys",
      set(empty.keys()) == {"name", "company", "title", "role", "email", "phone",
                            "website", "city", "postal_code", "address", "confidence"})

# --- extract_card: fail-safe (never raises, never hits the API) -------------
r_empty = card.extract_card(b"", "image/jpeg")
check("leeres Bild -> ok=False", r_empty["ok"] is False and r_empty["error"] == "leeres Bild")

r_badmime = card.extract_card(b"\xff\xd8\xff\xe0data", "application/zip")
check("falscher Typ -> ok=False + Hinweis", r_badmime["ok"] is False and "nicht unterstützt" in r_badmime["error"])
check("Fail-safe liefert volle Feld-Shape", all(k in r_badmime for k in
      ("ok", "name", "company", "role", "email", "phone", "website", "city", "confidence", "error")))

# no-key path: temporarily drop ANTHROPIC_API_KEY so the guard fires without an API call
_saved_key = os.environ.pop("ANTHROPIC_API_KEY", None)
try:
    r_nokey = card.extract_card(b"\xff\xd8\xff\xe0data", "image/jpeg")
    check("ohne API-Key -> OCR nicht konfiguriert",
          r_nokey["ok"] is False and r_nokey["error"] == "OCR nicht konfiguriert")
finally:
    if _saved_key is not None:
        os.environ["ANTHROPIC_API_KEY"] = _saved_key

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (walkin_card_ocr)")
sys.exit(0)
