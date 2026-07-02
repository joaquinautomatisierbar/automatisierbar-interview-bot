"""state.py — SQLite processed-state store for the Befund-Automat.

One file DB at <data_dir>/state.db, two tables:

  processed      one row per (mail, attachment) with terminal status
                 success | failed | skipped. Doubles as the pilot metrics
                 source (doctor.py --stats reads it).
  mailbox_state  last processed UID per UIDVALIDITY (UID-based polling —
                 Outlook marks mail \\Seen first, so UNSEEN is useless).

Dedup keys:
  primary    (uidvalidity, uid, attachment_index)         — normal operation
  secondary  (message_id, attachment_sha256)              — survives state.db
             loss and UIDVALIDITY resets, so the startup rescan window can
             never re-file a PDF that was already filed.

All statuses are TERMINAL — no auto-retry. A failed mail stays unflagged,
which IS the manual-review signal for Dr. Ulrich; a silent late retry could
file a duplicate after she has already handled it by hand.
"""

from __future__ import annotations

import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from . import config
except ImportError:  # direct-script / test runs with tools/praxis_ulrich on sys.path
    import config  # type: ignore

TZ = ZoneInfo("Europe/Zurich")

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"   # non-Befund PDFs (ist_befund=false), oversize, duplicates

_SCHEMA = """
CREATE TABLE IF NOT EXISTS processed (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  uidvalidity        INTEGER NOT NULL,
  uid                INTEGER NOT NULL,
  attachment_index   INTEGER NOT NULL,
  attachment_sha256  TEXT NOT NULL,
  message_id         TEXT NOT NULL DEFAULT '',
  absender           TEXT NOT NULL DEFAULT '',
  pdf_dateiname      TEXT NOT NULL DEFAULT '',
  status             TEXT NOT NULL CHECK (status IN ('success','failed','skipped')),
  fehler             TEXT NOT NULL DEFAULT '',
  filed_filename     TEXT NOT NULL DEFAULT '',
  dokumenttitel      TEXT NOT NULL DEFAULT '',
  patientin_vorname  TEXT NOT NULL DEFAULT '',
  patientin_nachname TEXT NOT NULL DEFAULT '',
  geburtsdatum       TEXT NOT NULL DEFAULT '',
  created_at         TEXT NOT NULL,
  UNIQUE (uidvalidity, uid, attachment_index)
);
CREATE INDEX IF NOT EXISTS idx_processed_msg_sha
  ON processed (message_id, attachment_sha256);
CREATE INDEX IF NOT EXISTS idx_processed_created
  ON processed (created_at);

CREATE TABLE IF NOT EXISTS mailbox_state (
  uidvalidity  INTEGER PRIMARY KEY,
  last_uid     INTEGER NOT NULL,
  updated_at   TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def db_path() -> Path:
    return config.data_dir() / "state.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# UID tracking
# ---------------------------------------------------------------------------


def get_last_uid(uidvalidity: int) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT last_uid FROM mailbox_state WHERE uidvalidity = ?", (uidvalidity,)
        ).fetchone()
        return int(row["last_uid"]) if row else 0
    finally:
        conn.close()


def set_last_uid(uidvalidity: int, uid: int) -> None:
    """Monotonic: never moves backwards within a UIDVALIDITY generation."""
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO mailbox_state (uidvalidity, last_uid, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(uidvalidity) DO UPDATE SET
                 last_uid = MAX(last_uid, excluded.last_uid),
                 updated_at = excluded.updated_at""",
            (uidvalidity, uid, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Dedup + recording
# ---------------------------------------------------------------------------


def already_processed(uidvalidity: int, uid: int, attachment_index: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM processed WHERE uidvalidity=? AND uid=? AND attachment_index=?",
            (uidvalidity, uid, attachment_index),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def seen_attachment(message_id: str, sha256: str) -> bool:
    """Secondary dedup: was this exact attachment of this message ever handled?
    Catches UIDVALIDITY resets and state.db restores from backup."""
    if not sha256:
        return False
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM processed WHERE message_id=? AND attachment_sha256=?",
            (message_id or "", sha256),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def record_attachment(
    *,
    uidvalidity: int,
    uid: int,
    attachment_index: int,
    attachment_sha256: str,
    message_id: str = "",
    absender: str = "",
    pdf_dateiname: str = "",
    status: str,
    fehler: str = "",
    filed_filename: str = "",
    dokumenttitel: str = "",
    patientin_vorname: str = "",
    patientin_nachname: str = "",
    geburtsdatum: str = "",
) -> None:
    assert status in (STATUS_SUCCESS, STATUS_FAILED, STATUS_SKIPPED)
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO processed
               (uidvalidity, uid, attachment_index, attachment_sha256, message_id,
                absender, pdf_dateiname, status, fehler, filed_filename, dokumenttitel,
                patientin_vorname, patientin_nachname, geburtsdatum, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uidvalidity, uid, attachment_index, attachment_sha256, message_id or "",
             absender, pdf_dateiname, status, fehler, filed_filename, dokumenttitel,
             patientin_vorname, patientin_nachname, geburtsdatum, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pilot metrics + housekeeping
# ---------------------------------------------------------------------------


def stats(days: int | None = None) -> dict:
    """Counts for doctor.py --stats. days=None -> all time."""
    conn = get_conn()
    try:
        where, params = "", ()
        if days is not None:
            cutoff = datetime.now(TZ).timestamp() - days * 86400
            cutoff_iso = datetime.fromtimestamp(cutoff, TZ).isoformat(timespec="seconds")
            where, params = "WHERE created_at >= ?", (cutoff_iso,)
        rows = conn.execute(
            f"SELECT status, COUNT(*) AS n FROM processed {where} GROUP BY status", params
        ).fetchall()
        by_status = {r["status"]: r["n"] for r in rows}
        fails = conn.execute(
            f"SELECT fehler, COUNT(*) AS n FROM processed {where} "
            "AND fehler != '' GROUP BY fehler ORDER BY n DESC LIMIT 10"
            if where else
            "SELECT fehler, COUNT(*) AS n FROM processed WHERE fehler != '' "
            "GROUP BY fehler ORDER BY n DESC LIMIT 10",
            params,
        ).fetchall()
        return {
            "success": by_status.get(STATUS_SUCCESS, 0),
            "failed": by_status.get(STATUS_FAILED, 0),
            "skipped": by_status.get(STATUS_SKIPPED, 0),
            "total": sum(by_status.values()),
            "top_fehler": [(r["fehler"], r["n"]) for r in fails],
        }
    finally:
        conn.close()


def backup_if_due(max_age_days: int = 7) -> bool:
    """Weekly cold copy state.db -> state.backup.db (framing: state-loss safety).
    Returns True if a backup was written."""
    src = db_path()
    if not src.exists():
        return False
    dst = src.with_name("state.backup.db")
    if dst.exists() and (time.time() - dst.stat().st_mtime) < max_age_days * 86400:
        return False
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"[befund-state] Backup fehlgeschlagen: {e!r}", flush=True)
        return False
