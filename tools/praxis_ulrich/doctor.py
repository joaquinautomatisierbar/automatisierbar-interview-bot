#!/usr/bin/env python3
"""doctor.py — On-Site-Selbsttest + Pilot-Statistik für den Befund-Automat.

Selbsttest (Install-Termin, Schritt für Schritt mit Dr. Ulrich):
  1. IMAP-Verbindung + Login + Ordnerwahl (HIN Mail Token)
  2. UIDVALIDITY lesbar
  3. Mails der letzten 7 Tage zählbar (readonly)
  4. Fähnchen-Roundtrip an einer SELBST angehängten Testnachricht — die einzige
     Stelle im ganzen System, die je eine Mail löscht, und zwar ausschliesslich
     unsere eigene Testnachricht (APPEND -> FLAG -> Verify -> EXPUNGE).
  5. Hotfolder beschreibbar (.part -> replace -> delete Probe)
  6. Toast + Clipboard sichtbar (visuell bestätigen)
  7. Optional --llm: EIN kleiner API-Ping (Kosten ~Rappen)

Usage:
  python3 tools/praxis_ulrich/doctor.py                # Selbsttest ohne LLM
  python3 tools/praxis_ulrich/doctor.py --llm          # inkl. LLM-Ping
  python3 tools/praxis_ulrich/doctor.py --stats [--days 7]
"""

from __future__ import annotations

import argparse
import imaplib
import os
import sys
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from praxis_ulrich import config, mailbox, notify, secrets_store, state  # noqa: E402

OK, FAIL, SKIP = "  ✅ ", "  ❌ ", "  ⏭️  "


def _p(status: str, msg: str) -> None:
    print(status + msg, flush=True)


def selftest(cfg: dict, *, with_llm: bool = False) -> int:
    failures = 0
    settings = config.imap_settings(cfg)
    print(f"Befund-Automat Selbsttest — Profil «{settings['profile']}», "
          f"Host {settings['host']}\n")

    password = secrets_store.get_secret("imap_password")
    if not password:
        _p(FAIL, "IMAP-Passwort/Mail-Token fehlt (secrets_store: imap_password)")
        return 1

    # 1-4: Mailbox
    try:
        with mailbox.MailboxClient(settings["host"], settings["port"],
                                   settings["user"], password,
                                   folder=settings["folder"]) as client:
            _p(OK, f"IMAP-Login als {settings['user']} + Ordner {settings['folder']}")
            if client.uidvalidity:
                _p(OK, f"UIDVALIDITY = {client.uidvalidity}")
            else:
                failures += 1
                _p(FAIL, "UIDVALIDITY nicht lesbar")

            try:
                typ, data = client.conn.uid("search", None, "SINCE", mailbox.imap_since(7))
                n = len(data[0].split()) if (typ == "OK" and data and data[0]) else 0
                _p(OK, f"Mails der letzten 7 Tage: {n}")
            except Exception as e:
                failures += 1
                _p(FAIL, f"SEARCH fehlgeschlagen: {e!r}")

            failures += _flag_roundtrip(client, settings["folder"])
    except Exception as e:
        _p(FAIL, f"IMAP-Verbindung fehlgeschlagen: {e!r}")
        failures += 1

    # 5: Hotfolder
    hot = cfg.get("hotfolder_path") or ""
    if not hot:
        _p(SKIP, "Hotfolder-Pfad noch nicht konfiguriert (Install-Termin)")
    else:
        try:
            probe = os.path.join(hot, ".befund-probe.part")
            final = os.path.join(hot, ".befund-probe")
            with open(probe, "wb") as f:
                f.write(b"probe")
            os.replace(probe, final)
            os.remove(final)
            _p(OK, f"Hotfolder beschreibbar: {hot}")
        except Exception as e:
            failures += 1
            _p(FAIL, f"Hotfolder-Probe fehlgeschlagen: {e!r}")

    # 6: Toast + Clipboard
    notifier = notify.make_notifier(cfg)
    try:
        notifier._toast("Befund-Automat Selbsttest",
                        "Wenn Sie das sehen, funktionieren Benachrichtigungen. ✅")
        _p(OK, "Toast ausgelöst — bitte visuell bestätigen")
    except Exception as e:
        failures += 1
        _p(FAIL, f"Toast fehlgeschlagen: {e!r}")
    try:
        notifier._clipboard("Befund-Automat Selbsttest — Zwischenablage funktioniert.")
        _p(OK, "Clipboard gesetzt — bitte mit Ctrl+V prüfen")
    except Exception as e:
        failures += 1
        _p(FAIL, f"Clipboard fehlgeschlagen: {e!r}")

    # 7: LLM-Ping (optional, EIN kleiner Call)
    if with_llm:
        try:
            from praxis_ulrich import providers
            key = secrets_store.get_secret("llm_api_key")
            if not key:
                failures += 1
                _p(FAIL, "LLM-API-Key fehlt (secrets_store: llm_api_key)")
            else:
                raw = providers.run_extraction(
                    "Antworte exakt mit {\"pong\": true}",
                    [{"type": "text", "text": "ping"}], cfg, key, max_tokens=20)
                _p(OK if "pong" in raw else FAIL, f"LLM-Ping: {raw.strip()[:60]}")
        except Exception as e:
            failures += 1
            _p(FAIL, f"LLM-Ping fehlgeschlagen: {e!r}")
    else:
        _p(SKIP, "LLM-Ping übersprungen (--llm für den Test)")

    print(f"\n{'ALLE CHECKS OK ✅' if failures == 0 else f'{failures} CHECK(S) FEHLGESCHLAGEN ❌'}")
    return 0 if failures == 0 else 1


def _flag_roundtrip(client: mailbox.MailboxClient, folder: str) -> int:
    """APPEND eigene Testnachricht -> Flag -> Verify -> Cleanup. Returns #failures."""
    marker = f"befund-selftest-{int(time.time())}"
    msg = (f"From: Befund-Automat <selftest@localhost>\r\n"
           f"Subject: Befund-Automat Selbsttest (wird gleich entfernt)\r\n"
           f"Message-ID: <{marker}@selftest>\r\n\r\n"
           f"Automatischer Fähnchen-Test.\r\n").encode()
    try:
        typ, _ = client.conn.append(folder, None, imaplib.Time2Internaldate(time.time()), msg)
        if typ != "OK":
            _p(FAIL, "Selbsttest-APPEND fehlgeschlagen")
            return 1
        typ, data = client.conn.uid("search", None, "HEADER", "Message-ID", f"<{marker}@selftest>")
        if typ != "OK" or not data or not data[0]:
            _p(FAIL, "Selbsttest-Nachricht nicht auffindbar")
            return 1
        uid = int(data[0].split()[-1])
        if not client.flag_red(uid):
            _p(FAIL, "Fähnchen setzen fehlgeschlagen")
            return 1
        typ, data = client.conn.uid("fetch", str(uid), "(FLAGS)")
        flagged = typ == "OK" and data and b"\\Flagged" in (data[0] if isinstance(data[0], bytes) else data[0][0])
        # Cleanup: NUR unsere eigene Testnachricht.
        client.conn.uid("STORE", str(uid), "+FLAGS", "(\\Deleted)")
        client.conn.expunge()
        if flagged:
            _p(OK, "Fähnchen-Roundtrip (setzen + verifizieren + aufräumen)")
            return 0
        _p(FAIL, "Fähnchen gesetzt, aber nicht verifizierbar")
        return 1
    except Exception as e:
        _p(FAIL, f"Fähnchen-Roundtrip fehlgeschlagen: {e!r}")
        return 1


def print_stats(days: int | None) -> int:
    state.init_db()
    s = state.stats(days)
    window = f"letzte {days} Tage" if days else "gesamt"
    print(f"Befund-Automat Statistik ({window}) — {datetime.now():%d.%m.%Y %H:%M}\n")
    print(f"  abgelegt (success):   {s['success']}")
    print(f"  fehlgeschlagen:       {s['failed']}")
    print(f"  übersprungen:         {s['skipped']}   (kein Befund / Duplikate)")
    print(f"  total:                {s['total']}")
    if s["top_fehler"]:
        print("\n  häufigste Fehler:")
        for fehler, n in s["top_fehler"]:
            print(f"    {n:>3}× {fehler}")
    if s["total"]:
        rate = s["success"] / max(s["success"] + s["failed"], 1) * 100
        print(f"\n  Erkennungs-/Ablagequote: {rate:.0f}% "
              f"(Pilot-Gate: ≥95% und NULL falsche Patientenzuordnungen)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Befund-Automat doctor")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--llm", action="store_true", help="inkl. 1 kleinem LLM-Ping")
    ap.add_argument("--profile", choices=["hin", "test"], default=None)
    args = ap.parse_args(argv)

    if args.stats:
        return print_stats(args.days)
    cfg = config.load()
    if args.profile:
        cfg["profile"] = args.profile
    return selftest(cfg, with_llm=args.llm)


if __name__ == "__main__":
    sys.exit(main())
