"""Build the POST /api/v1/leadmails body from a parsed message + classification.

Pure + deterministic so it's fully unit-tested. The Hub consumes this body: it resolves the
lead by the counterparty address (fromEmail for incoming, toEmail for outgoing) or thread
linkage, dedups on externalMessageId, and maps intentTag -> CRM-state action itself.
"""
from __future__ import annotations

import hashlib
import re
from email.utils import parsedate_to_datetime

_ID_RE = re.compile(r"<[^>]+>")


def external_message_id(p: dict, mailbox: str, folder: str) -> str:
    """A stable dedup key. The RFC Message-ID when present, else a sha1: fallback over the
    immutable identifying fields so the same message always hashes the same on re-scan."""
    mid = (p.get("message_id") or "").strip()
    if mid:
        return mid
    basis = "\x1f".join([
        mailbox or "", folder or "",
        (p.get("from_email") or ""), (p.get("to_email") or ""),
        (p.get("subject") or ""), (p.get("date") or ""),
    ])
    return "sha1:" + hashlib.sha1(basis.encode("utf-8", "replace")).hexdigest()


def _sent_at_iso(p: dict):
    raw = (p.get("date") or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        return dt.isoformat() if dt is not None else None
    except Exception:
        return None


def build_leadmail_payload(p: dict, *, direction: str, mailbox: str, folder: str, intent: dict) -> dict:
    """Assemble the LeadMail POST body. `direction` is 'incoming' | 'outgoing'; `intent` is a
    normalized classify result (intent_tag/confidence/reply_language/reason)."""
    intent = intent or {}
    return {
        "mailbox": mailbox,
        "direction": direction,
        "externalMessageId": external_message_id(p, mailbox, folder),
        "inReplyTo": (p.get("in_reply_to") or "").strip() or None,
        "references": _ID_RE.findall(p.get("references") or ""),
        "fromName": p.get("from_name") or "",
        "fromEmail": p.get("from_email") or "",
        "toName": p.get("to_name") or "",
        "toEmail": p.get("to_email") or "",
        "cc": list(p.get("cc") or []),
        "subject": p.get("subject") or "",
        "body": p.get("body_text") or "",
        "sentAt": _sent_at_iso(p),
        "intentTag": intent.get("intent_tag") or "",
        "confidence": intent.get("confidence", 0.0),
        "replyLanguage": intent.get("reply_language") or "de",
        "reason": intent.get("reason") or "",
    }
