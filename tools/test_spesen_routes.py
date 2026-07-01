#!/usr/bin/env python3
"""Offline route tests for KnowSpesen via Flask's test client.

Run: python3 tools/test_spesen_routes.py   (exit 0 = pass). OCR + FX are
monkeypatched, so this never hits the network or spends API credits. Exercises
auth, config, OCR prefill, beleg create (CHF / FX / pauschale / placeholder),
listing + totals, month-close and ZIP download end-to-end through the real app.
"""
import io
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # tools/  (spesen package)
sys.path.insert(0, _ROOT)   # repo root (api.py)

os.environ["SPESEN_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="spdb_"), "ks.db")
os.environ["SPESEN_RECEIPT_DIR"] = tempfile.mkdtemp(prefix="sprcpt_")
os.environ["SPESEN_OUTPUT_DIR"] = tempfile.mkdtemp(prefix="spout_")
os.environ["SPESEN_ACCOUNTANT_EMAIL"] = "buchhaltung@gubser-kalt.ch"

import api  # noqa: E402
from spesen import db, currency, ocr, config  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- fixtures: no network, no credits ---------------------------------------
currency._fetch_json = lambda url: {"base": "EUR", "date": "2026-06-20", "rates": {"CHF": 0.95}}
ocr.extract_receipt = lambda content, mt, **k: {
    "ok": True, "haendler": "Restaurant Hiltl", "datum": "2026-06-10",
    "betrag": 87.50, "waehrung": "CHF", "confidence": 0.92, "error": None}

db.init_db()
db.upsert_knowbody("Markus Schacher", "markus@knowgravity.com", "TOK")
c = api.app.test_client()
Q = "?k=TOK"

# --- auth --------------------------------------------------------------------
check("whoami ohne Token -> 401", c.get("/api/spesen/whoami").status_code == 401)
r = c.get("/api/spesen/whoami" + Q)
check("whoami mit Token -> 200 + Name", r.status_code == 200 and r.get_json()["name"] == "Markus Schacher")

# --- config ------------------------------------------------------------------
r = c.get("/api/spesen/config" + Q)
cfg = r.get_json()
check("config: Kategorien", "Mahlzeit" in cfg["categories"])
check("config: Pauschalen geladen", any(p["code"] == "mittagessen_kunde" for p in cfg["pauschalen"]))
check("config: accountant email", cfg["accountant_email"] == "buchhaltung@gubser-kalt.ch")

# --- OCR prefill (mocked) ----------------------------------------------------
r = c.post("/api/spesen/ocr" + Q,
           data={"beleg": (io.BytesIO(b"\xff\xd8\xff" + b"x" * 40), "r.jpg")},
           content_type="multipart/form-data")
oj = r.get_json()
check("OCR -> Händler vorausgefüllt", oj.get("ok") and oj.get("haendler") == "Restaurant Hiltl")

# --- create CHF beleg --------------------------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "beleg", "datum": "2026-06-10", "kategorie": "Mahlzeit",
    "betrag_original": "87.50", "waehrung": "CHF", "zahlungsart": "Firmenkreditkarte"})
bj = r.get_json()
check("CHF-Beleg gespeichert", r.status_code == 200 and bj["ok"] and bj["betrag_chf"] == 87.50)
check("CHF-Beleg nicht Kaffeekasse", bj["ist_kaffeekasse"] is False)

# --- create EUR beleg (FX mock) weiterverrechenbar ---------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "beleg", "datum": "2026-06-20", "kategorie": "Unterkunft",
    "betrag_original": "142", "waehrung": "EUR", "zahlungsart": "Privat-Kreditkarte",
    "projekt": "Kunde Berlin", "weiterverrechenbar": "true"})
bj = r.get_json()
check("EUR-Beleg -> 134.90 CHF", bj["ok"] and bj["betrag_chf"] == round(142 * 0.95, 2))

# --- pauschale (30, < 50 -> Kaffeekasse) -------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "pauschale", "datum": "2026-06-12", "kategorie": "Mahlzeit",
    "pauschale_code": "mittagessen_kunde", "zahlungsart": "Privat-Cash"})
bj = r.get_json()
check("Pauschale Mittagessen = 30", bj["ok"] and bj["betrag_chf"] == 30.0)
check("Pauschale < 50 -> Kaffeekasse + Warnung", bj["ist_kaffeekasse"] is True and bool(bj["warnung"]))

# --- placeholder pauschale rejected -----------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "pauschale", "datum": "2026-06-12", "kategorie": "Transport",
    "pauschale_code": "auto_km", "zahlungsart": "Privat-Cash"})
check("Platzhalter-Pauschale -> 422", r.status_code == 422)

# --- validation error --------------------------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={"art": "beleg", "datum": "", "kategorie": ""})
check("fehlende Pflichtfelder -> 400", r.status_code == 400)

# --- listing + totals --------------------------------------------------------
r = c.get("/api/spesen/belege" + Q + "&month=2026-06")
lj = r.get_json()
check("Liste: total 222.40 (Kaffeekasse raus)", lj["total_chf"] == 222.40)
check("Liste: anzahl 2", lj["anzahl"] == 2)
check("Liste: weiterverrechenbar 134.90", lj["weiter_chf"] == 134.90)
check("Liste: kaffeekasse 30.00", lj["kaffeekasse_chf"] == 30.00)
check("Liste: noch nicht geschlossen", lj["closed"] is False)

# --- comma-amount beleg (the <1 CHF bug) -------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "beleg", "datum": "2026-06-14", "kategorie": "Material",
    "betrag_original": "0,50", "waehrung": "CHF", "zahlungsart": "Privat-Cash"})
check("Komma-Betrag 0,50 -> 200 + 0.5 CHF", r.status_code == 200 and r.get_json()["betrag_chf"] == 0.5)

# --- image endpoint (owner-scoped) ------------------------------------------
r = c.post("/api/spesen/beleg" + Q, data={
    "art": "beleg", "datum": "2026-06-16", "kategorie": "Transport",
    "betrag_original": "80", "waehrung": "CHF", "zahlungsart": "Firmenkreditkarte",
    "beleg": (io.BytesIO(b"\xff\xd8\xff" + b"x" * 60), "r.jpg")}, content_type="multipart/form-data")
img_id = r.get_json()["beleg_id"]
r = c.get(f"/api/spesen/beleg/{img_id}/image" + Q)
check("Bild-Endpoint 200 + jpeg", r.status_code == 200 and r.data[:2] == b"\xff\xd8")
check("Bild-Endpoint ohne Token -> 401", c.get(f"/api/spesen/beleg/{img_id}/image").status_code == 401)

# --- full-fidelity PATCH: change currency (EUR) + notiz + kaffee override -----
r = c.patch(f"/api/spesen/beleg/{img_id}" + Q,
            json={"betrag_original": "100", "waehrung": "EUR", "notiz": "Taxi Berlin",
                  "kategorie": "Transport", "ist_kaffeekasse": True})
check("PATCH Währungswechsel ok", r.get_json().get("ok") is True)
_b = db.get_beleg(img_id)
check("PATCH: EUR -> 95.00 CHF (FX)", _b["betrag_chf"] == 95.0 and _b["waehrung"] == "EUR")
check("PATCH: notiz gesetzt", _b["notiz"] == "Taxi Berlin")
check("PATCH: Kaffeekasse-Override greift (trotz 95 CHF)", _b["ist_kaffeekasse"] == 1)

# --- edit a Kaffeekasse beleg ------------------------------------------------
kaffee_id = next(b["id"] for b in lj["belege"] if b["ist_kaffeekasse"])
r = c.patch(f"/api/spesen/beleg/{kaffee_id}" + Q, json={"notiz": "Kaffee mit Kunde"})
check("PATCH offener Beleg ok", r.get_json().get("ok") is True)

# --- shared Kaffeekasse overview (spans KnowBodies) --------------------------
r = c.get("/api/spesen/kaffeekasse" + Q + "&month=2026-06")
ov = r.get_json()
check("Kaffeekasse-Overview 200 + total > 0", r.status_code == 200 and ov["total_chf"] > 0)
check("Kaffeekasse-Overview: Markus enthalten",
      any(p["name"] == "Markus Schacher" for p in ov["per_person"]))

# --- health endpoint ---------------------------------------------------------
r = c.get("/api/spesen/health")
hj = r.get_json()
check("health 200 + status ok", r.status_code == 200 and hj["status"] == "ok")
check("health checks db + receipts", hj["checks"]["db"] == "ok" and hj["checks"]["receipts_writable"] == "ok")

# --- month-close needs the typed Kontroll-Bestätigung ------------------------
r = c.post("/api/spesen/month-close" + Q, json={"month": "2026-06"})
check("month-close ohne Bestätigung -> 400", r.status_code == 400 and r.get_json().get("need_attest"))
r = c.post("/api/spesen/month-close" + Q, json={"month": "2026-06", "bestaetigung_text": "irgendwas"})
check("month-close falscher Text -> 400", r.status_code == 400)

# correct text (case/space tolerant)
_typed = "  " + config.ATTESTATION_TEXT.upper() + "  "
r = c.post("/api/spesen/month-close" + Q, json={"month": "2026-06", "bestaetigung_text": _typed})
mj = r.get_json()
check("month-close mit Bestätigung ok", r.status_code == 200 and mj["ok"])
# active total unchanged: the 0,50 is Kaffeekasse and the 95-CHF beleg got a Kaffeekasse override
check("month-close total 222.40 (Kaffeekasse ausgeschlossen)", mj["total_chf"] == 222.40)
check("Bestätigung in Buchhaltungs-Mail", "wahrheitsgetreu" in mj["email"]["body"].lower())
_close = db.get_close(1, "2026-06")
check("Bestätigung in DB (von + am)", bool(_close["bestaetigung_text"]) and _close["bestaetigt_von"] == "Markus Schacher")
check("month-close Email-Entwurf vorhanden", mj["email"]["subject"].startswith("Spesenabrechnung"))
check("month-close download-link", mj["download"].startswith("/api/spesen/download"))

# --- download ZIP ------------------------------------------------------------
r = c.get("/api/spesen/download" + Q + "&month=2026-06")
check("download -> ZIP bytes", r.status_code == 200 and r.data[:2] == b"PK")
check("download -> zip mimetype", "zip" in r.headers.get("Content-Type", ""))

# --- after close: locked + delete refused -----------------------------------
r = c.get("/api/spesen/belege" + Q + "&month=2026-06")
check("nach Abschluss: closed=True", r.get_json()["closed"] is True)
active_id = next(b["id"] for b in r.get_json()["belege"] if not b["ist_kaffeekasse"])
r = c.delete(f"/api/spesen/beleg/{active_id}" + Q)
check("gesperrter Beleg löschen -> 409", r.status_code == 409)

# --- month reopen unlocks ---
r = c.post("/api/spesen/month-reopen" + Q, json={"month": "2026-06"})
check("month-reopen ok", r.get_json().get("ok") is True)
r = c.get("/api/spesen/belege" + Q + "&month=2026-06")
check("nach reopen: closed=False", r.get_json()["closed"] is False)
r = c.delete(f"/api/spesen/beleg/{active_id}" + Q)
check("nach reopen: löschen ok", r.get_json().get("ok") is True)

# --- feedback submit ---
r = c.post("/api/spesen/feedback" + Q, json={"text": "Galerie-Upload geht nicht"})
check("feedback gespeichert", r.get_json().get("ok") is True)
check("leeres feedback -> 400", c.post("/api/spesen/feedback" + Q, json={"text": ""}).status_code == 400)
check("feedback-list ohne Auth -> 401", c.get("/api/spesen/feedback").status_code == 401)

# --- feedback admin (cockpit session) ---
c.post("/api/cockpit/login", json={"password": "Operations2026$"})
r = c.get("/api/spesen/feedback")
check("admin feedback-list ok", r.status_code == 200 and len(r.get_json()["open"]) >= 1)
fid = r.get_json()["open"][0]["id"]
check("feedback resolve ok", c.post(f"/api/spesen/feedback/{fid}/resolve").get_json().get("ok") is True)
check("nach resolve: 0 offen", len(c.get("/api/spesen/feedback").get_json()["open"]) == 0)

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (routes)")
sys.exit(0)
