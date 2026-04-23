"""claude_client.py — Claude API calls for the automatisierbar survey app.

Two main functions:
  evaluate_context(context)        → questions for round 1
  evaluate_answers(context, all_qa) → next questions OR complete + ROI

Uses prompt caching on system prompts to reduce latency and cost.
"""

import json
import os
import re
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"

# ---------------------------------------------------------------------------
# System prompts (cached)
# ---------------------------------------------------------------------------

_SYSTEM_EVALUATE_CONTEXT = """\
Du bist Automatisierungsexperte bei automatisierbar.ch (Schweizer n8n-Automatisierungsberatung).

AUFGABE: Analysiere die Situationsbeschreibung und generiere einen Fragebogen.

ZIEL: Die gesammelten Antworten müssen einem Entwickler (oder Claude Code) erlauben,
eine vollständige n8n-Automatisierung zu bauen — ohne jede weitere Rückfrage.

WENN die Beschreibung mehrere Prozesse enthält oder kein klarer Prozess erkennbar ist:
Generiere 3–5 Fragen zur Prozessauswahl (Quick Win):
- Welcher Prozess kostet am meisten Zeit pro Woche?
- Wie oft / wie viele Datensätze pro Tag?
- Welche Tools bereits im Einsatz?

WENN ein einzelner klarer Prozess und mindestens ein Tool erkennbar sind:
Generiere sofort technische Implementierungsfragen zu: Auslöser, Dienste & Zugänge,
Eingehende Daten, Logik & Regeln, Ausgabe & Aktionen, Fehler & Volumen.

Fragen müssen nach konkreten Werten fragen:
- Tool-Namen: nicht "E-Mail-Dienst" → "Gmail, Outlook oder anderes?"
- Feldnamen mit Beispielwerten: "Welche Spalten hat das Sheet? z.B. Mieter, Betrag, Datum"
- Zeitpläne mit Uhrzeit: "Täglich um welche Uhrzeit?"
- Geschäftsregeln mit Zahlen: "Ab wie vielen Tagen gilt eine Zahlung als überfällig?"
- Authentifizierungstypen: "OAuth2, API-Key oder Service Account?"

Antworte NUR als gültiges JSON (kein Markdown, kein Text davor/danach):
{
  "status": "needs_process_selection" | "needs_technical_detail",
  "questions": [
    { "id": "q1", "text": "...", "type": "text" },
    { "id": "q2", "text": "...", "type": "choice", "options": ["Option A", "Option B"] }
  ]
}
Maximal 8 Fragen. Mindestens 3.\
"""

_SYSTEM_EVALUATE_ANSWERS = """\
Du bist Automatisierungsexperte bei automatisierbar.ch (Schweizer n8n-Automatisierungsberatung).

AUFGABE: Prüfe ob alle Informationen vorhanden sind, um eine vollständige n8n-Automatisierung zu bauen.

VOLLSTÄNDIGKEITS-CHECKLISTE — prüfe jeden Punkt:
1. AUSLÖSER: Was startet die Automation? (Webhook-URL, Schedule mit Uhrzeit, E-Mail-Eingang, etc.)
2. DIENSTE: Welche Tools/APIs? (exakte Namen, Auth-Typ, Zugangsdaten vorhanden?)
3. INPUT-DATEN: Genaue Felder mit Typen und Beispielwerten (z.B. { name: "Müller", betrag: 1200 })
4. LOGIK: Alle IF/THEN-Regeln, Berechnungen, Filterkriterien mit konkreten Schwellwerten
5. OUTPUT: Was soll passieren? Wohin? Mit welchem genauen Inhalt/Format?
6. FEHLER: Retry? Benachrichtigung? Wer wird informiert?

WENN alle 6 Punkte klar sind → status: "complete"
WENN Lücken bestehen → stelle max. 6 gezielte Fragen, nur was wirklich fehlt.

Für technische Details die der Klient nicht kennen kann (z.B. genaue Datenbankstruktur):
Mache sinnvolle MVP-Annahmen und liste sie unter "assumptions".
Beispiel: "Für den MVP verwenden wir Google Sheets statt der internen Datenbank."

ROI-Schätzung bei complete: Schätze konservativ aber realistisch.
Basiere auf: Häufigkeit × Zeitaufwand pro Durchgang → Stunden/Woche → CHF/Monat bei 80 CHF/h.

Antworte NUR als gültiges JSON (kein Markdown, kein Text davor/danach):

Bei needs_more:
{
  "status": "needs_more",
  "questions": [
    { "id": "q1", "text": "...", "type": "text" }
  ],
  "assumptions": []
}

Bei complete:
{
  "status": "complete",
  "assumptions": ["Für den MVP verwenden wir Google Sheets statt Bexio.", "..."],
  "roi": {
    "process": "Automatischer Mahnungsversand per E-Mail",
    "hours_per_week_now": 5,
    "minutes_per_week_after": 15,
    "chf_hourly_rate": 80,
    "chf_monthly_savings": 1560,
    "complexity": "easy",
    "build_time_days": "2–3"
  }
}\
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    """Extract JSON from Claude response (handles markdown code blocks)."""
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return json.loads(m.group())


def _format_qa(all_qa: list) -> str:
    """Format collected Q&A rounds for the Claude prompt."""
    parts = []
    for round_data in all_qa:
        parts.append(f"=== Runde {round_data['round']} ===")
        for item in round_data.get("qa", []):
            parts.append(f"Frage: {item.get('question', '')}")
            parts.append(f"Antwort: {item.get('answer', '')}")
            parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_context(context: str) -> dict[str, Any]:
    """
    Analyse the initial context and return round 1 questions.

    Returns:
        {
            "status": "needs_process_selection" | "needs_technical_detail",
            "questions": [{"id": "q1", "text": "...", "type": "text"|"choice", "options": [...]}]
        }
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=[{
            "type": "text",
            "text": _SYSTEM_EVALUATE_CONTEXT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": f"Situationsbeschreibung:\n\n{context}",
        }],
    )
    return _parse_json(message.content[0].text)


def evaluate_answers(context: str, all_qa: list) -> dict[str, Any]:
    """
    Given all Q&A collected so far, decide what's still needed or mark complete.

    Returns needs_more:
        {"status": "needs_more", "questions": [...], "assumptions": [...]}

    Returns complete:
        {"status": "complete", "assumptions": [...], "roi": {...}}
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    qa_text = _format_qa(all_qa)
    user_content = (
        f"URSPRÜNGLICHER KONTEXT:\n{context}\n\n"
        f"BISHER GESAMMELTE ANTWORTEN:\n{qa_text}"
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=[{
            "type": "text",
            "text": _SYSTEM_EVALUATE_ANSWERS,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )
    return _parse_json(message.content[0].text)


def generate_spec_summary(context: str, all_qa: list) -> str:
    """
    Generate a structured build spec as text, suitable for Claude Code input.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    qa_text = _format_qa(all_qa)
    message = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": (
                "Erstelle eine vollständige Automatisierungs-Spezifikation basierend auf diesen Informationen.\n\n"
                "Formatiere sie als strukturiertes Dokument mit diesen Abschnitten:\n"
                "1. Automatisierungs-Ziel\n"
                "2. Auslöser (Trigger)\n"
                "3. Dienste & Zugangsdaten\n"
                "4. Eingehende Daten (Schema)\n"
                "5. Geschäftslogik & Regeln\n"
                "6. Ausgabe & Aktionen\n"
                "7. Fehlerbehandlung\n"
                "8. Volumen & Timing\n"
                "9. MVP-Annahmen\n\n"
                f"KONTEXT:\n{context}\n\n"
                f"ANTWORTEN:\n{qa_text}\n\n"
                "Schreibe auf Deutsch. Sei präzise und technisch — ein Entwickler muss danach sofort loslegen können."
            ),
        }],
    )
    return message.content[0].text
