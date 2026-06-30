#!/usr/bin/env python3
"""Offline tests for spesen.currency — FX conversion + mandatory manual fallback.

Run: python3 tools/test_spesen_currency.py   (exit 0 = pass). HTTP is monkeypatched,
so this never touches the network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spesen import currency

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- CHF identity: no network call at all -----------------------------------
def _boom(url):
    raise AssertionError("network must not be called for CHF")


currency._fetch_json = _boom
chf = currency.convert_to_chf(87.50, "CHF", "2026-01-20")
check("CHF -> identity 87.50", chf["ok"] and chf["betrag_chf"] == 87.50 and chf["wechselkurs"] == 1.0)
check("CHF -> Quelle DIREKT_CHF", chf["kurs_quelle"] == "DIREKT_CHF")


# --- EUR conversion against a pinned frankfurter fixture ---------------------
def _fixture(url):
    assert "base=EUR" in url and "symbols=CHF" in url, url
    return {"amount": 1, "base": "EUR", "date": "2026-01-20", "rates": {"CHF": 0.95}}


currency._fetch_json = _fixture
eur = currency.convert_to_chf(142.00, "EUR", "2026-01-20")
check("EUR 142 @0.95 -> 134.90", eur["ok"] and eur["betrag_chf"] == round(142.00 * 0.95, 2))
check("EUR -> Kurs 0.95 gespeichert", eur["wechselkurs"] == 0.95)
check("EUR -> Quelle frankfurter.dev", eur["kurs_quelle"] == "frankfurter.dev")
check("EUR -> Kursdatum übernommen", eur["kurs_datum"] == "2026-01-20")


# --- API down -> mandatory manual fallback (ok=False, betrag None) ----------
def _down(url):
    raise OSError("connection refused")


currency._fetch_json = _down
fail = currency.convert_to_chf(200.00, "USD", "2026-01-25")
check("API-Ausfall -> ok=False", fail["ok"] is False)
check("API-Ausfall -> betrag_chf None (kein stiller 0)", fail["betrag_chf"] is None)
check("API-Ausfall -> Fehlermeldung gesetzt", bool(fail["error"]))


# --- rate missing in response -> failure, not a crash -----------------------
def _no_chf(url):
    return {"amount": 1, "base": "USD", "date": "2026-01-25", "rates": {}}


currency._fetch_json = _no_chf
nochf = currency.convert_to_chf(200.00, "USD", "2026-01-25")
check("Fehlender Kurs -> ok=False", nochf["ok"] is False and nochf["betrag_chf"] is None)


# --- invalid amount ----------------------------------------------------------
bad = currency.convert_to_chf("abc", "EUR", "2026-01-20")
check("Ungültiger Betrag -> ok=False", bad["ok"] is False)


if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (currency)")
sys.exit(0)
