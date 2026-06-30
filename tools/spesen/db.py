"""db.py — SQLite persistence for KnowSpesen.

One file DB (SPESEN_DB_PATH), four tables: knowbodies, pauschaltarife, belege,
monatsabschluesse. All access goes through get_conn() which always enables foreign
keys. init_db() is idempotent (CREATE IF NOT EXISTS) and seed_pauschalen() re-syncs
the rate table from config.py on startup, so deploying new known rates needs no
manual SQL.

Money is stored as REAL (CHF) for MVP readability. If the accountant ever needs
bit-exact reconciliation, switch betrag_* to INTEGER Rappen — flagged in the plan.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:  # local CLI runs: load .env so SPESEN_DB_PATH/etc. resolve. No-op in prod (systemd injects env).
    from pathlib import Path as _P
    _envf = _P(__file__).resolve().parent.parent.parent / ".env"
    if _envf.exists():
        for _line in _envf.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
except Exception:
    pass

# Import config robustly whether loaded as a package (api.py: `import spesen.db`)
# or run directly as a script (`python3 tools/spesen/db.py`).
try:
    from . import config  # type: ignore
except ImportError:  # pragma: no cover - direct-script run: tools/spesen is sys.path[0]
    import config  # type: ignore

TZ = ZoneInfo("Europe/Zurich")

DEFAULT_DB_PATH = "/srv/knowspesen/data/knowspesen.db"


def db_path() -> str:
    return os.environ.get("SPESEN_DB_PATH", DEFAULT_DB_PATH)


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    """Open a connection with row access + foreign keys on. Caller closes."""
    path = db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowbodies (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  email        TEXT UNIQUE,
  login_token  TEXT UNIQUE,
  active       INTEGER NOT NULL DEFAULT 1,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pauschaltarife (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  code           TEXT UNIQUE NOT NULL,
  label          TEXT NOT NULL,
  rate_chf       REAL,
  unit           TEXT NOT NULL DEFAULT 'pauschale',
  is_placeholder INTEGER NOT NULL DEFAULT 0,
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monatsabschluesse (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  knowbody_id   INTEGER NOT NULL REFERENCES knowbodies(id),
  jahr_monat    TEXT NOT NULL,
  summe_chf     REAL NOT NULL DEFAULT 0,
  summe_weiterverrechenbar_chf REAL NOT NULL DEFAULT 0,
  anzahl_belege INTEGER NOT NULL DEFAULT 0,
  pdf_pfad      TEXT,
  xlsx_pfad     TEXT,
  zip_pfad      TEXT,
  geschlossen_am TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(knowbody_id, jahr_monat)
);

CREATE TABLE IF NOT EXISTS belege (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  knowbody_id     INTEGER NOT NULL REFERENCES knowbodies(id),
  art             TEXT NOT NULL DEFAULT 'beleg' CHECK(art IN ('beleg','pauschale')),
  haendler        TEXT,
  beleg_datum     TEXT,
  betrag_original REAL,
  waehrung        TEXT NOT NULL DEFAULT 'CHF',
  wechselkurs     REAL,
  kurs_quelle     TEXT,
  betrag_chf      REAL NOT NULL,
  kategorie       TEXT,
  unterkategorie  TEXT,
  zahlungsart     TEXT,
  projekt         TEXT,
  weiterverrechenbar INTEGER NOT NULL DEFAULT 0,
  pauschale_code  TEXT,
  ist_kaffeekasse INTEGER NOT NULL DEFAULT 0,
  bild_pfad       TEXT,
  ocr_confidence  REAL,
  notiz           TEXT,
  monatsabschluss_id INTEGER REFERENCES monatsabschluesse(id),
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_belege_kb_month ON belege(knowbody_id, beleg_datum);
CREATE INDEX IF NOT EXISTS idx_belege_close ON belege(monatsabschluss_id);

CREATE TABLE IF NOT EXISTS feedback (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  knowbody_id INTEGER REFERENCES knowbodies(id),
  name        TEXT,
  text        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open',
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);

CREATE TABLE IF NOT EXISTS app_meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);
"""


def init_db() -> None:
    """Create all tables/indexes if missing, then sync the rate table from config."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
        seed_pauschalen(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------

def seed_pauschalen(conn: sqlite3.Connection | None = None) -> None:
    """Upsert every tariff from config.PAUSCHALTARIFE. Idempotent: updates label/
    rate/unit/placeholder on the existing code, inserts new codes. This is how a
    new known rate ships — edit config.py, restart, done."""
    own = conn is None
    conn = conn or get_conn()
    try:
        for t in config.PAUSCHALTARIFE:
            conn.execute(
                """
                INSERT INTO pauschaltarife (code, label, rate_chf, unit, is_placeholder, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                  label=excluded.label, rate_chf=excluded.rate_chf,
                  unit=excluded.unit, is_placeholder=excluded.is_placeholder,
                  updated_at=excluded.updated_at
                """,
                (t["code"], t["label"], t["rate_chf"], t["unit"],
                 1 if t["is_placeholder"] else 0, now_iso()),
            )
        conn.commit()
    finally:
        if own:
            conn.close()


def list_pauschalen() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT code, label, rate_chf, unit, is_placeholder FROM pauschaltarife ORDER BY is_placeholder, label"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# KnowBodies
# ---------------------------------------------------------------------------

def upsert_knowbody(name: str, email: str = "", login_token: str = "", active: int = 1) -> int:
    """Insert (or update by email) a KnowBody. Returns the row id."""
    conn = get_conn()
    try:
        existing = None
        if email:
            existing = conn.execute("SELECT id FROM knowbodies WHERE email=?", (email,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE knowbodies SET name=?, login_token=?, active=? WHERE id=?",
                (name, login_token or None, active, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        cur = conn.execute(
            "INSERT INTO knowbodies (name, email, login_token, active) VALUES (?, ?, ?, ?)",
            (name, email or None, login_token or None, active),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_knowbody(kb_id: int) -> dict | None:
    conn = get_conn()
    try:
        return row_to_dict(conn.execute("SELECT * FROM knowbodies WHERE id=?", (kb_id,)).fetchone())
    finally:
        conn.close()


def get_knowbody_by_token(token: str) -> dict | None:
    if not token:
        return None
    conn = get_conn()
    try:
        return row_to_dict(conn.execute(
            "SELECT * FROM knowbodies WHERE login_token=? AND active=1", (token,)).fetchone())
    finally:
        conn.close()


def list_knowbodies(active_only: bool = True) -> list[dict]:
    conn = get_conn()
    try:
        q = "SELECT * FROM knowbodies"
        if active_only:
            q += " WHERE active=1"
        q += " ORDER BY name"
        return [dict(r) for r in conn.execute(q).fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Belege
# ---------------------------------------------------------------------------

_BELEG_COLS = (
    "knowbody_id", "art", "haendler", "beleg_datum", "betrag_original", "waehrung",
    "wechselkurs", "kurs_quelle", "betrag_chf", "kategorie", "unterkategorie",
    "zahlungsart", "projekt", "weiterverrechenbar", "pauschale_code",
    "ist_kaffeekasse", "bild_pfad", "ocr_confidence", "notiz",
)


def insert_beleg(fields: dict) -> int:
    """Insert one beleg. Only whitelisted columns are taken from `fields`."""
    cols = [c for c in _BELEG_COLS if c in fields]
    placeholders = ", ".join("?" for _ in cols)
    vals = [fields[c] for c in cols]
    conn = get_conn()
    try:
        cur = conn.execute(
            f"INSERT INTO belege ({', '.join(cols)}) VALUES ({placeholders})", vals)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_beleg(beleg_id: int) -> dict | None:
    conn = get_conn()
    try:
        return row_to_dict(conn.execute("SELECT * FROM belege WHERE id=?", (beleg_id,)).fetchone())
    finally:
        conn.close()


def list_belege(knowbody_id: int, month: str | None = None) -> list[dict]:
    """All belege for a KnowBody, optionally filtered to a 'YYYY-MM' month bucket
    (by beleg_datum). Newest first."""
    conn = get_conn()
    try:
        if month:
            rows = conn.execute(
                "SELECT * FROM belege WHERE knowbody_id=? AND substr(beleg_datum,1,7)=? "
                "ORDER BY beleg_datum DESC, id DESC",
                (knowbody_id, month),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM belege WHERE knowbody_id=? ORDER BY beleg_datum DESC, id DESC",
                (knowbody_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_beleg(beleg_id: int, fields: dict) -> bool:
    """Update whitelisted columns. Refuses if the beleg is locked (month closed)."""
    cols = [c for c in _BELEG_COLS if c in fields and c != "knowbody_id"]
    if not cols:
        return False
    conn = get_conn()
    try:
        locked = conn.execute(
            "SELECT monatsabschluss_id FROM belege WHERE id=?", (beleg_id,)).fetchone()
        if locked is None or locked["monatsabschluss_id"] is not None:
            return False
        sets = ", ".join(f"{c}=?" for c in cols) + ", updated_at=?"
        vals = [fields[c] for c in cols] + [now_iso(), beleg_id]
        cur = conn.execute(f"UPDATE belege SET {sets} WHERE id=? AND monatsabschluss_id IS NULL", vals)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_beleg(beleg_id: int) -> bool:
    """Delete a beleg unless its month is already closed (locked)."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM belege WHERE id=? AND monatsabschluss_id IS NULL", (beleg_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Monatsabschluss
# ---------------------------------------------------------------------------

def get_close(knowbody_id: int, jahr_monat: str) -> dict | None:
    conn = get_conn()
    try:
        return row_to_dict(conn.execute(
            "SELECT * FROM monatsabschluesse WHERE knowbody_id=? AND jahr_monat=?",
            (knowbody_id, jahr_monat)).fetchone())
    finally:
        conn.close()


def belege_for_month(knowbody_id: int, jahr_monat: str, include_kaffeekasse: bool = False) -> list[dict]:
    """Belege that go INTO the monthly report: the month bucket, oldest first,
    Kaffeekasse excluded by default. Placeholder-pauschale belege (no CHF amount)
    are also excluded so they never produce a wrong total."""
    conn = get_conn()
    try:
        q = ("SELECT * FROM belege WHERE knowbody_id=? AND substr(beleg_datum,1,7)=? ")
        params = [knowbody_id, jahr_monat]
        if not include_kaffeekasse:
            q += "AND ist_kaffeekasse=0 "
        q += "ORDER BY beleg_datum ASC, id ASC"
        return [dict(r) for r in conn.execute(q, params).fetchall()]
    finally:
        conn.close()


def finalize_close(knowbody_id: int, jahr_monat: str, *, summe_chf: float,
                   summe_weiter_chf: float, anzahl: int, beleg_ids: list[int],
                   pdf_pfad: str = "", xlsx_pfad: str = "", zip_pfad: str = "") -> int:
    """Atomically: upsert the monatsabschluss row, then lock every included beleg
    by stamping its monatsabschluss_id. Re-closing a month overwrites artifacts and
    re-locks the current set. Returns the monatsabschluss id."""
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        existing = conn.execute(
            "SELECT id FROM monatsabschluesse WHERE knowbody_id=? AND jahr_monat=?",
            (knowbody_id, jahr_monat)).fetchone()
        if existing:
            ma_id = existing["id"]
            conn.execute(
                "UPDATE monatsabschluesse SET summe_chf=?, summe_weiterverrechenbar_chf=?, "
                "anzahl_belege=?, pdf_pfad=?, xlsx_pfad=?, zip_pfad=?, geschlossen_am=? WHERE id=?",
                (summe_chf, summe_weiter_chf, anzahl, pdf_pfad, xlsx_pfad, zip_pfad, now_iso(), ma_id),
            )
            # release any previously-locked belege for this month before re-locking the current set
            conn.execute("UPDATE belege SET monatsabschluss_id=NULL WHERE monatsabschluss_id=?", (ma_id,))
        else:
            cur = conn.execute(
                "INSERT INTO monatsabschluesse (knowbody_id, jahr_monat, summe_chf, "
                "summe_weiterverrechenbar_chf, anzahl_belege, pdf_pfad, xlsx_pfad, zip_pfad) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (knowbody_id, jahr_monat, summe_chf, summe_weiter_chf, anzahl, pdf_pfad, xlsx_pfad, zip_pfad),
            )
            ma_id = cur.lastrowid
        for bid in beleg_ids:
            conn.execute(
                "UPDATE belege SET monatsabschluss_id=?, updated_at=? WHERE id=? AND knowbody_id=?",
                (ma_id, now_iso(), bid, knowbody_id))
        conn.commit()
        return ma_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def open_months(jahr_monat: str) -> list[dict]:
    """KnowBodies who have NOT closed `jahr_monat` (for the reminder cron).
    Includes those with belege in the month but no close, and (optionally) all
    active members. Here: active members without a close row for the month."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT k.id, k.name, k.email
            FROM knowbodies k
            WHERE k.active=1 AND NOT EXISTS (
              SELECT 1 FROM monatsabschluesse m
              WHERE m.knowbody_id=k.id AND m.jahr_monat=?
            )
            ORDER BY k.name
            """,
            (jahr_monat,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def reopen_close(knowbody_id: int, jahr_monat: str) -> bool:
    """Undo a month close: unlock every beleg of that close and delete the
    monatsabschluss row, so the month becomes editable again. The PDF/Excel/ZIP on
    disk are left as-is (regenerated on the next close). Returns False if no close."""
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        row = conn.execute(
            "SELECT id FROM monatsabschluesse WHERE knowbody_id=? AND jahr_monat=?",
            (knowbody_id, jahr_monat)).fetchone()
        if not row:
            conn.rollback()
            return False
        ma_id = row["id"]
        conn.execute(
            "UPDATE belege SET monatsabschluss_id=NULL, updated_at=? WHERE monatsabschluss_id=?",
            (now_iso(), ma_id))
        conn.execute("DELETE FROM monatsabschluesse WHERE id=?", (ma_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Feedback ("Nachricht an den Entwickler") + tiny key/value meta store
# ---------------------------------------------------------------------------

def add_feedback(knowbody_id, name: str, text: str) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO feedback (knowbody_id, name, text) VALUES (?, ?, ?)",
            (knowbody_id, name or None, text))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def open_feedback() -> list[dict]:
    """All unresolved feedback, oldest first."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM feedback WHERE status='open' ORDER BY created_at ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def resolve_feedback(feedback_id: int) -> bool:
    conn = get_conn()
    try:
        cur = conn.execute(
            "UPDATE feedback SET status='resolved', resolved_at=? WHERE id=? AND status='open'",
            (now_iso(), feedback_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def meta_get(key: str) -> str | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT value FROM app_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def meta_set(key: str, value: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":  # `python3 tools/spesen/db.py` → init + print schema summary
    import sys
    if not os.environ.get("SPESEN_DB_PATH"):
        os.environ["SPESEN_DB_PATH"] = str(Path(__file__).resolve().parent.parent.parent / ".tmp" / "knowspesen.db")
    init_db()
    print(f"[knowspesen] DB initialised at {db_path()}")
    print(f"[knowspesen] pauschaltarife seeded: {len(list_pauschalen())} rows")
    for t in list_pauschalen():
        flag = " (Tarif folgt)" if t["is_placeholder"] else ""
        rate = "—" if t["rate_chf"] is None else f"CHF {t['rate_chf']:.2f}"
        print(f"  - {t['label']}: {rate}{flag}")
    sys.exit(0)
