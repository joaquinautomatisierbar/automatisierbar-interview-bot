"""Tests for the mail-sync CRM logger pure core (tools/mail_sync/).

Covers the offline-testable logic: the intent-tag taxonomy normaliser, the To/Cc-aware
message parser, the outbound skip gate, the dedup state ledger, and the LeadMail POST-body
builder. IMAP/HTTP/LLM glue is exercised separately via --dry-run integration.
"""
from __future__ import annotations

import email.message
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import types  # noqa: E402

from mail_sync import taxonomy, payload, imap_read  # noqa: E402
from mail_sync import state as mstate  # noqa: E402
from mail_sync import classify, hub_client  # noqa: E402

_SENTINEL = object()


def _raw(**kw) -> bytes:
    """Build a raw RFC 5322 message. Pass to="" to omit the To header entirely."""
    m = email.message.EmailMessage()
    m["From"] = kw.get("from_", "Lead Person <lead@kunde.ch>")
    to = kw.get("to", _SENTINEL)
    if to is _SENTINEL:
        m["To"] = "joaquin@automatisierbar.ch"
    elif to:
        m["To"] = to
    if kw.get("cc"):
        m["Cc"] = kw["cc"]
    m["Subject"] = kw.get("subject", "Re: Angebot")
    if kw.get("mid", _SENTINEL) is not _SENTINEL:
        if kw["mid"]:
            m["Message-ID"] = kw["mid"]
    else:
        m["Message-ID"] = "<abc@kunde.ch>"
    if kw.get("in_reply_to"):
        m["In-Reply-To"] = kw["in_reply_to"]
    if kw.get("references"):
        m["References"] = kw["references"]
    m["Date"] = kw.get("date", "Tue, 01 Jul 2026 09:30:00 +0200")
    m.set_content(kw.get("body", "Hallo, ja gerne. Passt Dienstag?"))
    return m.as_bytes()


# ─────────────────────────── taxonomy.normalize_intent ───────────────────────────

def test_normalize_valid_incoming_tag_passthrough():
    r = taxonomy.normalize_intent(
        {"intent_tag": "in_interesse", "confidence": 0.8, "reply_language": "de", "reason": "will Termin"},
        "incoming")
    assert r["intent_tag"] == "in_interesse"
    assert r["confidence"] == 0.8
    assert r["reply_language"] == "de"
    assert r["reason"] == "will Termin"


def test_normalize_unknown_tag_falls_back_to_direction_default():
    r = taxonomy.normalize_intent({"intent_tag": "garbage"}, "incoming")
    assert r["intent_tag"] == taxonomy.DEFAULT_INCOMING


def test_normalize_rejects_cross_direction_tag():
    # an outgoing tag returned for an incoming mail must not leak through
    r = taxonomy.normalize_intent({"intent_tag": "out_angebot"}, "incoming")
    assert r["intent_tag"] == taxonomy.DEFAULT_INCOMING


def test_normalize_outgoing_default_for_unknown():
    r = taxonomy.normalize_intent({"intent_tag": "nope"}, "outgoing")
    assert r["intent_tag"] == taxonomy.DEFAULT_OUTGOING


def test_normalize_clamps_confidence_high_and_bad():
    assert taxonomy.normalize_intent({"intent_tag": "in_absage", "confidence": 5}, "incoming")["confidence"] == 1.0
    assert taxonomy.normalize_intent({"intent_tag": "in_absage", "confidence": "x"}, "incoming")["confidence"] == 0.0


def test_normalize_language_defaults_to_de():
    assert taxonomy.normalize_intent({"intent_tag": "in_absage", "reply_language": "zz"}, "incoming")["reply_language"] == "de"
    assert taxonomy.normalize_intent({"intent_tag": "in_absage", "reply_language": "EN"}, "incoming")["reply_language"] == "en"


# ─────────────────────────── imap_read.parse_full ───────────────────────────

def test_parse_full_extracts_to_and_cc():
    p = imap_read.parse_full(_raw(to="A <a@kunde.ch>", cc="B <b@kunde.ch>, c@kunde.ch"))
    assert p["to_email"] == "a@kunde.ch"
    assert "b@kunde.ch" in p["cc"] and "c@kunde.ch" in p["cc"]


def test_parse_full_keeps_incoming_fields():
    p = imap_read.parse_full(_raw(mid="<m1@kunde.ch>", in_reply_to="<orig@x>"))
    assert p["message_id"] == "<m1@kunde.ch>"
    assert p["in_reply_to"] == "<orig@x>"
    assert p["from_email"] == "lead@kunde.ch"


# ─────────────────────────── imap_read.should_skip_outbound ───────────────────────────

def test_outbound_to_external_lead_not_skipped():
    p = imap_read.parse_full(_raw(from_="joaquin@automatisierbar.ch", to="lead@kunde.ch"))
    skip, _ = imap_read.should_skip_outbound(p)
    assert skip is False


def test_outbound_to_internal_team_skipped():
    p = imap_read.parse_full(_raw(from_="joaquin@automatisierbar.ch", to="tej@automatisierbar.ch"))
    skip, reason = imap_read.should_skip_outbound(p)
    assert skip is True


def test_outbound_external_cc_counts_as_recipient():
    p = imap_read.parse_full(_raw(from_="joaquin@automatisierbar.ch",
                                  to="tej@automatisierbar.ch", cc="lead@kunde.ch"))
    skip, _ = imap_read.should_skip_outbound(p)
    assert skip is False


def test_outbound_no_recipient_skipped():
    p = imap_read.parse_full(_raw(from_="joaquin@automatisierbar.ch", to=""))
    skip, reason = imap_read.should_skip_outbound(p)
    assert skip is True


# ─────────────────────────── payload ───────────────────────────

def test_external_message_id_uses_message_id():
    p = imap_read.parse_full(_raw(mid="<x@kunde.ch>"))
    assert payload.external_message_id(p, "joaquin", "INBOX") == "<x@kunde.ch>"


def test_external_message_id_falls_back_to_stable_hash():
    eid1 = payload.external_message_id(imap_read.parse_full(_raw(mid="")), "joaquin", "INBOX")
    eid2 = payload.external_message_id(imap_read.parse_full(_raw(mid="")), "joaquin", "INBOX")
    assert eid1.startswith("sha1:")
    assert eid1 == eid2


def test_build_payload_incoming_shape():
    p = imap_read.parse_full(_raw(from_="Lead <lead@kunde.ch>", to="joaquin@automatisierbar.ch",
                                  subject="Re: Angebot", references="<a@x> <b@y>", in_reply_to="<b@y>"))
    intent = {"intent_tag": "in_interesse", "confidence": 0.9, "reason": "Termin", "reply_language": "de"}
    body = payload.build_leadmail_payload(p, direction="incoming", mailbox="joaquin", folder="INBOX", intent=intent)
    assert body["direction"] == "incoming"
    assert body["fromEmail"] == "lead@kunde.ch"
    assert body["toEmail"] == "joaquin@automatisierbar.ch"
    assert body["intentTag"] == "in_interesse"
    assert body["inReplyTo"] == "<b@y>"
    assert body["references"] == ["<a@x>", "<b@y>"]
    assert body["subject"] == "Re: Angebot"
    assert body["sentAt"].startswith("2026-07-01T")
    assert body["mailbox"] == "joaquin"


def test_build_payload_outgoing_counterparty_is_recipient():
    p = imap_read.parse_full(_raw(from_="joaquin@automatisierbar.ch", to="Lead <lead@kunde.ch>"))
    intent = {"intent_tag": "out_angebot", "confidence": 0.7, "reason": "", "reply_language": "de"}
    body = payload.build_leadmail_payload(p, direction="outgoing", mailbox="joaquin", folder="Sent", intent=intent)
    assert body["fromEmail"] == "joaquin@automatisierbar.ch"
    assert body["toEmail"] == "lead@kunde.ch"
    assert body["intentTag"] == "out_angebot"


# ─────────────────────────── state ledger ───────────────────────────

def test_state_roundtrip(tmp_path):
    st = mstate.load_state("joaquin", base_dir=str(tmp_path))
    assert st["processed"] == {}
    mstate.mark_seen(st, "<m1@x>")
    assert mstate.is_seen(st, "<m1@x>")
    mstate.save_state(st, "joaquin", base_dir=str(tmp_path))
    st2 = mstate.load_state("joaquin", base_dir=str(tmp_path))
    assert mstate.is_seen(st2, "<m1@x>")


def test_state_path_is_per_mailbox(tmp_path):
    assert mstate.state_path("tej", base_dir=str(tmp_path)).endswith("mail-sync-state.tej.json")
    assert mstate.state_path("nico", base_dir=str(tmp_path)) != mstate.state_path("tej", base_dir=str(tmp_path))


# ─────────────────────────── classify (fail-safe) ───────────────────────────

def test_classify_mail_intent_failsafe_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = classify.classify_mail_intent(direction="incoming", subject="x", body="y")
    assert r["intent_tag"] == taxonomy.DEFAULT_INCOMING
    assert r["confidence"] == 0.0


def test_classify_mail_intent_outgoing_failsafe(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = classify.classify_mail_intent(direction="outgoing", subject="x", body="y")
    assert r["intent_tag"] == taxonomy.DEFAULT_OUTGOING


# ─────────────────────────── hub_client (retry) ───────────────────────────

def test_hub_client_retries_then_succeeds():
    calls = {"n": 0}

    def transport(url, headers, body):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("boom")
        return types.SimpleNamespace(status=201, body={"matched": True})

    res = hub_client.post_leadmail({"externalMessageId": "<m>"}, base_url="http://h", api_key="k",
                                   transport=transport, max_attempts=3, sleep=lambda s: None)
    assert res.ok is True
    assert calls["n"] == 3


def test_hub_client_gives_up_after_max_attempts():
    def transport(url, headers, body):
        raise ConnectionError("down")

    res = hub_client.post_leadmail({"externalMessageId": "<m>"}, base_url="http://h", api_key="k",
                                   transport=transport, max_attempts=2, sleep=lambda s: None)
    assert res.ok is False


def test_hub_client_does_not_retry_client_error():
    calls = {"n": 0}

    def transport(url, headers, body):
        calls["n"] += 1
        return types.SimpleNamespace(status=400, body={"error": "bad"})

    res = hub_client.post_leadmail({"externalMessageId": "<m>"}, base_url="http://h", api_key="k",
                                   transport=transport, max_attempts=3, sleep=lambda s: None)
    assert res.ok is False
    assert calls["n"] == 1  # a 400 is terminal — no retry storm
