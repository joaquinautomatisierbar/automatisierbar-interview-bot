"""reminder.py — monthly "Spesen noch offen" reminder (VPS cron, dry-run by default).

On the 25th a cron runs this; it finds active KnowBodies who have NOT closed the
current month and prints (logs) a per-person reminder. It does NOT send mail by
default: who sends the reminder and from which mailbox is an open client decision
(KnowBodies use Outlook; we won't email their staff before Markus confirms). The
_send() seam is where a real Outlook/SMTP sender drops in later.

Usage:
  python3 tools/spesen/reminder.py            # current month, dry-run
  python3 tools/spesen/reminder.py 2026-06    # explicit month, dry-run
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from . import db
except ImportError:  # pragma: no cover
    import db

TZ = ZoneInfo("Europe/Zurich")
_MONTHS = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"]
PWA_URL = os.environ.get("KNOWSPESEN_URL", "https://knowspesen.automatisierbar.ch/spesen")


def _month_label(jm: str) -> str:
    try:
        y, m = jm.split("-")
        return f"{_MONTHS[int(m)]} {y}"
    except Exception:
        return jm


def build_reminder(member: dict, jahr_monat: str) -> dict:
    vorname = (member.get("name") or "").split(" ")[0] or "Hallo"
    monat = _month_label(jahr_monat)
    subject = f"Erinnerung: Spesen {monat} noch offen"
    body = (
        f"Hallo {vorname}\n\n"
        f"deine Spesenabrechnung für {monat} ist noch nicht abgeschlossen.\n"
        f"Du kannst sie in KnowSpesen mit einem Klick abschliessen:\n{PWA_URL}\n\n"
        "Falls du diesen Monat keine Spesen hast, schliesse den Monat trotzdem kurz ab, "
        "damit die Buchhaltung eine saubere Bestätigung erhält.\n\n"
        "Freundliche Grüsse\nKnowSpesen"
    )
    return {"to": member.get("email") or "", "subject": subject, "body": body}


def _send(to: str, subject: str, body: str) -> bool:
    """Real sender drops in here (Outlook / SMTP / info@-relay) once the client
    confirms who reminds whom. Until then this is a no-op (dry-run)."""
    return False


def run(jahr_monat: str = "", send: bool = False) -> dict:
    jm = jahr_monat or datetime.now(TZ).strftime("%Y-%m")
    open_members = db.open_months(jm)
    sent = 0
    for m in open_members:
        r = build_reminder(m, jm)
        print(f"[reminder] OFFEN: {m['name']} <{m.get('email') or '—'}> · {jm}")
        if send and r["to"]:
            if _send(r["to"], r["subject"], r["body"]):
                sent += 1
    print(f"[reminder] {jm}: {len(open_members)} offen, {sent} gesendet "
          f"({'LIVE' if send else 'DRY-RUN'})")
    return {"month": jm, "open": len(open_members), "sent": sent, "dry_run": not send}


if __name__ == "__main__":
    month = sys.argv[1] if len(sys.argv) > 1 and "-" in sys.argv[1] else ""
    do_send = "--send" in sys.argv
    run(month, send=do_send)
