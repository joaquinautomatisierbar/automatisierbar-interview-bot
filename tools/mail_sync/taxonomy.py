"""Intent-tag taxonomy for the mail-sync CRM logger.

Every mail carries exactly one intent tag. OUTGOING tags describe OUR intent (the mail we sent);
INCOMING tags describe the counterparty's response. The stable ASCII keys below travel over the
wire in the LeadMail POST body and MUST stay in lock-step with the Hub's
packages/shared/src/mail-intent.ts (same keys, same German labels). The Hub owns the
tag -> CRM-state-delta + risk mapping; this side only classifies + validates the tag.
"""
from __future__ import annotations

# key -> German display label (shown in the Hub Badge; also the human hint in the classify prompt)
OUTGOING_TAGS = {
    "out_erstkontakt": "Erstkontakt",
    "out_followup": "Follow-up / Nachfassen",
    "out_terminvorschlag": "Terminvorschlag",
    "out_angebot": "Angebot / Offerte",
    "out_rueckfrage_beantwortet": "Rückfrage beantwortet",
    "out_reaktivierung": "Reaktivierung",
}

INCOMING_TAGS = {
    "in_interesse": "Interesse / Terminwunsch",
    "in_rueckfrage": "Rückfrage / Info gewünscht",
    "in_preis": "Preis / Konditionen",
    "in_absage": "Absage / Kein Interesse",
    "in_spaeter": "Später / Vertagt",
    "in_abwesenheit": "Abwesenheit / Auto-Reply",
    "in_sonstiges": "Sonstiges",
}

# neutral fallbacks when the model returns nothing usable
DEFAULT_INCOMING = "in_sonstiges"
DEFAULT_OUTGOING = "out_followup"

_LANGS = ("de", "en", "fr")


def tags_for(direction: str) -> dict:
    """The valid tag set for a direction ('incoming' | 'outgoing')."""
    return OUTGOING_TAGS if direction == "outgoing" else INCOMING_TAGS


def default_tag(direction: str) -> str:
    return DEFAULT_OUTGOING if direction == "outgoing" else DEFAULT_INCOMING


def normalize_intent(raw: dict, direction: str) -> dict:
    """Coerce a raw classifier dict into a safe, validated result.

    Returns {intent_tag, confidence, reply_language, reason}. An unknown or cross-direction
    tag falls back to the direction default; confidence is clamped to [0,1] (non-numeric -> 0.0);
    reply_language is one of de/en/fr (default de); reason is trimmed.
    """
    raw = raw or {}
    valid = tags_for(direction)
    tag = str(raw.get("intent_tag", "")).strip()
    if tag not in valid:
        tag = default_tag(direction)

    try:
        conf = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
    except (TypeError, ValueError):
        conf = 0.0

    lang = str(raw.get("reply_language", "de")).lower().strip()[:2]
    if lang not in _LANGS:
        lang = "de"

    return {
        "intent_tag": tag,
        "confidence": conf,
        "reply_language": lang,
        "reason": str(raw.get("reason", ""))[:300],
    }
