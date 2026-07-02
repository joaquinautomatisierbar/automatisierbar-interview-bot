#!/usr/bin/env python3
"""Offline tests for praxis_ulrich.mailbox — attachment extraction, UID discovery,
PEEK fetch, flagging. FakeIMAP, no network.

Run: python3 tools/test_praxis_mailbox.py
"""
import os
import sys
import tempfile
from datetime import datetime
from email.message import EmailMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BEFUND_DATA_DIR", tempfile.mkdtemp(prefix="befund_mbx_"))

from praxis_ulrich import mailbox  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


PDF_A = b"%PDF-1.4 fake-a"
PDF_B = b"%PDF-1.4 fake-b"


def build_mail(pdfs=None, *, from_="befunde@usz.ch", subject="Befund",
               octet_stream=False, with_image=False, unnamed_pdf=False) -> bytes:
    m = EmailMessage()
    m["From"] = from_
    m["To"] = "praxis-ulrich@hin.ch"
    m["Subject"] = subject
    m["Message-ID"] = "<t1@test>"
    m.set_content("Guten Tag, anbei der Bericht.")
    for i, blob in enumerate(pdfs or []):
        if octet_stream:
            m.add_attachment(blob, maintype="application", subtype="octet-stream",
                             filename=f"bericht_{i}.pdf")
        elif unnamed_pdf:
            m.add_attachment(blob, maintype="application", subtype="pdf")
        else:
            m.add_attachment(blob, maintype="application", subtype="pdf",
                             filename=f"Bericht {i} — Ümlaut.pdf")
    if with_image:
        m.add_attachment(b"\x89PNG fake", maintype="image", subtype="png",
                         filename="logo.png")
    return bytes(m)


# --- extract_pdf_attachments ---------------------------------------------------
atts = mailbox.extract_pdf_attachments(build_mail([PDF_A]))
check("1 PDF erkannt", len(atts) == 1 and atts[0][1] == PDF_A and atts[0][2] == 0)
check("Dateiname decodiert (Umlaut)", "Ümlaut" in atts[0][0])

atts = mailbox.extract_pdf_attachments(build_mail([PDF_A, PDF_B]))
check("2 PDFs, Indizes 0/1", [a[2] for a in atts] == [0, 1] and atts[1][1] == PDF_B)

atts = mailbox.extract_pdf_attachments(build_mail([PDF_A], octet_stream=True))
check("octet-stream mit .pdf-Namen zählt", len(atts) == 1)

atts = mailbox.extract_pdf_attachments(build_mail([PDF_A], unnamed_pdf=True))
check("PDF ohne Dateinamen -> Fallback-Name", len(atts) == 1 and atts[0][0] == "anhang-1.pdf")

atts = mailbox.extract_pdf_attachments(build_mail([], with_image=True))
check("Bild-Anhang ignoriert", atts == [])

check("kein Anhang -> []", mailbox.extract_pdf_attachments(build_mail([])) == [])
check("Garbage-Bytes -> [] (never raises)", mailbox.extract_pdf_attachments(b"\x00\xff kaputt") == [])

meta = mailbox.parse_message_meta(build_mail([PDF_A]))
check("meta message_id", meta["message_id"] == "<t1@test>")
check("meta from_email", meta["from_email"] == "befunde@usz.ch")
check("meta subject", meta["subject"] == "Befund")

# --- imap_since / internaldate ---------------------------------------------------
check("imap_since Format", mailbox.imap_since(3, today=datetime(2026, 7, 2)) == "29-Jun-2026")
dt = mailbox._parse_internaldate(b'1 (UID 7 INTERNALDATE "02-Jul-2026 09:32:00 +0200" BODY[] {5}')
check("INTERNALDATE geparst", dt == datetime(2026, 7, 2, 9, 32, 0))
check("INTERNALDATE fehlt -> None", mailbox._parse_internaldate(b"1 (UID 7)") is None)


# --- FakeIMAP + MailboxClient ----------------------------------------------------
class FakeIMAP:
    """Just enough imaplib surface for MailboxClient. Mailbox: {uid: raw_bytes}."""

    def __init__(self, msgs, uidvalidity=424242, fail_store=False):
        self.msgs = msgs
        self.uidvalidity = uidvalidity
        self.fail_store = fail_store
        self.flagged = []
        self.logged_out = False
        self.fetch_commands = []

    def login(self, u, p):
        return ("OK", [b"Logged in"])

    def select(self, folder):
        return ("OK", [str(len(self.msgs)).encode()])

    def response(self, key):
        if key == "UIDVALIDITY":
            return (key, [str(self.uidvalidity).encode()])
        return (key, [None])

    def status(self, folder, what):
        return ("OK", [f"INBOX (UIDVALIDITY {self.uidvalidity})".encode()])

    def uid(self, cmd, *args):
        cmd = cmd.lower()
        if cmd == "search":
            crit = [a for a in args if a]
            if "UID" in crit:
                rng = crit[crit.index("UID") + 1]
                lo = int(rng.split(":")[0])
                # RFC quirk: N:* matches at least the last message
                hits = sorted(u for u in self.msgs if u >= lo) or sorted(self.msgs)[-1:]
            else:  # SINCE — Fake: alle
                hits = sorted(self.msgs)
            return ("OK", [b" ".join(str(u).encode() for u in hits)])
        if cmd == "fetch":
            uid = int(args[0])
            self.fetch_commands.append(args[1])
            raw = self.msgs.get(uid)
            if raw is None:
                return ("OK", [None])
            meta = f'{uid} (UID {uid} INTERNALDATE "02-Jul-2026 09:32:00 +0200" BODY[] {{{len(raw)}}}'.encode()
            return ("OK", [(meta, raw), b")"])
        if cmd == "store":
            if self.fail_store:
                return ("NO", [b"nope"])
            self.flagged.append(int(args[0]))
            return ("OK", [b""])
        raise AssertionError(f"unexpected uid cmd {cmd}")

    def logout(self):
        self.logged_out = True
        return ("BYE", [b""])


msgs = {5: build_mail([PDF_A]), 7: build_mail([PDF_A, PDF_B]), 9: build_mail([])}
fake = FakeIMAP(msgs)
client = mailbox.MailboxClient("h", 993, "u", "pw", conn_factory=lambda h, p: fake).connect()

check("UIDVALIDITY gelesen", client.uidvalidity == 424242)
check("neue UIDs > last", client.new_uids(5) == [7, 9])
check("UID-Quirk gefiltert (nichts Neues)", client.new_uids(9) == [])
check("Rescan-Fenster liefert alles", client.new_uids(9, rescan_days=3) == [5, 7, 9])

raw, internal = client.fetch_raw(7)
check("fetch_raw Bytes", raw == msgs[7])
check("fetch_raw INTERNALDATE", internal == datetime(2026, 7, 2, 9, 32, 0))
check("fetch nutzt BODY.PEEK (kein \\Seen)", all(b"PEEK" in c.encode() if isinstance(c, str) else b"PEEK" in c for c in fake.fetch_commands))

check("flag_red OK", client.flag_red(7) and fake.flagged == [7])
client.close()
check("logout aufgerufen", fake.logged_out)

fake2 = FakeIMAP(msgs, fail_store=True)
client2 = mailbox.MailboxClient("h", 993, "u", "pw", conn_factory=lambda h, p: fake2).connect()
check("flag_red NO -> False (nie Exception)", client2.flag_red(5) is False)
client2.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
