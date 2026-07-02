#!/usr/bin/env python3
"""Offline tests for praxis_ulrich config + state (dedup, UID tracking, stats).

Run: python3 tools/test_praxis_state.py   (exit 0 = pass). No network, no key.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Isolate ALL app data in a temp dir BEFORE importing the package.
_TMP = tempfile.mkdtemp(prefix="befund_state_")
os.environ["BEFUND_DATA_DIR"] = _TMP

from praxis_ulrich import config, state  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- config invariants --------------------------------------------------------
check("25 Titel-Vorlagen", len(config.TITEL_VORLAGEN) == 25)
check("Titel-Vorlagen eindeutig", len(set(config.TITEL_VORLAGEN)) == 25)
check("kein Titel mit / (Dateinamen)", all("/" not in t and "\\" not in t for t in config.TITEL_VORLAGEN))

cfg = config.load()
check("Default-Profil test (nie versehentlich prod)", cfg["profile"] == "test")
check("HIN Host korrekt", cfg["hin_imap_host"] == "imap.mail.hin.ch")
check("Default-Sink hotfolder", cfg["sink"] == "hotfolder")
check("data_dir = BEFUND_DATA_DIR override", str(config.data_dir()) == _TMP)

os.environ["BEFUND_POLL_INTERVAL_SEC"] = "60"
check("env override int", config.load()["poll_interval_sec"] == 60)
del os.environ["BEFUND_POLL_INTERVAL_SEC"]

imap = config.imap_settings(cfg)
check("imap_settings test-Profil", imap["host"] == cfg["test_imap_host"] and imap["port"] == 993)
imap_hin = config.imap_settings({**cfg, "profile": "hin"})
check("imap_settings hin-Profil", imap_hin["host"] == "imap.mail.hin.ch")

# --- state: init idempotent ----------------------------------------------------
state.init_db()
state.init_db()
check("init_db idempotent", state.db_path().exists())

# --- UID tracking ---------------------------------------------------------------
check("last_uid unbekannt -> 0", state.get_last_uid(1111) == 0)
state.set_last_uid(1111, 50)
check("last_uid gesetzt", state.get_last_uid(1111) == 50)
state.set_last_uid(1111, 40)
check("last_uid monoton (kein Rückschritt)", state.get_last_uid(1111) == 50)
state.set_last_uid(1111, 60)
check("last_uid vorwärts", state.get_last_uid(1111) == 60)
check("UIDVALIDITY getrennt", state.get_last_uid(2222) == 0)

# --- dedup: primary + secondary --------------------------------------------------
check("unbekannt -> not processed", not state.already_processed(1111, 7, 0))
state.record_attachment(
    uidvalidity=1111, uid=7, attachment_index=0, attachment_sha256="abc123",
    message_id="<m1@hin.ch>", absender="befunde@usz.ch", pdf_dateiname="bericht.pdf",
    status=state.STATUS_SUCCESS, filed_filename="Urinkultur 06-2026_Muster_Maria.pdf",
    dokumenttitel="Urinkultur 06/2026",
    patientin_vorname="Maria", patientin_nachname="Muster", geburtsdatum="12.03.1985",
)
check("primary dedup greift", state.already_processed(1111, 7, 0))
check("anderer Anhang nicht dedupt", not state.already_processed(1111, 7, 1))
check("secondary dedup (message_id+sha)", state.seen_attachment("<m1@hin.ch>", "abc123"))
check("secondary: anderer sha nicht", not state.seen_attachment("<m1@hin.ch>", "zzz"))
check("secondary: leerer sha nie True", not state.seen_attachment("<m1@hin.ch>", ""))

# UIDVALIDITY reset: same mail appears under new (uidvalidity, uid) — secondary must catch it
check("UIDVALIDITY-Reset: primary greift nicht", not state.already_processed(9999, 3, 0))
check("UIDVALIDITY-Reset: secondary rettet", state.seen_attachment("<m1@hin.ch>", "abc123"))

# failed + skipped are terminal (recorded and deduped, no auto-retry)
state.record_attachment(
    uidvalidity=1111, uid=8, attachment_index=0, attachment_sha256="def456",
    message_id="<m2@hin.ch>", status=state.STATUS_FAILED, fehler="LLM Timeout",
)
check("failed ist terminal", state.already_processed(1111, 8, 0))
state.record_attachment(
    uidvalidity=1111, uid=9, attachment_index=0, attachment_sha256="ghi789",
    message_id="<m3@hin.ch>", status=state.STATUS_SKIPPED, fehler="kein Befund",
)
check("skipped ist terminal", state.already_processed(1111, 9, 0))

# INSERT OR REPLACE: re-record same key does not duplicate
state.record_attachment(
    uidvalidity=1111, uid=7, attachment_index=0, attachment_sha256="abc123",
    message_id="<m1@hin.ch>", status=state.STATUS_SUCCESS,
)
s_all = state.stats()
check("kein Duplikat bei re-record", s_all["total"] == 3)

# --- stats -----------------------------------------------------------------------
check("stats success", s_all["success"] == 1)
check("stats failed", s_all["failed"] == 1)
check("stats skipped", s_all["skipped"] == 1)
check("stats top_fehler enthält LLM Timeout", any("LLM Timeout" == f for f, _ in s_all["top_fehler"]))
s_week = state.stats(days=7)
check("stats mit Zeitfenster", s_week["total"] == 3)

# --- backup ----------------------------------------------------------------------
check("backup schreibt", state.backup_if_due())
check("backup existiert", (state.db_path().with_name("state.backup.db")).exists())
check("backup nicht doppelt (frisch)", not state.backup_if_due())

# --- secrets_store (env path only, no keyring dependency) ------------------------
from praxis_ulrich import secrets_store  # noqa: E402

os.environ["BEFUND_IMAP_PASSWORD"] = "tok-123"
check("secret aus env", secrets_store.get_secret("imap_password") == "tok-123")
del os.environ["BEFUND_IMAP_PASSWORD"]
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["ANTHROPIC_API_KEY"] = "sk-test"
check("llm_api_key Fallback auf ANTHROPIC_API_KEY", secrets_store.get_secret("llm_api_key") == "sk-test")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
