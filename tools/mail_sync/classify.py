"""Classify one mail's intent with Claude Haiku.

OUTGOING mail is classified for OUR intent; INCOMING mail for the counterparty's response.
Mirrors tools/claude_client.classify_inbox_email: Haiku, ephemeral prompt cache, JSON out,
fails SAFE (returns the direction's default tag with confidence 0.0 on any error / missing key)
so a classification failure never mislabels a lead. anthropic + claude_client are imported
lazily so this module stays importable offline (tests, dry parsing).
"""
from __future__ import annotations

import os

from mail_sync import taxonomy

MODEL_CLASSIFY = "claude-haiku-4-5-20251001"  # kept local so import stays offline-safe

_JSON_HINT = ('Antworte NUR als gültiges JSON (kein Markdown): '
              '{"intent_tag": "<schlüssel>", "confidence": 0.0-1.0, '
              '"reply_language": "de|en|fr", "reason": "kurz, max 1 Satz"}')


def _menu(tags: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in tags.items())


_SYSTEM_INCOMING = f"""\
Du triagierst eine ANTWORT, die ein Lead oder Kunde an automatisierbar.ch (Schweizer KI-/
Automatisierungsberatung für KMU) geschickt hat. Bestimme die Absicht der Antwort.

Wähle GENAU EINEN intent_tag (gib nur den Schlüssel zurück, nicht das Label):
{_menu(taxonomy.INCOMING_TAGS)}

Richtlinien:
- in_interesse: sagt zu, will einen Termin, fragt aktiv nach einem Gespräch, klar positiv.
- in_rueckfrage: hat eine inhaltliche Frage / will mehr Infos, bevor er weitergeht.
- in_preis: fragt konkret nach Preis, Kosten oder Konditionen.
- in_absage: kein Interesse, Absage, "bitte nicht mehr kontaktieren", klar negativ.
- in_spaeter: grundsätzlich offen, aber jetzt nicht, später/vertagt.
- in_abwesenheit: automatische Abwesenheits-/Out-of-Office-Antwort, kein Mensch.
- in_sonstiges: geschäftlich, aber keine der obigen Kategorien.

confidence: 0.0-1.0, wie sicher du beim Tag bist.
reply_language: Sprache der Antwortmail (de/en/fr), Default de.

{_JSON_HINT}"""


_SYSTEM_OUTGOING = f"""\
Du klassifizierst eine E-Mail, die das Team von automatisierbar.ch SELBST an einen Lead oder
Kunden gesendet hat. Bestimme die Absicht UNSERER Mail.

Wähle GENAU EINEN intent_tag (gib nur den Schlüssel zurück, nicht das Label):
{_menu(taxonomy.OUTGOING_TAGS)}

Richtlinien:
- out_erstkontakt: allererste Kontaktaufnahme mit diesem Kontakt.
- out_followup: Nachfassen / Erinnerung nach vorheriger Nachricht ohne Antwort.
- out_terminvorschlag: schlägt konkrete Termine / ein Gespräch vor.
- out_angebot: enthält ein Angebot, eine Offerte oder Preise.
- out_rueckfrage_beantwortet: beantwortet eine Frage des Kontakts.
- out_reaktivierung: reaktiviert einen länger inaktiven / kalten Kontakt.

confidence: 0.0-1.0. reply_language: Sprache der Mail (de/en/fr), Default de.

{_JSON_HINT}"""


def _system_for(direction: str) -> str:
    return _SYSTEM_OUTGOING if direction == "outgoing" else _SYSTEM_INCOMING


def classify_mail_intent(*, direction: str, subject: str, body: str,
                         from_name: str = "", from_email: str = "", to_email: str = "",
                         model: str = MODEL_CLASSIFY) -> dict:
    """Return {intent_tag, confidence, reply_language, reason} for one mail. Fails SAFE."""
    safe = taxonomy.normalize_intent({}, direction)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return safe
    try:
        import anthropic
        from claude_client import _parse_json

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        who = (f"Von: {from_name} <{from_email}>\n" if direction == "incoming"
               else f"An: {to_email}\n")
        user = f"{who}Betreff: {subject}\n\nNachrichtentext:\n{(body or '')[:6000]}"
        msg = client.messages.create(
            model=model,
            max_tokens=300,
            system=[{"type": "text", "text": _system_for(direction),
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        d = _parse_json(msg.content[0].text)
        return taxonomy.normalize_intent(d, direction)
    except Exception as e:  # noqa: BLE001
        print(f"[mail-classify:{direction}] error={e!r}", flush=True)
        return safe
