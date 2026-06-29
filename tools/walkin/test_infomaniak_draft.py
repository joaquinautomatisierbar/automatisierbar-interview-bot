#!/usr/bin/env python3
"""Offline regression tests for infomaniak_draft.py.

Locks the invariants that matter for a tool that deposits DRAFTS into a live mailbox:
  - it can never send (smtplib is never imported),
  - MIME is well-formed UTF-8 with CRLF endings,
  - an empty/best-guess recipient yields no To header (An: leer),
  - the Drafts folder + subfolder path is resolved for both "/" and "." separators,
    incl. RFC 6154 \\Drafts special-use and a localized "Entwürfe" name.

Pure/offline — never touches Infomaniak. Run:

    python3 tools/walkin/test_infomaniak_draft.py     # exit 0 = all pass
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import infomaniak_draft as ifd

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("  ok  " if cond else "FAIL  ") + name)


# --- no-send guarantee: the tool must never pull in smtplib --------------------
check("smtplib nicht importiert (kann nicht senden)", "smtplib" not in sys.modules)
with open(ifd.__file__) as f:
    src = f.read()
check("kein smtplib im Quelltext", "import smtplib" not in src and "smtplib." not in src)
check("append nutzt \\Draft-Flag", "(\\\\Draft)" in src)

# --- MIME build: confident draft ----------------------------------------------
d1 = {"company": "Furness Shipping AG", "to": "rkortland@furness.ch",
      "subject": "Unser Besuch bei Ihnen, kurzer nächster Schritt",
      "body": "Guten Tag Herr Kortland,\n\nVersand- und Zolldokumente.\n👉 https://x\n\nGrüsse",
      "confident": True}
m1 = ifd.build_message(d1, "joaquin@automatisierbar.ch", msgid="<a@automatisierbar.ch>")
b1 = ifd.message_bytes(m1)
check("From korrekt", m1["From"] == "joaquin@automatisierbar.ch")
check("To korrekt", m1["To"] == "rkortland@furness.ch")
check("Subject korrekt", m1["Subject"].startswith("Unser Besuch"))
check("X-Walkin-Company gesetzt", m1["X-Walkin-Company"] == "Furness Shipping AG")
check("CRLF vorhanden", b"\r\n" in b1)
check("keine nackten LF", b"\n" not in b1.replace(b"\r\n", b""))
check("Umlaut erhalten", "Grüsse" in m1.get_content())
check("ß/Emoji erhalten", "👉" in m1.get_content())
check("Subject roundtrips als UTF-8", m1.get("Subject") == d1["subject"])

# --- empty-To (best-guess address) --------------------------------------------
d2 = {"company": "Pro Infirmis", "to": "", "subject": "B", "body": "x", "confident": False}
m2 = ifd.build_message(d2, "joaquin@automatisierbar.ch", msgid="<b@automatisierbar.ch>")
check("Empty-To => kein To-Header", m2["To"] is None)
check("Empty-To behält From", m2["From"] == "joaquin@automatisierbar.ch")

# --- folder detection ----------------------------------------------------------
slash = [b'(\\HasNoChildren) "/" "INBOX"',
         b'(\\HasNoChildren \\Drafts) "/" "Drafts"',
         b'(\\HasNoChildren \\Sent) "/" "Sent"']
p, sep = ifd.pick_drafts_folder(slash)
check("special-use \\Drafts (/)", p == "Drafts" and sep == "/")
check("Zielpfad Drafts/Walk-in", ifd.build_target(p, sep, "Walk-in") == "Drafts/Walk-in")

dot = [b'(\\HasNoChildren) "." INBOX', b'(\\HasNoChildren \\Drafts) "." INBOX.Drafts']
p2, sep2 = ifd.pick_drafts_folder(dot)
check("special-use mit sep '.'", p2 == "INBOX.Drafts" and sep2 == ".")
check("Zielpfad INBOX.Drafts.Walk-in", ifd.build_target(p2, sep2, "Walk-in") == "INBOX.Drafts.Walk-in")

noflag = [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Drafts"']
p3, sep3 = ifd.pick_drafts_folder(noflag)
check("Fallback auf Namen 'Drafts'", p3 == "Drafts")

de = [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren \\Drafts) "/" "Entw\xc3\xbcrfe"']
p4, _ = ifd.pick_drafts_folder(de)
check("lokalisierter Drafts-Name", p4 is not None and "Entw" in p4)

empty = ifd.pick_drafts_folder([])
check("leere LIST => (None, '/')", empty == (None, "/"))

# --- quoting -------------------------------------------------------------------
check("Quoting einfach", ifd._q("Drafts/Walk-in") == '"Drafts/Walk-in"')
check("Quoting escaped", ifd._q('a"b') == '"a\\"b"')

# --- config defaults -----------------------------------------------------------
cfg = ifd.load_config()
check("config host default", cfg["imap_host"] == "mail.infomaniak.com")
check("config subfolder leer => Haupt-Drafts", cfg["drafts_subfolder"] == "")
# empty subfolder must resolve the target to the bare Drafts parent
check("leerer Subfolder => Ziel = Drafts", ifd.build_target("Drafts", "/", cfg["drafts_subfolder"]) == "Drafts")

print()
if FAIL:
    print(f"❌ {len(FAIL)} FEHLGESCHLAGEN: {FAIL}")
    sys.exit(1)
print(f"✅ alle {len(PASS)} infomaniak_draft Tests bestanden")
