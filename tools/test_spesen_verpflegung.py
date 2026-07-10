#!/usr/bin/env python3
"""Offline tests for spesen.verpflegung — the monthly per-diem + km engine.

Run: python3 tools/test_spesen_verpflegung.py   (exit 0 = pass). No network, no DB.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spesen import verpflegung, config

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


def day(fr=0, mi=0, na=0, frd=None, mid=None, nad=None):
    return {"fr_claimed": fr, "fr_deckung": frd, "mi_claimed": mi, "mi_deckung": mid,
            "na_claimed": na, "na_deckung": nad}


# --- meal counts × config rate ----------------------------------------------
rows = [day(mi=1, mid="VISA"), day(mi=1, mid="KS"), day(mi=1, mid="Bar"),
        day(fr=1, frd="KS"), day(na=1, nad="VISA")]
s = verpflegung.compute_verpflegung_summary(rows, None)
check("Mittag: 3 × 30 = 90.00", s["meals"]["mittag"]["total_chf"] == 90.00)
check("Frühstück: 1 × 10 = 10.00", s["meals"]["fruehstueck"]["total_chf"] == 10.00)
check("Nacht: 1 × 30 = 30.00", s["meals"]["nacht"]["total_chf"] == 30.00)
check("Verpflegung total = 130.00", s["verpflegung_total_chf"] == 130.00)
check("Deckung Mittag: VISA1/Bar1/KS1",
      s["meals"]["mittag"]["deckung"] == {"VISA": 1, "Bar": 1, "KS": 1})

# --- rates come from the tariff list, not hardcoded -------------------------
custom = [{"code": "mittagessen_kunde", "label": "M", "rate_chf": 99.0, "unit": "pauschale", "is_placeholder": False},
          {"code": "fruehstueck_vor_8", "label": "F", "rate_chf": 10.0, "unit": "pauschale", "is_placeholder": False},
          {"code": "abendessen_kunde", "label": "N", "rate_chf": 30.0, "unit": "pauschale", "is_placeholder": False},
          {"code": "auto_km", "label": "km", "rate_chf": 0.70, "unit": "pro_km", "is_placeholder": False}]
s2 = verpflegung.compute_verpflegung_summary([day(mi=1, mid="VISA")], None, tariffs=custom)
check("Config-Rate-Sourcing: Mittag folgt Tarifliste (99.00)", s2["meals"]["mittag"]["total_chf"] == 99.00)

# --- placeholder meal poisons only when claimed -----------------------------
ph = [{"code": "mittagessen_kunde", "label": "M", "rate_chf": None, "unit": "pauschale", "is_placeholder": True},
      {"code": "fruehstueck_vor_8", "label": "F", "rate_chf": 10.0, "unit": "pauschale", "is_placeholder": False},
      {"code": "abendessen_kunde", "label": "N", "rate_chf": 30.0, "unit": "pauschale", "is_placeholder": False},
      {"code": "auto_km", "label": "km", "rate_chf": 0.70, "unit": "pro_km", "is_placeholder": False}]
s3 = verpflegung.compute_verpflegung_summary([day(mi=1, mid="VISA"), day(fr=1, frd="KS")], None, tariffs=ph)
check("Platzhalter-Mittag claimed -> total None", s3["meals"]["mittag"]["total_chf"] is None)
check("Platzhalter poisons Verpflegung total -> None", s3["verpflegung_total_chf"] is None)
# same placeholder but NOT claimed -> no poison
s3b = verpflegung.compute_verpflegung_summary([day(fr=1, frd="KS")], None, tariffs=ph)
check("Platzhalter-Mittag NICHT claimed -> total ok (10.00)", s3b["verpflegung_total_chf"] == 10.00)

# --- kilometer: total, 5/7 firma, entschädigung -----------------------------
km = verpflegung.compute_verpflegung_summary([], {"km_start": 58900, "km_end": 59300})
check("Km Total = 400", km["km"]["total"] == 400)
check("Km Firma = 400*5/7 ≈ 286", km["km"]["firma"] == 286)
check("Km Entschädigung = 286*0.70 = 200.20", km["km"]["entschaedigung_chf"] == 200.20)
check("Km firma_is_override False", km["km"]["firma_is_override"] is False)

# --- km override ------------------------------------------------------------
kmo = verpflegung.compute_verpflegung_summary([], {"km_start": 0, "km_end": 400, "km_firma_override": 300})
check("Km Override 300 -> Entschädigung 210.00", kmo["km"]["entschaedigung_chf"] == 210.00)
check("Km firma_is_override True", kmo["km"]["firma_is_override"] is True)

# --- no km entered -> 0, not None -------------------------------------------
kmn = verpflegung.compute_verpflegung_summary([day(mi=1, mid="VISA")], None)
check("Kein km -> Entschädigung 0.0", kmn["km"]["entschaedigung_chf"] == 0.0)
check("Kein km -> total None", kmn["km"]["total"] is None)
check("Gesamttotal = Verpflegung + 0 = 30.00", kmn["gesamttotal_chf"] == 30.00)

# --- negative odometer guarded ----------------------------------------------
kmneg = verpflegung.compute_verpflegung_summary([], {"km_start": 500, "km_end": 100})
check("Km end<start -> total None", kmneg["km"]["total"] is None)
check("Km end<start -> Entschädigung 0.0", kmneg["km"]["entschaedigung_chf"] == 0.0)

# --- gesamttotal None when a claimed meal is placeholder --------------------
check("Gesamttotal None wenn Platzhalter claimed", s3["gesamttotal_chf"] is None)

# --- real config rates match config -----------------------------------------
mconf = next(t for t in config.PAUSCHALTARIFE if t["code"] == "mittagessen_kunde")
check("Engine nutzt echte Config-Rate (Mittag)",
      s["meals"]["mittag"]["rate_chf"] == mconf["rate_chf"])


if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (verpflegung)")
sys.exit(0)
