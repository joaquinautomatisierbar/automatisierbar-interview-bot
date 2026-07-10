"""seed.py — demo + real seed data for KnowSpesen.

seed_knowbodies() (go-live): upserts the 6 REAL KnowBodies (from Markus's mail of
  2026-07-10, see references/knowgravity/markus-email-2026-07-10.md) with secure
  random magic-link tokens. Idempotent — a token is generated once per person and
  preserved on re-run so already-distributed links keep working.

seed_demo() (demo only): upserts Markus + 2 fictional test KnowBodies with
  deterministic 'demo-*' tokens and, if Markus has no belege this month, a varied
  sample set (CHF, EUR, weiterverrechenbar, a Kaffeekasse item, a Pauschale).
"""

from __future__ import annotations

import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from . import db, pauschalen
except ImportError:  # pragma: no cover
    import db, pauschalen

TZ = ZoneInfo("Europe/Zurich")

# The 6 real KnowBodies (name, email) — Markus Schacher, 2026-07-10.
KNOWBODIES = [
    ("Christian Bühler", "christian.buehler@knowgravity.com"),
    ("Jonas Bucher", "jonas.bucher@knowgravity.com"),
    ("Markus Schacher", "markus.schacher@knowgravity.com"),
    ("Patrick Grässle", "patrick.graessle@knowgravity.com"),
    ("Reto Schreppers", "reto.schreppers@knowgravity.com"),
    ("Rolf Gubser", "rolf.gubser@knowgravity.com"),
]

DEMO_MEMBERS = [
    ("Markus Schacher", "markus.schacher@knowgravity.com", "demo-markus"),
    ("Anna Beispiel", "anna@knowgravity.com", "demo-anna"),
    ("Luca Muster", "luca@knowgravity.com", "demo-luca"),
]


def seed_knowbodies() -> dict:
    """Idempotently upsert the 6 real KnowBodies with secure random magic-link
    tokens. A token is generated ONCE per person and preserved on re-run, so links
    already handed out stay valid; a leftover 'demo-*' token is replaced on first
    real run. Returns the list incl. magic links for distribution."""
    db.init_db()
    existing = {kb["email"]: kb for kb in db.list_knowbodies(active_only=False) if kb.get("email")}
    out = []
    for name, email in KNOWBODIES:
        prev = existing.get(email)
        keep = bool(prev and prev.get("login_token") and not prev["login_token"].startswith("demo-"))
        tok = prev["login_token"] if keep else secrets.token_urlsafe(16)
        kid = db.upsert_knowbody(name, email, tok)
        out.append({"id": kid, "name": name, "email": email,
                    "token": tok, "login": f"/spesen?k={tok}"})
    return {"knowbodies": out, "count": len(out)}


def _kf(betrag, pausch=False):
    return 1 if pauschalen.is_kaffeekasse(betrag, ist_pauschale=pausch) else 0


def seed_demo() -> dict:
    db.init_db()
    ids = {}
    for name, email, tok in DEMO_MEMBERS:
        ids[name] = db.upsert_knowbody(name, email, tok)

    mk = ids["Markus Schacher"]
    today = datetime.now(TZ).date()
    month = today.strftime("%Y-%m")

    def day(n):
        return today.replace(day=min(n, 28)).isoformat()

    added = 0
    if not db.list_belege(mk, month):
        samples = [
            {"art": "beleg", "haendler": "Restaurant Hiltl", "beleg_datum": day(4),
             "betrag_original": 87.50, "waehrung": "CHF", "betrag_chf": 87.50,
             "kategorie": "Mahlzeit", "unterkategorie": "Geschäftsessen mit Kunden",
             "zahlungsart": "Firmenkreditkarte", "projekt": "Kunde ABC AG", "weiterverrechenbar": 1},
            {"art": "beleg", "haendler": "Hotel Adlon Berlin", "beleg_datum": day(9),
             "betrag_original": 142.00, "waehrung": "EUR", "wechselkurs": 0.95,
             "kurs_quelle": "frankfurter.dev", "betrag_chf": 134.90, "kategorie": "Unterkunft",
             "unterkategorie": "Hotel", "zahlungsart": "Privat-Kreditkarte",
             "projekt": "Kunde Berlin GmbH", "weiterverrechenbar": 1},
            {"art": "beleg", "haendler": "SBB", "beleg_datum": day(11),
             "betrag_original": 56.00, "waehrung": "CHF", "betrag_chf": 56.00,
             "kategorie": "Transport", "unterkategorie": "SBB / Bahn",
             "zahlungsart": "Firmenkreditkarte", "weiterverrechenbar": 0},
            {"art": "pauschale", "beleg_datum": day(12), "betrag_original": 30.00,
             "waehrung": "CHF", "betrag_chf": 30.00, "kategorie": "Mahlzeit",
             "unterkategorie": "Mittagessen beim Kunden", "zahlungsart": "Privat-Cash",
             "pauschale_code": "mittagessen_kunde", "weiterverrechenbar": 0},
            {"art": "beleg", "haendler": "Office World", "beleg_datum": day(15),
             "betrag_original": 12.50, "waehrung": "CHF", "betrag_chf": 12.50,
             "kategorie": "Material", "unterkategorie": "Büromaterial",
             "zahlungsart": "Privat-Cash", "weiterverrechenbar": 0},
        ]
        for s in samples:
            s["knowbody_id"] = mk
            s["ist_kaffeekasse"] = _kf(s["betrag_chf"], pausch=(s["art"] == "pauschale"))
            db.insert_beleg(s)
            added += 1

    return {
        "members": [{"name": n, "email": e, "token": t, "login": f"/spesen?k={t}"}
                    for n, e, t in DEMO_MEMBERS],
        "sample_belege_added": added,
        "month": month,
    }


if __name__ == "__main__":
    import json
    import sys
    if "--real" in sys.argv:
        print(json.dumps(seed_knowbodies(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(seed_demo(), ensure_ascii=False, indent=2))
