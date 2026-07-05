"""IMAP read helpers for the mail-sync CRM logger.

REUSES the battle-tested pure helpers from tools/inbox_reply_drafter.py (parse_incoming,
should_skip, _connect_inbox, _find_folder, _q) — importing them rather than duplicating, so the
live drafter stays the single source of that logic. Adds what the CRM logger needs on top:
To/Cc extraction (an outbound mail's recipient is the counterparty we match to a lead), Sent
folder detection, an outbound skip gate, and a read-only INBOX/Sent message iterator.
"""
from __future__ import annotations

import email
import email.policy
import os
import sys
from email.utils import getaddresses

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

# stdlib-only underneath — safe to import offline (see inbox_reply_drafter header).
from inbox_reply_drafter import (  # noqa: E402
    parse_incoming, should_skip, _connect_inbox, _find_folder, _dh, _q,
)

SELF_DOMAIN = "automatisierbar.ch"
SENT_FLAG = "\\Sent"
SENT_NAMES = ("Sent", "INBOX.Sent", "Sent Messages", "Sent Items", "Gesendet", "Gesendete Objekte")
_MAX_FETCH = 400  # hard cap on messages fetched per folder per run


def _addrs(raw: str):
    """[(display-name, email-lowercased)] for a header value; junk/blank addresses dropped."""
    out = []
    for nm, addr in getaddresses([raw or ""]):
        addr = (addr or "").lower().strip()
        if addr and "@" in addr:
            out.append((_dh(nm).strip(), addr))
    return out


def parse_full(raw: bytes) -> dict:
    """parse_incoming(raw) + To/Cc extraction. Adds:
      to_email  – first To address (the counterparty for an outbound mail)
      to_name   – first To display name
      to        – [all To addresses]
      cc        – [all Cc addresses]
    """
    p = parse_incoming(raw)
    m = email.message_from_bytes(raw, policy=email.policy.default)
    tos = _addrs(str(m.get("To", "")))
    ccs = _addrs(str(m.get("Cc", "")))
    p["to"] = [a for _, a in tos]
    p["to_name"] = tos[0][0] if tos else ""
    p["to_email"] = tos[0][1] if tos else ""
    p["cc"] = [a for _, a in ccs]
    return p


def should_skip_outbound(p: dict, self_domain: str = SELF_DOMAIN):
    """Cheap gate for a mail we SENT (Sent folder). Returns (skip: bool, reason: str).

    We only log outbound mail that actually went to an external counterparty (a lead/client).
    Purely-internal team mail and mail with no recipient at all are dropped."""
    recipients = list(p.get("to") or []) + list(p.get("cc") or [])
    recipients = [a for a in recipients if a and "@" in a]
    if not recipients:
        return True, "no-recipient"
    external = [a for a in recipients if a.rsplit("@", 1)[-1].lower() != self_domain.lower()]
    if not external:
        return True, "internal-only"
    return False, ""


# ---- IMAP iteration (IO — integration-tested via --dry-run) -----------------

def find_sent_folder(list_lines):
    """The Sent folder name from an IMAP LIST response (RFC 6154 \\Sent flag, else by name)."""
    name, _ = _find_folder(list_lines, SENT_FLAG, SENT_NAMES)
    return name


def fetch_parsed_since(imap, folder: str, since_str: str, cap: int = _MAX_FETCH):
    """Yield parse_full(dict) for messages in `folder` since `since_str` (IMAP date, e.g.
    '01-Jul-2026'), newest first, up to `cap`. Read-only SELECT + BODY.PEEK so nothing is
    marked \\Seen. Bad/undecodable messages are skipped."""
    if not folder:
        return
    typ, _ = imap.select(_q(folder), readonly=True)
    if typ != "OK":
        return
    typ, data = imap.search(None, "SINCE", since_str)
    if typ != "OK" or not data or not data[0]:
        return
    nums = list(reversed(data[0].split()))[:cap]  # newest first, capped
    for num in nums:
        t, d = imap.fetch(num, "(BODY.PEEK[])")
        if t != "OK" or not d or not d[0]:
            continue
        rawmsg = d[0][1]
        if not isinstance(rawmsg, (bytes, bytearray)):
            continue
        try:
            yield parse_full(rawmsg)
        except Exception as e:  # noqa: BLE001 — one bad message must not stop the run
            print(f"[mail-sync] parse failed in {folder}: {e}", flush=True)
            continue
