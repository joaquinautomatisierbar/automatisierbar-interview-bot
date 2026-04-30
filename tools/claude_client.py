"""claude_client.py — Claude API calls for the automatisierbar survey app."""

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
7. ZEIT & VOLUMEN: Wie viele Stunden/Woche verbringt der Klient aktuell mit diesem Prozess? Wie viele Datensätze/Vorgänge pro Tag oder Woche?

WENN alle 7 Punkte klar sind → status: "complete"
WENN Lücken bestehen → stelle max. 6 gezielte Fragen, nur was wirklich fehlt.

WICHTIG zu Punkt 7: Die Zeitangabe MUSS vom Klienten kommen — niemals schätzen oder erfinden.
Frage konkret: "Wie viele Stunden pro Woche verbringen Sie oder Ihr Team aktuell mit diesem Prozess?"
Frage konkret: "Wie viele [Rechnungen / Anfragen / Einträge] bearbeiten Sie pro Tag oder Woche?"

Für technische Details die der Klient nicht kennen kann (z.B. genaue Datenbankstruktur):
Mache sinnvolle MVP-Annahmen und liste sie unter "assumptions".
Beispiel: "Für den MVP verwenden wir Google Sheets statt der internen Datenbank."

ROI-Schätzung bei complete: Basiere AUSSCHLIESSLICH auf den vom Klienten genannten Zahlen.
Berechnung: Stunden/Woche × 4.3 × CHF 80/h = CHF/Monat Einsparung.
Nach Automation: ca. 15–30 Minuten/Woche für Monitoring (keine Schätzung, immer 15 Min als Standard).

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
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return json.loads(m.group())


def _format_qa(all_qa: list) -> str:
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
                "1. Automatisierungs-Ziel\n2. Auslöser (Trigger)\n3. Dienste & Zugangsdaten\n"
                "4. Eingehende Daten (Schema)\n5. Geschäftslogik & Regeln\n6. Ausgabe & Aktionen\n"
                "7. Fehlerbehandlung\n8. Volumen & Timing\n9. MVP-Annahmen\n\n"
                f"KONTEXT:\n{context}\n\nANTWORTEN:\n{qa_text}\n\n"
                "Schreibe auf Deutsch. Sei präzise und technisch — ein Entwickler muss danach sofort loslegen können."
            ),
        }],
    )
    return message.content[0].text


def generate_claude_code_prompt(
    context: str,
    all_qa: list,
    roi: dict,
    lead_info: dict = None,
) -> str:
    """Generate a ready-to-paste Claude Code prompt from the collected session data."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    qa_text = _format_qa(all_qa)

    lead_section = ""
    if lead_info:
        parts = []
        if lead_info.get("name"):            parts.append(f"Contact: {lead_info['name']}")
        if lead_info.get("firma"):           parts.append(f"Company: {lead_info['firma']}")
        if lead_info.get("branche"):         parts.append(f"Industry: {lead_info['branche']}")
        if lead_info.get("groesse"):         parts.append(f"Size: {lead_info['groesse']}")
        if lead_info.get("problem_cluster"): parts.append(f"Problem cluster: {lead_info['problem_cluster']}")
        if lead_info.get("top_problem"):     parts.append(f"Top problem (from CRM): {lead_info['top_problem']}")
        lead_section = "\n".join(parts)

    roi_section = ""
    if roi:
        roi_section = (
            f"Process: {roi.get('process', '')}\n"
            f"Time now: {roi.get('hours_per_week_now', '')} h/week → "
            f"{roi.get('minutes_per_week_after', '')} min/week after automation\n"
            f"Monthly savings: CHF {roi.get('chf_monthly_savings', '')}\n"
            f"Complexity: {roi.get('complexity', '')}\n"
            f"Build time estimate: {roi.get('build_time_days', '')}"
        )

    message = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": (
                "You are writing a Claude Code prompt that a developer will paste into Claude Code. "
                "Claude Code will then build the n8n workflow end-to-end without asking the developer any questions.\n\n"
                "Write in English. Use ONLY the data provided below. Use exact tool names, field names, "
                "thresholds, and Tagesangaben from the Q&A — never abstract them.\n\n"
                "STRUCTURE — exactly these sections:\n"
                "# Automation Build Spec — <ConcreteProcessName>\n"
                "## Client\n  one paragraph: company, industry, size, the problem this solves\n"
                "## Goal\n  one sentence with measurable outcome (e.g. 'Cut Mahnungsversand from 3h/week to 15min/week')\n"
                "## Trigger\n  exact n8n trigger node + config (e.g. 'Schedule Trigger, daily 08:00 Europe/Zurich')\n"
                "## Services & Auth\n  list every external service: n8n node name → credential type → required scopes\n"
                "## Input Data Schema\n  JSON example with the user's actual field names and example values\n"
                "## Business Logic\n  numbered IF/THEN rules with concrete thresholds from the Q&A\n"
                "## Output & Actions\n  for each output: target system, payload mapping, recipient\n"
                "## Error Handling\n  retry policy + failure notification target (concrete addresses/channels)\n"
                "## Volume & Timing\n  records/day from Q&A, peak burst, latency tolerance\n"
                "## MVP Assumptions\n  list every assumption explicitly. If a fact wasn't in the Q&A, "
                "PICK A SENSIBLE DEFAULT and label it '(MVP default — confirm with client)'.\n"
                "## Build Instructions\n  numbered steps a developer follows: 1) Create credential X, 2) Add node Y with config Z, "
                "3) Wire to node W, ... End with a test plan: 3 sample payloads (happy path, edge case, failure).\n\n"
                "HARD RULES:\n"
                "- NEVER write 'To be defined', 'TBD', 'not specified', 'request from client', or any placeholder. "
                "  If data is missing, pick a concrete MVP default (Gmail OAuth2, Google Sheets, daily 08:00, "
                "  retry 3× exponential backoff, notify the contact's email) and mark '(MVP default — confirm with client)'.\n"
                "- Use exact n8n node names: 'Schedule Trigger', 'HTTP Request', 'Gmail', 'Google Sheets', 'IF', 'Set', etc.\n"
                "- Reference the user's actual field names from the Q&A (e.g. 'Rechnungsnummer', 'Fälligkeitsdatum'), not generic 'field_1'.\n"
                "- Max ~200 lines total. Be tight, not verbose.\n\n"
                "End with this exact line (and nothing after it):\n"
                "'Build this as an n8n workflow. Start with a working MVP. Flag any credentials or config the client needs to provide.'\n\n"
                f"=== CLIENT INFO ===\n{lead_section or '(no lead linked — use generic placeholder values from MVP defaults)'}\n\n"
                f"=== ORIGINAL CONTEXT ===\n{context}\n\n"
                f"=== COLLECTED Q&A ===\n{qa_text}\n\n"
                f"=== ROI ESTIMATE ===\n{roi_section or '(not yet calculated)'}"
            ),
        }],
    )
    return message.content[0].text
