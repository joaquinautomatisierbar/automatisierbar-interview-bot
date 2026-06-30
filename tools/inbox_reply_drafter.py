#!/usr/bin/env python3
"""inbox_reply_drafter.py — draft replies to inbound business mail as Infomaniak IMAP drafts.

Every business-relevant email arriving at joaquin@automatisierbar.ch gets a ready-to-edit
REPLY DRAFT placed in the Infomaniak Drafts folder, threaded under the original message.
Joaquin opens his normal mail app, checks/edits, and hits send. Nothing is ever sent
automatically — the draft IS the approval surface (same model as the /walkinmail flow).

Flow per run (VPS cron, every ~10 min):
  1. poll INBOX (readonly => messages stay UNREAD) for mail since the last run
  2. cheap pre-LLM skip rules (self/team, no-reply, newsletters, auto-submitted)
  3. dedup: skip anything already replied to / already drafted (Sent + Drafts In-Reply-To
     scan) and anything in the local state file
  4. classify relevance + category + language (Claude Haiku) — drop non-business mail
  5. gather context: matching CRM lead, any existing appointment, live free booking slots
  6. draft a reply in Joaquin's voice (Claude Sonnet), German Sie by default, no em-dashes
  7. APPEND a threaded draft (In-Reply-To / References) to the Drafts folder

Reuses: tools/walkin/infomaniak_draft.py (build_message + APPEND + folder detection),
tools/walkin/infomaniak_signature.py (signature), tools/claude_client.py (classify + draft),
tools/notion_session.py (lead + appointment context), the Cockpit /api/book/slots endpoint.

DRAFTS ONLY — imports imaplib only, never smtplib / the Mail-API send path. By construction
this tool cannot send. Missing creds / errors degrade to a logged no-op.

Auth (.env or /etc/cockpit/env): JOAQUIN_IMAP_USER / JOAQUIN_IMAP_PASSWORD (Infomaniak app
password for the joaquin@ mailbox; falls back to INFOMANIAK_IMAP_* for local dev where those
already point at joaquin). Context: NOTION_API_KEY, COCKPIT_APPOINTMENTS_DB_ID, ANTHROPIC_API_KEY.

Usage:
  python3 tools/inbox_reply_drafter.py --dry-run --verbose   # preview, no mailbox writes
  python3 tools/inbox_reply_drafter.py --max-per-run 2       # supervised first live run
  python3 tools/inbox_reply_drafter.py                       # cron mode
  python3 tools/inbox_reply_drafter.py --list-folders        # debug folder detection
"""

import argparse
import email
import email.policy
import imaplib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr

import requests

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TOOLS_DIR)
_WALKIN_DIR = os.path.join(_TOOLS_DIR, "walkin")
sys.path.insert(0, _TOOLS_DIR)
sys.path.insert(0, _WALKIN_DIR)

# Reused mail machinery (stdlib-only imports underneath — safe to import offline).
from infomaniak_draft import (  # noqa: E402
    build_message, message_bytes, pick_drafts_folder, build_target, _q,
    _parse_list_line, env, load_config,
)
from infomaniak_signature import get_signature, html_to_text  # noqa: E402

STATE_PATH = os.path.join(_REPO_ROOT, ".tmp", "inbox-reply-drafter-state.json")
DEFAULT_SINCE_DAYS = 3
DEFAULT_MAX_PER_RUN = 10
DEFAULT_MAX_SCAN = 80          # bound on classify calls per run (first run can see many mails)
STATE_RETENTION_DAYS = 30
ANSWERED_SCAN_LIMIT = 600      # most-recent Sent/Drafts messages to scan for dedup
SELF_DOMAIN = "automatisierbar.ch"

_RE_PREFIX = re.compile(r"^\s*(re|aw|antw|rv|tr|fwd|wg)\s*:\s*", re.I)
_NOREPLY_LOCALPARTS = {
    "no-reply", "noreply", "no_reply", "donotreply", "do-not-reply", "do_not_reply",
    "mailer-daemon", "postmaster", "bounce", "bounces", "notification", "notifications",
    "newsletter", "news", "mailing", "info-noreply",
}
_WD_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_MON_DE = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
           "September", "Oktober", "November", "Dezember"]


# ---- pure helpers (offline-testable) ----------------------------------------

def _dh(raw) -> str:
    """Decode a possibly MIME-encoded header to a plain str."""
    if raw is None:
        return ""
    try:
        return str(make_header(decode_header(str(raw))))
    except Exception:
        return str(raw)


def _body_text(msg) -> str:
    """Best plain-text body from a parsed message. Prefers text/plain; falls back to
    flattening text/html via the signature tool's html_to_text."""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(
                        part.get("Content-Disposition", "")):
                    return part.get_content()
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    return html_to_text(part.get_content())
            return ""
        if msg.get_content_type() == "text/html":
            return html_to_text(msg.get_content())
        return msg.get_content()
    except Exception:
        return ""


def parse_incoming(raw: bytes) -> dict:
    """Parse a raw RFC 5322 message into the fields the drafter needs."""
    m = email.message_from_bytes(raw, policy=email.policy.default)
    from_name, from_email = parseaddr(str(m.get("From", "")))
    _, reply_to_email = parseaddr(str(m.get("Reply-To", "")))
    return {
        "message_id": (str(m.get("Message-ID", "")) or "").strip(),
        "in_reply_to": (str(m.get("In-Reply-To", "")) or "").strip(),
        "references": (str(m.get("References", "")) or "").strip(),
        "from_name": _dh(from_name).strip(),
        "from_email": (from_email or "").lower().strip(),
        "reply_to_email": (reply_to_email or "").lower().strip(),
        "subject": _dh(m.get("Subject", "")).strip(),
        "date": str(m.get("Date", "")).strip(),
        "body_text": (_body_text(m) or "").strip(),
        "list_unsubscribe": str(m.get("List-Unsubscribe", "")).strip(),
        "list_id": str(m.get("List-Id", "")).strip(),
        "auto_submitted": str(m.get("Auto-Submitted", "")).strip().lower(),
        "precedence": str(m.get("Precedence", "")).strip().lower(),
    }


def should_skip(p: dict, self_domain: str = SELF_DOMAIN):
    """Cheap pre-LLM gate. Returns (skip: bool, reason: str)."""
    addr = (p.get("from_email") or "").lower()
    if not addr or "@" not in addr:
        return True, "no-from"
    localpart, _, domain = addr.partition("@")
    if domain == self_domain:
        return True, "self/team"
    if localpart in _NOREPLY_LOCALPARTS or localpart.startswith(("no-reply", "noreply", "donotreply")):
        return True, "no-reply-sender"
    if p.get("auto_submitted") and p["auto_submitted"] != "no":
        return True, "auto-submitted"
    if p.get("list_unsubscribe") or p.get("list_id"):
        return True, "bulk/list"
    if p.get("precedence") in ("bulk", "list", "junk"):
        return True, "precedence-bulk"
    return False, ""


def build_re_subject(subject: str) -> str:
    """Single 'Re: ' prefix, stripping any stacked Re:/Aw:/Fwd: first."""
    s = (subject or "").strip()
    while True:
        m = _RE_PREFIX.match(s)
        if not m:
            break
        s = s[m.end():].strip()
    return f"Re: {s}" if s else "Re:"


def build_references(p: dict) -> str:
    """RFC 5322 References for the reply: original References chain + original Message-ID."""
    parts = []
    refs = (p.get("references") or "").strip()
    if refs:
        parts.append(refs)
    mid = (p.get("message_id") or "").strip()
    if mid and mid not in refs:
        parts.append(mid)
    return " ".join(parts).strip()


def pick_to_address(p: dict) -> str:
    """Where the reply goes: Reply-To if present, else From."""
    return p.get("reply_to_email") or p.get("from_email") or ""


def strip_prose_dashes(text: str) -> str:
    """Safety net for the no-em-dash rule. Converts prose em/en dashes to a comma; turns any
    leftover en-dash into a plain hyphen. Compound-word hyphens (30-Minuten-Termin) untouched."""
    t = text or ""
    for sep in (" — ", " – ", " —", "— ", " –", "– "):
        t = t.replace(sep, ", ")
    t = t.replace("—", ", ")   # any leftover em dash
    t = t.replace("–", "-")    # any leftover en dash -> hyphen
    return t


def _format_slot_label(iso: str) -> str:
    """German label for a slot start datetime, e.g. 'Dienstag, 1. Juli 2026 um 14:00 Uhr'."""
    dt = datetime.fromisoformat(iso)
    return f"{_WD_DE[dt.weekday()]}, {dt.day}. {_MON_DE[dt.month]} {dt.year} um {dt:%H:%M} Uhr"


def collect_slots(slots_json: dict, limit: int = 3) -> list:
    """Flatten the /api/book/slots response to the first `limit` free slots as
    [{iso, label}, ...]."""
    out = []
    for day in (slots_json.get("days") or []):
        for s in (day.get("slots") or []):
            iso = s.get("start")
            if not iso:
                continue
            try:
                label = _format_slot_label(iso)
            except Exception:
                label = iso
            out.append({"iso": iso, "label": label})
            if len(out) >= limit:
                return out
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---- state (idempotency) ----------------------------------------------------

def load_state() -> dict:
    try:
        with open(STATE_PATH) as f:
            st = json.load(f)
        st.setdefault("processed", {})
        st.setdefault("last_run", "")
        return st
    except (FileNotFoundError, json.JSONDecodeError):
        return {"processed": {}, "last_run": ""}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=STATE_RETENTION_DAYS)).isoformat()
    state["processed"] = {k: v for k, v in state.get("processed", {}).items()
                          if (v or "") >= cutoff}
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


# ---- IMAP ------------------------------------------------------------------

def _connect_inbox():
    """Connect to the joaquin@ mailbox. Returns (imap, user) or (None, None)."""
    user = env("JOAQUIN_IMAP_USER") or env("INFOMANIAK_IMAP_USER")
    pw = env("JOAQUIN_IMAP_PASSWORD") or env("INFOMANIAK_IMAP_PASSWORD")
    host = env("JOAQUIN_IMAP_HOST") or env("INFOMANIAK_IMAP_HOST") or "mail.infomaniak.com"
    port = int(env("JOAQUIN_IMAP_PORT") or env("INFOMANIAK_IMAP_PORT") or 993)
    if not user or not pw:
        print("[inbox] IMAP creds missing (set JOAQUIN_IMAP_USER / JOAQUIN_IMAP_PASSWORD)")
        return None, None
    try:
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(user, pw)
        return imap, user
    except Exception as e:
        print(f"[inbox] IMAP login failed ({host}:{port}): {e}")
        return None, None


def _find_folder(list_lines, flag, names):
    """Find a folder by RFC 6154 special-use flag (e.g. '\\Sent'), else by name. Returns
    (name, sep) or (None, default_sep)."""
    parsed = [p for p in (_parse_list_line(l) for l in (list_lines or [])) if p]
    for p in parsed:
        if any(f.lower() == flag.lower() for f in p["flags"]):
            return p["name"], p["sep"]
    by = {p["name"]: p for p in parsed}
    for nm in names:
        if nm in by:
            return nm, by[nm]["sep"]
    return None, (parsed[0]["sep"] if parsed else "/")


def collect_answered_ids(imap, folders) -> set:
    """Message-IDs that already have a reply or draft: every <id> referenced via In-Reply-To
    or References across the Sent + Drafts folders. An incoming whose Message-ID is in here
    has already been answered (Sent) or already has a draft (Drafts) — skip it."""
    answered = set()
    for folder in folders:
        if not folder:
            continue
        try:
            typ, _ = imap.select(_q(folder), readonly=True)
            if typ != "OK":
                continue
            typ, data = imap.search(None, "ALL")
            if typ != "OK" or not data or not data[0]:
                continue
            nums = data[0].split()[-ANSWERED_SCAN_LIMIT:]
            for num in nums:
                t, d = imap.fetch(num, "(BODY.PEEK[HEADER.FIELDS (IN-REPLY-TO REFERENCES)])")
                if t != "OK" or not d or not d[0]:
                    continue
                raw = d[0][1]
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode("utf-8", "replace")
                for mid in re.findall(r"<[^>]+>", raw or ""):
                    answered.add(mid.strip())
        except Exception as e:
            print(f"[inbox] answered-scan {folder} failed: {e}")
    return answered


def fetch_slots(url: str, timeout: int = 8) -> list:
    """GET the Cockpit booking app's free slots (runs on the same VPS). Best-effort: any
    failure returns [] and the draft falls back to the booking link."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return collect_slots(r.json())
    except Exception as e:
        print(f"[inbox] slots fetch failed ({url}): {e}")
        return []


# ---- context ----------------------------------------------------------------

def gather_context(ns, p: dict, appointments_db: str):
    """Look up the sender in the Leads DB and any existing appointment. Read-only."""
    lead = appointment = None
    try:
        page = ns.find_lead_by_email_or_phone(email=p.get("from_email", ""))
        if page:
            lead = ns._extract_lead(page)
    except Exception as e:
        print(f"[inbox] lead lookup failed: {e}")
    if lead and appointments_db:
        try:
            lead_id = lead.get("page_id")
            for a in ns.list_appointments(appointments_db):
                if lead_id and lead_id in (a.get("lead_ids") or []):
                    appointment = a
                    break
        except Exception as e:
            print(f"[inbox] appointment lookup failed: {e}")
    return lead, appointment


def _notify(text: str) -> None:
    """Optional low-noise operator ping (off unless INBOX_DRAFTER_NOTIFY is truthy)."""
    if env("INBOX_DRAFTER_NOTIFY", "0") not in ("1", "true", "yes"):
        return
    tok = env("OPERATOR_TELEGRAM_BOT_TOKEN", "")
    chat = env("OPERATOR_TELEGRAM_CHAT_ID", "")
    if not (tok and chat):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": text, "disable_web_page_preview": True},
                      timeout=10)
    except Exception:
        pass


# ---- orchestration ----------------------------------------------------------

def run(*, dry_run=False, max_per_run=DEFAULT_MAX_PER_RUN, max_scan=DEFAULT_MAX_SCAN,
        since_days=DEFAULT_SINCE_DAYS, verbose=False) -> dict:
    import claude_client as cc          # lazy (pulls anthropic) — keeps module import light
    import notion_session as ns         # lazy (pulls requests/Notion)

    cfg = load_config()
    from_addr = env("JOAQUIN_FROM") or cfg.get("from") or "joaquin@automatisierbar.ch"
    booking_url = cfg.get("booking") or "https://cockpit.automatisierbar.ch/book"
    slots_url = env("BOOKING_SLOTS_URL") or "http://127.0.0.1:8082/api/book/slots"
    appointments_db = env("COCKPIT_APPOINTMENTS_DB_ID") or ""

    state = load_state()
    since_str = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%d-%b-%Y")

    imap, user = _connect_inbox()
    if not imap:
        print("[inbox] no IMAP connection — skipping (no-op).")
        return {"skipped": "no_imap"}

    sig = get_signature(cfg)
    print(f"[inbox] mailbox={user} signature={'ok(' + sig['source'] + ')' if sig else 'NONE'} "
          f"since={since_str} dry_run={dry_run}")

    counts = {"drafted": 0, "skipped_rule": 0, "skipped_irrelevant": 0,
              "skipped_dup": 0, "skipped_seen": 0, "failed": 0, "scanned": 0}
    try:
        typ, lines = imap.list()
        drafts_parent, dsep = pick_drafts_folder(lines)
        drafts_folder = build_target(
            drafts_parent or env("INFOMANIAK_DRAFTS_PARENT") or "Drafts", dsep, "")
        sent_folder, _ = _find_folder(lines, "\\Sent",
                                      ("Sent", "INBOX.Sent", "Sent Messages", "Gesendet"))
        answered = collect_answered_ids(imap, [sent_folder, drafts_folder])
        if verbose:
            print(f"[inbox] drafts={drafts_folder!r} sent={sent_folder!r} "
                  f"answered_ids={len(answered)}")

        typ, _ = imap.select("INBOX", readonly=True)   # readonly => never marks \Seen
        if typ != "OK":
            print("[inbox] cannot select INBOX")
            return {"skipped": "no_inbox"}
        typ, data = imap.search(None, "SINCE", since_str)
        nums = data[0].split() if typ == "OK" and data and data[0] else []
        nums = list(reversed(nums))   # newest first, so caps keep the freshest

        for num in nums:
            if counts["drafted"] >= max_per_run or counts["scanned"] >= max_scan:
                break
            t, d = imap.fetch(num, "(BODY.PEEK[])")
            if t != "OK" or not d or not d[0]:
                continue
            raw = d[0][1]
            if not isinstance(raw, (bytes, bytearray)):
                continue
            try:
                p = parse_incoming(raw)
            except Exception as e:
                print(f"[inbox] parse failed: {e}")
                continue

            mid = p.get("message_id", "")
            if mid and mid in state["processed"]:
                counts["skipped_seen"] += 1
                continue
            if mid and mid in answered:
                counts["skipped_dup"] += 1
                if verbose:
                    print(f"[skip-dup] {p['subject'][:60]} (already replied/drafted)")
                continue
            skip, reason = should_skip(p)
            if skip:
                counts["skipped_rule"] += 1
                if verbose:
                    print(f"[skip-rule:{reason}] {p['from_email']} | {p['subject'][:60]}")
                continue

            counts["scanned"] += 1
            cls = cc.classify_inbox_email(p["subject"], p["body_text"],
                                          from_name=p["from_name"], from_email=p["from_email"])
            if not cls["business_relevant"]:
                counts["skipped_irrelevant"] += 1
                if mid and not dry_run:
                    state["processed"][mid] = _now_iso()   # don't re-classify noise each run
                if verbose:
                    print(f"[skip-irrelevant] {p['subject'][:60]} ({cls['reason']})")
                continue

            lead, appointment = gather_context(ns, p, appointments_db)
            slots = (fetch_slots(slots_url)
                     if cls["category"] in ("appointment_booking", "appointment_reschedule")
                     else [])
            reply = cc.draft_inbox_reply(
                incoming=p, lead=lead, appointment=appointment, slots=slots,
                language=cls["reply_language"], category=cls["category"],
                booking_url=booking_url)
            if not reply or not reply.get("body"):
                counts["failed"] += 1
                print(f"[FAIL] empty draft for: {p['subject'][:60]}")
                continue

            subject = (reply.get("subject") or "").strip()
            if not _RE_PREFIX.match(subject):
                subject = build_re_subject(p["subject"])
            draft = {
                "company": (lead.get("firma") if lead else "") or "",
                "to": pick_to_address(p),
                "subject": subject,
                "body": strip_prose_dashes(reply["body"]),
            }
            msg = build_message(draft, from_addr, signature=sig,
                                in_reply_to=mid or None,
                                references=build_references(p) or None)
            tag = (f"[cat={cls['category']} lang={cls['reply_language']} "
                   f"conf={cls['confidence']:.2f} lead={'y' if lead else 'n'} slots={len(slots)}]")
            if dry_run:
                print("=" * 64)
                print(message_bytes(msg).decode("utf-8", "replace"))
                print(f"[dry] would draft -> {draft['to']} | {subject[:60]} {tag}")
                counts["drafted"] += 1
                continue
            try:
                t2, adata = imap.append(_q(drafts_folder), "(\\Draft)",
                                        imaplib.Time2Internaldate(time.time()), message_bytes(msg))
                if t2 != "OK":
                    raise RuntimeError(f"APPEND -> {t2} {adata}")
                if mid:
                    state["processed"][mid] = _now_iso()
                counts["drafted"] += 1
                print(f"[OK  ] draft -> {draft['to']} | {subject[:60]} {tag}")
            except Exception as e:
                counts["failed"] += 1
                print(f"[FAIL] append for {p['subject'][:60]}: {e}")

        if not dry_run:
            state["last_run"] = _now_iso()
            save_state(state)

        summary = (f"[inbox] drafted={counts['drafted']} "
                   f"skipped(rule={counts['skipped_rule']} irrelevant={counts['skipped_irrelevant']} "
                   f"dup={counts['skipped_dup']} seen={counts['skipped_seen']}) "
                   f"failed={counts['failed']} scanned={counts['scanned']} dry_run={dry_run}")
        print(summary)
        if not dry_run and (counts["drafted"] or counts["failed"]):
            _notify(f"📥 Inbox-Drafter: {counts['drafted']} Entwürfe erstellt, "
                    f"{counts['failed']} fehlgeschlagen")
        return counts
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def cmd_list_folders() -> int:
    imap, user = _connect_inbox()
    if not imap:
        return 2
    try:
        typ, lines = imap.list()
        print(f"--- folders ({user}) ---")
        for l in (lines or []):
            p = _parse_list_line(l)
            if p:
                print(f"  {p['name']}   (sep={p['sep']!r} flags={' '.join(p['flags'])})")
        dp, dsep = pick_drafts_folder(lines)
        sent, _ = _find_folder(lines, "\\Sent", ("Sent", "INBOX.Sent", "Sent Messages", "Gesendet"))
        print(f"--- drafts={build_target(dp or 'Drafts', dsep, '')!r}  sent={sent!r} ---")
        return 0
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="Draft replies to inbound business mail as Infomaniak IMAP drafts.")
    ap.add_argument("--dry-run", action="store_true", help="Build + print drafts, no mailbox writes / no state change")
    ap.add_argument("--max-per-run", type=int, default=DEFAULT_MAX_PER_RUN, help="Cap drafts created this run")
    ap.add_argument("--max-scan", type=int, default=DEFAULT_MAX_SCAN, help="Cap classify calls this run")
    ap.add_argument("--since-days", type=int, default=DEFAULT_SINCE_DAYS, help="INBOX lookback window (days)")
    ap.add_argument("--list-folders", action="store_true", help="Login + show folders/detection, then exit")
    ap.add_argument("--verbose", action="store_true", help="Per-message skip/draft logging")
    args = ap.parse_args()

    if args.list_folders:
        sys.exit(cmd_list_folders())

    run(dry_run=args.dry_run, max_per_run=args.max_per_run, max_scan=args.max_scan,
        since_days=args.since_days, verbose=args.verbose)


if __name__ == "__main__":
    main()
