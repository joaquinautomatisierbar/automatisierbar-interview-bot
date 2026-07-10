#!/usr/bin/env python3
"""Offline tests for spesen.pauschalen — the per-diem + Kaffeekasse rules.

Run: python3 tools/test_spesen_pauschalen.py   (exit 0 = pass). No network, no DB.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spesen import pauschalen, config

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- Kaffeekasse / CHF-50 minimum -------------------------------------------
check("pauschale 49.99 -> Kaffeekasse", pauschalen.is_kaffeekasse(49.99, ist_pauschale=True) is True)
check("pauschale 50.00 -> nicht Kaffeekasse", pauschalen.is_kaffeekasse(50.00, ist_pauschale=True) is False)
check("pauschale 30.00 -> Kaffeekasse (Steueramt)", pauschalen.is_kaffeekasse(30.00, ist_pauschale=True) is True)
check("Beleg 100.00 -> nicht Kaffeekasse", pauschalen.is_kaffeekasse(100.00, ist_pauschale=False) is False)
check("Betrag None -> nicht Kaffeekasse", pauschalen.is_kaffeekasse(None, ist_pauschale=True) is False)
# small receipted item follows the config toggle (default True)
expected_small = bool(config.KAFFEEKASSE_ALSO_SMALL_RECEIPTS)
check("Beleg 12.00 folgt Config-Toggle", pauschalen.is_kaffeekasse(12.00, ist_pauschale=False) is expected_small)

# --- Known flat tariffs (client-confirmed via example sheets, 2026-07-10) ----
mittag = pauschalen.resolve_by_code("mittagessen_kunde")
check("Mittagessen = 30.00", mittag["ok"] and mittag["betrag_chf"] == 30.00)
frueh = pauschalen.resolve_by_code("fruehstueck_vor_8")
check("Frühstück = 10.00", frueh["ok"] and frueh["betrag_chf"] == 10.00)
nachtessen = pauschalen.resolve_by_code("abendessen_kunde")
check("Nachtessen = 30.00", nachtessen["ok"] and nachtessen["betrag_chf"] == 30.00)
autokm = pauschalen.resolve_by_code("auto_km")
check("Autokilometer = 0.70/km", autokm["ok"] and autokm["betrag_chf"] == 0.70)

# --- Still-unknown tariff is a guarded placeholder, never a number -----------
uebern = pauschalen.resolve_by_code("uebernachtung")
check("Übernachtung -> Platzhalter, kein Betrag",
      uebern["ok"] is False and uebern["is_placeholder"] is True and uebern["betrag_chf"] is None)
check("Übernachtung -> 'Tarif folgt' Meldung", "Tarif folgt" in (uebern["error"] or ""))

# --- per-km / per-night multiply (synthetic known rate) ---------------------
km = pauschalen.resolve_pauschale(
    {"code": "x", "label": "km", "rate_chf": 0.70, "unit": "pro_km", "is_placeholder": False}, menge=100)
check("0.70/km * 100 = 70.00", km["ok"] and km["betrag_chf"] == 70.00)
nacht = pauschalen.resolve_pauschale(
    {"code": "n", "label": "n", "rate_chf": 150.0, "unit": "pro_nacht", "is_placeholder": False}, menge=3)
check("150/Nacht * 3 = 450.00", nacht["ok"] and nacht["betrag_chf"] == 450.00)

# --- unknown code is handled, not crashed -----------------------------------
bogus = pauschalen.resolve_by_code("does_not_exist")
check("Unbekannter Code -> ok=False, kein Crash", bogus["ok"] is False and bogus["betrag_chf"] is None)


if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (pauschalen)")
sys.exit(0)
