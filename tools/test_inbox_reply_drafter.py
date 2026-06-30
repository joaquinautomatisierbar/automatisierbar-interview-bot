#!/usr/bin/env python3
"""Offline regression tests for inbox_reply_drafter.py.

Pure/offline — never touches IMAP, Notion, or the Claude API. Exercises the message
parsing, skip rules, threading-header construction, slot formatting, dash sanitizing,
state idempotency, and the Sent/Drafts dedup scan (via a fake IMAP).

Run:  python3 tools/test_inbox_reply_drafter.py   (exit 0 = all pass, 1 = failures)
"""
import os
import sys
import tempfile
from email.message import EmailMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inbox_reply_drafter as ird  # noqa: E402

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("  ok  " if cond else "FAIL  ") + name)


def _raw(*, from_hdr, subject, body, message_id="<m1@ext.example>", reply_to=None,
         references=None, in_reply_to=None, html=False, extra=None):
    m = EmailMessage()
    m["From"] = from_hdr
    if reply_to:
        m["Reply-To"] = reply_to
    m["Subject"] = subject
    m["Message-ID"] = message_id
    if references:
        m["References"] = references
    if in_reply_to:
        m["In-Reply-To"] = in_reply_to
    for k, v in (extra or {}).items():
        m[k] = v
    if html:
        m.set_content(body, subtype="html")
    else:
        m.set_content(body)
    return m.as_bytes()


# ---- parse_incoming ---------------------------------------------------------

raw = _raw(from_hdr="Anna Müller <anna@kunde.ch>",
           subject="Können wir den Termin verschieben?",
           body="Guten Tag\n\nKlappt es nächste Woche?\n\nGruss Anna",
           message_id="<orig-123@kunde.ch>",
           references="<root@kunde.ch> <prev@kunde.ch>")
p = ird.parse_incoming(raw)
check("parse from_email", p["from_email"] == "anna@kunde.ch")
check("parse from_name decoded", p["from_name"] == "Anna Müller")
check("parse subject umlaut", p["subject"] == "Können wir den Termin verschieben?")
check("parse message_id", p["message_id"] == "<orig-123@kunde.ch>")
check("parse references kept", p["references"] == "<root@kunde.ch> <prev@kunde.ch>")
check("parse body text", "Klappt es nächste Woche?" in p["body_text"])

raw_rt = _raw(from_hdr="Sender <sender@a.ch>", reply_to="Real Reply <reply@b.ch>",
              subject="Re: Test", body="x")
p_rt = ird.parse_incoming(raw_rt)
check("parse reply_to", p_rt["reply_to_email"] == "reply@b.ch")

raw_html = _raw(from_hdr="H <h@kunde.ch>", subject="HTML",
                body="<p>Hallo</p><div>Zweite Zeile</div>", html=True)
p_html = ird.parse_incoming(raw_html)
check("parse html flattened to text", "Hallo" in p_html["body_text"]
      and "Zweite Zeile" in p_html["body_text"] and "<p>" not in p_html["body_text"])


# ---- should_skip ------------------------------------------------------------

def _p(from_email, **kw):
    base = {"from_email": from_email, "auto_submitted": "", "list_unsubscribe": "",
            "list_id": "", "precedence": ""}
    base.update(kw)
    return base


check("skip: normal external sender passes", ird.should_skip(_p("anna@kunde.ch"))[0] is False)
check("skip: self/team domain", ird.should_skip(_p("tej@automatisierbar.ch"))[1] == "self/team")
check("skip: no-reply sender", ird.should_skip(_p("no-reply@news.com"))[1] == "no-reply-sender")
check("skip: noreply variant", ird.should_skip(_p("noreply@x.com"))[1] == "no-reply-sender")
check("skip: empty from", ird.should_skip(_p(""))[1] == "no-from")
check("skip: auto-submitted", ird.should_skip(_p("a@b.ch", auto_submitted="auto-replied"))[1] == "auto-submitted")
check("skip: auto-submitted=no passes", ird.should_skip(_p("a@b.ch", auto_submitted="no"))[0] is False)
check("skip: list-unsubscribe (newsletter)", ird.should_skip(_p("a@b.ch", list_unsubscribe="<mailto:u@b.ch>"))[1] == "bulk/list")
check("skip: precedence bulk", ird.should_skip(_p("a@b.ch", precedence="bulk"))[1] == "precedence-bulk")


# ---- build_re_subject -------------------------------------------------------

check("re: adds prefix", ird.build_re_subject("Angebot") == "Re: Angebot")
check("re: no double", ird.build_re_subject("Re: Angebot") == "Re: Angebot")
check("re: strips stacked", ird.build_re_subject("Re: Aw: WG: Angebot") == "Re: Angebot")
check("re: case-insensitive", ird.build_re_subject("AW: Frage") == "Re: Frage")
check("re: empty", ird.build_re_subject("") == "Re:")


# ---- build_references / pick_to_address -------------------------------------

refs = ird.build_references({"references": "<root@x> <prev@x>", "message_id": "<orig@x>"})
check("references chain", refs == "<root@x> <prev@x> <orig@x>")
refs2 = ird.build_references({"references": "", "message_id": "<orig@x>"})
check("references from message_id only", refs2 == "<orig@x>")
refs3 = ird.build_references({"references": "<orig@x>", "message_id": "<orig@x>"})
check("references no dup of message_id", refs3 == "<orig@x>")
check("to: prefers reply-to", ird.pick_to_address({"reply_to_email": "r@x", "from_email": "f@x"}) == "r@x")
check("to: falls back to from", ird.pick_to_address({"reply_to_email": "", "from_email": "f@x"}) == "f@x")


# ---- strip_prose_dashes -----------------------------------------------------

s = ird.strip_prose_dashes("Hallo — das ist gut – wirklich.")
check("dash: no em dash left", "—" not in s)
check("dash: no en dash left", "–" not in s)
check("dash: em becomes comma", "Hallo, das ist gut" in s)
check("dash: keeps compound hyphen", "30-Minuten-Termin" in ird.strip_prose_dashes("ein 30-Minuten-Termin"))
check("dash: range en-dash -> hyphen", ird.strip_prose_dashes("30–60") == "30-60")


# ---- build_quote (proper reply with quoted history) ------------------------

qp = {"body_text": "Hallo Joaquin\nWie besprochen.", "from_name": "Anna Müller",
      "from_email": "anna@kunde.ch", "date": "Mon, 30 Jun 2026 14:00:00 +0200"}
qt, qh = ird.build_quote(qp, "de")
check("quote: de attribution", qt.startswith("Am 30.06.2026, 14:00 schrieb Anna Müller <anna@kunde.ch>:"))
check("quote: lines prefixed >", "> Hallo Joaquin" in qt and "> Wie besprochen." in qt)
check("quote: html blockquote", "<blockquote" in qh and "Hallo Joaquin" in qh)
check("quote: en attribution", ird.build_quote(qp, "en")[0].startswith("On 30.06.2026, 14:00, Anna Müller <anna@kunde.ch> wrote:"))
check("quote: empty original -> empty", ird.build_quote({"body_text": ""}, "de") == ("", ""))
qt_long, _ = ird.build_quote({"body_text": "x" * 5000, "from_email": "a@b.ch", "date": ""}, "en")
check("quote: long original truncated", "[...]" in qt_long and len(qt_long) < 4000)


# ---- slot formatting --------------------------------------------------------

label = ird._format_slot_label("2026-07-01T14:00:00+02:00")
check("slot label german weekday", label.startswith("Mittwoch, 1. Juli 2026 um 14:00 Uhr"))
slots_json = {"days": [
    {"date": "2026-07-01", "slots": [{"start": "2026-07-01T08:00:00+02:00", "label": "08:00"},
                                     {"start": "2026-07-01T09:00:00+02:00", "label": "09:00"}]},
    {"date": "2026-07-02", "slots": [{"start": "2026-07-02T10:00:00+02:00", "label": "10:00"}]},
]}
collected = ird.collect_slots(slots_json, limit=3)
check("collect_slots flattens across days", len(collected) == 3)
check("collect_slots keeps iso", collected[0]["iso"] == "2026-07-01T08:00:00+02:00")
check("collect_slots respects limit", len(ird.collect_slots(slots_json, limit=2)) == 2)
check("collect_slots empty", ird.collect_slots({}, limit=3) == [])


# ---- state (idempotency) ----------------------------------------------------

_tmp = tempfile.mkdtemp(prefix="inbox-drafter-test-")
ird.STATE_PATH = os.path.join(_tmp, "state.json")
check("state: empty when missing", ird.load_state() == {"processed": {}, "last_run": ""})
st = {"processed": {"<a@x>": ird._now_iso(),
                    "<old@x>": "2000-01-01T00:00:00+00:00"},   # older than retention
      "last_run": ird._now_iso()}
ird.save_state(st)
reloaded = ird.load_state()
check("state: recent entry persisted", "<a@x>" in reloaded["processed"])
check("state: stale entry pruned", "<old@x>" not in reloaded["processed"])
check("state: last_run persisted", bool(reloaded["last_run"]))


# ---- folder detection + answered-ids scan (fake IMAP) -----------------------

LIST_LINES = [b'(\\HasNoChildren) "/" "INBOX"',
              b'(\\HasNoChildren \\Drafts) "/" "Drafts"',
              b'(\\HasNoChildren \\Sent) "/" "Sent"']
sent_name, sent_sep = ird._find_folder(LIST_LINES, "\\Sent", ("Sent",))
check("find Sent via special-use", sent_name == "Sent" and sent_sep == "/")
none_name, _ = ird._find_folder(LIST_LINES, "\\Junk", ("Junk", "Spam"))
check("find returns None when absent", none_name is None)


class FakeIMAP:
    """Minimal IMAP stand-in for collect_answered_ids: two messages whose threading
    headers reference an already-answered original."""
    def select(self, mbox, readonly=False):
        return "OK", [b"2"]

    def search(self, charset, *criteria):
        return "OK", [b"1 2"]

    def fetch(self, num, spec):
        data = {
            b"1": b"In-Reply-To: <orig-answered@kunde.ch>\r\n",
            b"2": b"References: <root@kunde.ch> <orig-drafted@kunde.ch>\r\n",
        }
        return "OK", [(b"x", data.get(num, b""))]


answered = ird.collect_answered_ids(FakeIMAP(), ["Sent", "Drafts"])
check("answered: picks up In-Reply-To id", "<orig-answered@kunde.ch>" in answered)
check("answered: picks up References ids", "<orig-drafted@kunde.ch>" in answered
      and "<root@kunde.ch>" in answered)
check("answered: skips empty folder names", ird.collect_answered_ids(FakeIMAP(), [None, ""]) == set())


print()
if FAIL:
    print(f"❌ {len(FAIL)} FAILED: {FAIL}")
    sys.exit(1)
print(f"✅ all {len(PASS)} inbox_reply_drafter tests passed")
sys.exit(0)
