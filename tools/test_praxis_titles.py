#!/usr/bin/env python3
"""Offline tests for praxis_ulrich.titles — list validation, date suffix, filenames.

Run: python3 tools/test_praxis_titles.py
"""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BEFUND_DATA_DIR", tempfile.mkdtemp(prefix="befund_titles_"))

from praxis_ulrich import titles, config  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- resolve_titel ---------------------------------------------------------------
t, aus = titles.resolve_titel("Urinkultur")
check("exakter Listen-Match", t == "Urinkultur" and aus is True)
t, aus = titles.resolve_titel("  Urinkultur  ")
check("Whitespace getrimmt, Match bleibt", t == "Urinkultur" and aus is True)
t, aus = titles.resolve_titel("urinkultur")
check("Case-Mismatch -> Freitext (exakt heisst exakt)", aus is False)
t, aus = titles.resolve_titel("Schilddrüsen-Laborbefund")
check("Freitext durchgereicht", t == "Schilddrüsen-Laborbefund" and aus is False)
t, aus = titles.resolve_titel("X" * 200)
check("Freitext gekappt", len(t) <= config.FREITITEL_MAX_LEN)
t, aus = titles.resolve_titel(None)
check("leer -> Befundbericht", t == "Befundbericht" and aus is False)
t, aus = titles.resolve_titel("NIPT   V-Natal")
check("Innen-Whitespace kollabiert -> Listen-Match", t == "NIPT V-Natal" and aus is True)

# --- datum_suffix -----------------------------------------------------------------
d, f = titles.datum_suffix("10.06.2026", None)
check("Berichtsdatum primär", d == "06/2026" and f == "06-2026")
d, f = titles.datum_suffix(None, datetime(2026, 7, 2, 9, 32))
check("E-Mail-Datum Fallback", d == "07/2026" and f == "07-2026")
d, f = titles.datum_suffix("kaputt", datetime(2026, 7, 2))
check("kaputtes Berichtsdatum -> Fallback", d == "07/2026")
d, f = titles.datum_suffix(None, None)
check("Notfall-Fallback heute (existiert immer)", "/" in d and "-" in f)

check("dokumenttitel Format", titles.dokumenttitel("Urinkultur", "06/2026") == "Urinkultur 06/2026")

# --- build_filename ----------------------------------------------------------------
fn = titles.build_filename("Urinkultur", "06-2026", "Muster", "Maria")
check("Standard-Dateiname", fn == "Urinkultur 06-2026_Muster_Maria.pdf")
fn = titles.build_filename("Operationsbericht Spital", "06-2026", "Müller-Lüthi", "Zoë")
check("Umlaute bleiben", "Müller-Lüthi" in fn and "Zoë" in fn)
fn = titles.build_filename('Bericht<>:"/\\|?*', "06-2026", "Muster", "Maria")
check("verbotene Zeichen ersetzt", not any(c in fn for c in '<>:"/\\|?*'))
check("endet .pdf", fn.endswith(".pdf"))
fn = titles.build_filename("T" * 300, "06-2026", "Langname-Langname", "Vorname")
check("Länge gekappt", len(fn) <= titles.FILENAME_MAX_LEN)
check("Patient nie abgeschnitten", fn.endswith("_Langname-Langname_Vorname.pdf"))
fn = titles.build_filename("NIPT (V-Natal) mit Geschlechtsangabe", "06-2026", "Muster", "")
check("leerer Vorname ok", fn.endswith("_Muster_.pdf"))

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
