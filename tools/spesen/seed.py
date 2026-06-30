"""seed.py — demo data for KnowSpesen so a demo looks full + flowing.

seed_demo() (called by POST /api/spesen/setup-db {"seed_demo": true}, or directly):
  - upserts Markus + 2 test KnowBodies with deterministic magic-link tokens
  - if Markus has no belege this month, inserts a varied sample set (CHF, EUR,
    weiterverrechenbar, a Kaffeekasse item, a Pauschale)

Real KnowBody names + emails replace these before go-live (see workflows/knowspesen.md).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from . import db, pauschalen
except ImportError:  # pragma: no cover
    import db, pauschalen

TZ = ZoneInfo("Europe/Zurich")

DEMO_MEMBERS = [
    ("Markus Schacher", "markus.schacher@knowgravity.com", "demo-markus"),
    ("Anna Beispiel", "anna@knowgravity.com", "demo-anna"),
    ("Luca Muster", "luca@knowgravity.com", "demo-luca"),
]


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
    print(json.dumps(seed_demo(), ensure_ascii=False, indent=2))
