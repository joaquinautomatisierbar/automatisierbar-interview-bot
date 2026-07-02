#!/usr/bin/env python3
"""Offline tests for praxis_ulrich.notify (batching, rate limit) + main helpers
(InMemoryState isolation, single-instance lock).

Run: python3 tools/test_praxis_notify.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["BEFUND_DATA_DIR"] = tempfile.mkdtemp(prefix="befund_ntf_")

from praxis_ulrich import notify  # noqa: E402
from praxis_ulrich.pipeline import AttachmentOutcome  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


def outcome(titel="Urinkultur 06/2026", z="Z1\nZ2\nZ3\nZ4", vn="Maria", nn="Muster"):
    return AttachmentOutcome(index=0, pdf_name="x.pdf", status="success",
                             dokumenttitel=titel, vorname=vn, nachname=nn,
                             geburtsdatum="12.03.1985", zusammenfassung=z)


# --- Batching -----------------------------------------------------------------
n = notify.LogNotifier({})
n.doc_success(outcome())
payload = n.flush_cycle()
check("1 Doc -> nackter 4-Zeiler (direkt einfügbar)", payload == "Z1\nZ2\nZ3\nZ4")
check("Toast gefeuert", len(n.toasts) == 1 and "Urinkultur 06/2026" in n.toasts[0][1])
check("flush leert Zyklus", n.flush_cycle() is None)

n = notify.LogNotifier({})
n.doc_success(outcome(titel="A 06/2026", z="a1\na2\na3\na4"))
n.doc_success(outcome(titel="B 06/2026", z="b1\nb2\nb3\nb4", nn="Probe", vn="Petra"))
payload = n.flush_cycle()
check("2 Docs -> Header pro Doc", "[A 06/2026 · Maria Muster]" in payload
      and "[B 06/2026 · Petra Probe]" in payload)
check("2 Docs -> beide 4-Zeiler", "a4" in payload and "b1" in payload)
check("Clipboard einmal gesetzt", len(n.clipboards) == 1)

n = notify.LogNotifier({})
n.doc_success(outcome(z=""))
check("leere Zusammenfassung -> kein Clipboard-Payload", n.flush_cycle() is None)

# --- Fehler-Toasts + Rate-Limit -------------------------------------------------
n = notify.LogNotifier({"error_toast_cooldown_min": 60})
o = AttachmentOutcome(index=0, pdf_name="kaputt.pdf", status="failed")
n.doc_unrecognized(o, "spam@example.com")
n.doc_unrecognized(o, "spam@example.com")
check("identischer Fehler-Toast nur 1× pro Stunde", len(n.toasts) == 1)
n.doc_filing_failed(o, "C:\\Hotfolder")
check("anderer Fehler -> neuer Toast", len(n.toasts) == 2)
check("Ziel im Ablage-Fehler-Toast", "C:\\Hotfolder" in n.toasts[1][1])
n.connection_problem()
check("Verbindungs-Toast", "Verbindung" in n.toasts[2][0])

n2 = notify.LogNotifier({"error_toast_cooldown_min": 0})
n2.doc_unrecognized(o, "a@b.c")
n2.doc_unrecognized(o, "a@b.c")
check("Cooldown 0 -> jedes Mal", len(n2.toasts) == 2)

# --- make_notifier ----------------------------------------------------------------
check("macOS/dev -> LogNotifier", isinstance(notify.make_notifier({}), notify.LogNotifier)
      or sys.platform == "win32")

# --- main: InMemoryState + Lock -----------------------------------------------------
from praxis_ulrich import main as bmain, state  # noqa: E402

ms = bmain.InMemoryState()
ms.record_attachment(uidvalidity=1, uid=2, attachment_index=0,
                     attachment_sha256="s", message_id="<m>", status="success")
check("InMemoryState dedupt intern", ms.already_processed(1, 2, 0) and ms.seen_attachment("<m>", "s"))
check("InMemoryState: last_uid immer 0 (echter Lauf sieht alles neu)",
      ms.get_last_uid(1) == 0)
state.init_db()
check("InMemoryState berührt echte DB nicht", state.stats()["total"] == 0)

check("Single-Instance-Lock: erster gewinnt", bmain._acquire_single_instance_lock())
check("Single-Instance-Lock: eigener PID lebt -> zweite Instanz nein",
      not bmain._acquire_single_instance_lock())

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
