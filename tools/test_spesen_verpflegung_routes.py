#!/usr/bin/env python3
"""Offline route tests for the KnowSpesen Verpflegungs-/Kilometerblatt grid.

Run: python3 tools/test_spesen_verpflegung_routes.py   (exit 0 = pass). No network.
Exercises the GET scaffold, per-day PATCH + recomputed summary, km PATCH, deckung
enum validation, owner-scoping, config exposure, and the 409-after-close lock.
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

os.environ["SPESEN_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="spdb_"), "ks.db")
os.environ["SPESEN_RECEIPT_DIR"] = tempfile.mkdtemp(prefix="sprcpt_")
os.environ["SPESEN_OUTPUT_DIR"] = tempfile.mkdtemp(prefix="spout_")

import api  # noqa: E402
from spesen import db  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


db.init_db()
db.upsert_knowbody("Markus Schacher", "markus@knowgravity.com", "TOK")
db.upsert_knowbody("Reto Schreppers", "reto@knowgravity.com", "TOK2")
c = api.app.test_client()
Q = "?k=TOK&month=2026-03"
MONTH = "2026-03"
HDR = {"X-Spesen-Token": "TOK"}          # auth for PATCHes without a query string
HDR2 = {"X-Spesen-Token": "TOK2"}

# --- auth + config exposure --------------------------------------------------
check("verpflegung ohne Token -> 401", c.get("/api/spesen/verpflegung").status_code == 401)
cfg = c.get("/api/spesen/config?k=TOK").get_json()
check("config: verpflegung meals present", set(cfg["verpflegung"]["meals"]) == {"fruehstueck", "mittag", "nacht"})
check("config: mittag rate 30", cfg["verpflegung"]["meals"]["mittag"]["rate_chf"] == 30.0)
check("config: deckung options", cfg["verpflegung"]["deckung_options"] == ["VISA", "Bar", "KS"])
check("config: km rate 0.70", cfg["km"]["rate_chf"] == 0.70)

# --- GET scaffold: one entry per calendar day (März = 31) --------------------
r = c.get("/api/spesen/verpflegung" + Q)
gj = r.get_json()
check("scaffold: 31 Tage", len(gj["days"]) == 31)
check("scaffold: erster Tag 2026-03-01", gj["days"][0]["datum"] == "2026-03-01")
check("scaffold: Wochentag-Label da", gj["days"][0]["weekday"] in ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"))
check("scaffold: nicht geschlossen", gj["closed"] is False)

# --- PATCH a day: claim Mittag + returns recomputed summary -----------------
r = c.patch("/api/spesen/verpflegung/2026-03-04", headers=HDR, json={"mi_claimed": True, "mi_deckung": "VISA",
                                                        "arb_vormittag": True, "bemerkung": "Cudos"})
pj = r.get_json()
check("PATCH day ok", r.status_code == 200 and pj["ok"])
check("PATCH day: summary Mittag count 1", pj["summary"]["meals"]["mittag"]["count"] == 1)
check("PATCH day: summary Mittag total 30", pj["summary"]["meals"]["mittag"]["total_chf"] == 30.0)
check("PATCH day: bemerkung gespeichert", pj["day"]["bemerkung"] == "Cudos")

# two more lunches
c.patch("/api/spesen/verpflegung/2026-03-05", headers=HDR, json={"mi_claimed": True, "mi_deckung": "KS"})
r = c.patch("/api/spesen/verpflegung/2026-03-09", headers=HDR, json={"mi_claimed": True, "mi_deckung": "Bar",
                                                        "na_claimed": True, "na_deckung": "VISA", "arb_spaet": True})
sj = r.get_json()["summary"]
check("summary: 3 Mittag = 90", sj["meals"]["mittag"]["total_chf"] == 90.0)
check("summary: 1 Nacht = 30", sj["meals"]["nacht"]["total_chf"] == 30.0)
check("summary: Verpflegung total 120", sj["verpflegung_total_chf"] == 120.0)

# --- invalid deckung enum rejected ------------------------------------------
r = c.patch("/api/spesen/verpflegung/2026-03-10", headers=HDR, json={"mi_claimed": True, "mi_deckung": "Twint"})
check("Deckung ungültig -> 400", r.status_code == 400)

# --- invalid date -----------------------------------------------------------
check("Datum ungültig -> 400", c.patch("/api/spesen/verpflegung/2026-3-4", headers=HDR, json={"mi_claimed": True}).status_code == 400)

# --- km PATCH: 58900->59300 => 400 total, 286 firma, 200.20 ------------------
r = c.patch("/api/spesen/kilometer" + Q, json={"km_start": 58900, "km_end": 59300})
kj = r.get_json()
check("km PATCH ok", r.status_code == 200 and kj["ok"])
check("km: total 400", kj["summary"]["km"]["total"] == 400)
check("km: firma 286", kj["summary"]["km"]["firma"] == 286)
check("km: Entschädigung 200.20", kj["summary"]["km"]["entschaedigung_chf"] == 200.20)
check("km: Gesamttotal 320.20", kj["summary"]["gesamttotal_chf"] == 320.20)

# --- owner-scoping: other member does not see Markus's data -----------------
og = c.get("/api/spesen/verpflegung?k=TOK2&month=2026-03").get_json()
check("owner-scope: Reto sieht 0 Mittag", og["summary"]["meals"]["mittag"]["count"] == 0)
check("owner-scope: Reto km leer", og["kilometer"]["km_start"] is None)

# --- 409 after close --------------------------------------------------------
ma = db.finalize_close(db.get_knowbody_by_token("TOK")["id"], MONTH,
                       summe_chf=0, summe_weiter_chf=0, anzahl=0, beleg_ids=[])
r = c.patch("/api/spesen/verpflegung/2026-03-04", headers=HDR, json={"mi_claimed": False})
check("PATCH day nach Abschluss -> 409", r.status_code == 409)
r = c.patch("/api/spesen/kilometer" + Q, json={"km_end": 60000})
check("PATCH km nach Abschluss -> 409", r.status_code == 409)
check("GET zeigt closed=True", c.get("/api/spesen/verpflegung" + Q).get_json()["closed"] is True)


if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (verpflegung routes)")
sys.exit(0)
