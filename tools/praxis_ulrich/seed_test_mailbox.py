#!/usr/bin/env python3
"""seed_test_mailbox.py — feed the dev-harness mailbox with corpus fixtures.

IMAP-APPENDs the testdata/eml/* fixtures into the TEST mailbox INBOX (profile
"test", e.g. an Infomaniak test account). No SMTP anywhere in this package —
nothing can ever be *sent*, only deposited into our own test INBOX.

The full e2e harness run is then:
  1. python3 tools/praxis_ulrich/seed_test_mailbox.py
  2. BEFUND_PROFILE=test python3 tools/praxis_ulrich/main.py --once --dry-run
  3. (real sink test) BEFUND_HOTFOLDER_PATH=/tmp/hot python3 .../main.py --once

Credentials: config test profile (test_imap_host/user) + secrets_store
imap_password (BEFUND_IMAP_PASSWORD env in dev). Exit 2 if missing.
"""

from __future__ import annotations

import imaplib
import os
import sys
import time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from praxis_ulrich import config, make_corpus, secrets_store  # noqa: E402


def main() -> int:
    cfg = config.load()
    cfg["profile"] = "test"   # dieser Feeder darf NIE auf das HIN-Profil zeigen
    settings = config.imap_settings(cfg)
    password = secrets_store.get_secret("imap_password")
    if not settings["user"] or not password:
        print("Test-IMAP nicht konfiguriert (BEFUND_TEST_IMAP_USER + BEFUND_IMAP_PASSWORD). "
              "Abbruch ohne Aktion.")
        return 2

    emldir = Path(make_corpus.TESTDATA) / "eml"
    if not emldir.is_dir() or not list(emldir.glob("*.eml")):
        make_corpus.build()

    conn = imaplib.IMAP4_SSL(settings["host"], settings["port"])
    try:
        conn.login(settings["user"], password)
        n = 0
        for eml in sorted(emldir.glob("*.eml")):
            typ, _ = conn.append("INBOX", None,
                                 imaplib.Time2Internaldate(time.time()),
                                 eml.read_bytes())
            print(f"  {'ok ' if typ == 'OK' else 'FAIL'} APPEND {eml.name}")
            n += typ == "OK"
        print(f"\n{n} Fixture-Mails in {settings['user']}/INBOX abgelegt.")
        return 0 if n else 1
    finally:
        try:
            conn.logout()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
