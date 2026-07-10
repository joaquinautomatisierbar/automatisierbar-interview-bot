"""AI synthesis for the vRv discovery tool.

Three entry points, all deliberately narrow (no per-answer round-trips):
- suggest_followups(chapter_id, state): one Sonnet call, 2-4 suggestions, [] on failure
- generate_brief(state): German Offerten-Brief.md (8 fixed sections, grounded)
- generate_spec(state): English prototype build spec (mirrors the proven
  generate_claude_code_prompt section discipline from tools/claude_client.py)

The route layer runs generate_* in a background thread and persists status via
vrv.store (2 gunicorn workers: state lives on disk, never in process memory).
"""
import json
import os
import re
from datetime import datetime, timezone

import anthropic

from claude_client import MODEL_FAST, _complete_with_continuation
from vrv import catalog

MEETING_DATE = "05.08.2026"
CLIENT_NAME = "vR verwaltungen ag"


def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _all_questions(state):
    """Catalog questions + custom questions from state, catalog order first."""
    custom = [
        {
            "id": q["id"], "chapter": q["chapter"], "text": q["text"],
            "type": "text", "why_it_matters": "Vor Ort ergänzte Frage",
            "maps_to_offer_section": (catalog.chapter_by_id(q["chapter"]) or {}).get(
                "offer_section", ""),
            "priority": q.get("priority", "nice"), "client_visible": False,
        }
        for q in state.get("custom_questions", [])
    ]
    return list(catalog.QUESTIONS) + custom


def _answer_line(q, row):
    parts = [f"[{q['id']}] {q['text']}"]
    value = (row or {}).get("value", "").strip()
    client_value = (row or {}).get("client_value", "").strip()
    note = (row or {}).get("note", "").strip()
    status = (row or {}).get("status", "open")
    if value:
        parts.append(f"  Antwort ({(row or {}).get('source', 'prep')}): {value}")
    if client_value:
        parts.append(f"  Vorab-Antwort des Kunden: {client_value}")
    if note:
        parts.append(f"  Interne Notiz: {note}")
    if not value and not client_value:
        parts.append(f"  Antwort: KEINE ANGABE (Status: {status})")
    return "\n".join(parts)


def _answers_by_section(state):
    """Group all Q&A into offer sections, preserving catalog order."""
    answers = state.get("answers", {})
    sections = {}
    order = []
    for q in _all_questions(state):
        section = q["maps_to_offer_section"]
        if section not in sections:
            sections[section] = []
            order.append(section)
        sections[section].append(_answer_line(q, answers.get(q["id"])))
    return "\n\n".join(
        f"### {section}\n" + "\n".join(lines) for section, lines in
        ((s, sections[s]) for s in order)
    )


def _open_musts(state):
    answers = state.get("answers", {})
    done = {"answered", "skipped"}
    out = []
    for q in _all_questions(state):
        if q["priority"] != "must":
            continue
        status = (answers.get(q["id"]) or {}).get("status", "open")
        if status not in done:
            out.append(f"- [{q['id']}] {q['text']}")
    return "\n".join(out) or "- keine, alle Muss-Fragen sind beantwortet oder bewusst übersprungen"


# ---------------------------------------------------------------------------
# Follow-up suggestions (one call per chapter, optional)
# ---------------------------------------------------------------------------

_SYSTEM_FOLLOWUPS = """Du bist Discovery-Coach für ein Schweizer Automatisierungs-Team im Verkaufsgespräch mit einer Immobilienverwaltung (Order2Cash-Digitalisierung, pebeFinance, Microsoft 365, Hauswart-App).

Du erhältst die Fragen und bisherigen Antworten EINES Kapitels. Schlage 2 bis 4 präzise Folgefragen vor, die aus den konkreten Antworten entstehen (Lücken, Widersprüche, überraschende Details). Keine Wiederholung bereits gestellter Fragen, keine Allgemeinplätze.

Antworte NUR mit einem JSON-Array, kein anderer Text:
[{"text": "Die Folgefrage, direkt stellbar", "why": "1 Satz, warum sie sich aus den Antworten ergibt"}]"""


def suggest_followups(chapter_id, state):
    """2-4 follow-up suggestions for one chapter. Returns [] on any failure."""
    chapter = catalog.chapter_by_id(chapter_id)
    if chapter is None:
        return []
    answers = state.get("answers", {})
    lines = [
        _answer_line(q, answers.get(q["id"]))
        for q in _all_questions(state) if q["chapter"] == chapter_id
    ]
    try:
        message = _client().messages.create(
            model=MODEL_FAST,
            max_tokens=1200,
            system=[{
                "type": "text",
                "text": _SYSTEM_FOLLOWUPS,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{
                "role": "user",
                "content": f"Kapitel {chapter_id}: {chapter['title']}\n\n" + "\n\n".join(lines),
            }],
        )
        raw = message.content[0].text if message.content else ""
        match = re.search(r"\[.*\]", raw, re.S)
        if not match:
            return []
        parsed = json.loads(match.group(0))
        out = []
        for item in parsed[:4]:
            text = str(item.get("text", "")).strip()
            why = str(item.get("why", "")).strip()
            if text:
                out.append({"text": text[:500], "why": why[:300]})
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Offerten-Brief.md (German)
# ---------------------------------------------------------------------------

_SYSTEM_BRIEF = """Du schreibst den internen Offerten-Brief nach dem Discovery-Termin bei der vR verwaltungen ag (Immobilienverwaltung, Personalvorsorge, Hauswartung, Treuhand; Solothurn). Der Brief ist die Arbeitsgrundlage für die Offerte des Teams Automatisierbar.

HARTE REGELN:
1. Verwende AUSSCHLIESSLICH die gelieferten Antworten. Erfinde nichts, keine Zahlen, keine Systemnamen, keine Annahmen als Fakten.
2. Jede übernommene Aussage trägt ihre Herkunft in Klammern, z.B. "(Frage b3)".
3. Wo Information fehlt, schreibe wörtlich "Keine Angabe" plus die Fragen-ID.
4. Sie-Form, sachliches Schweizer Hochdeutsch, keine Gedankenstriche (verwende Komma, Doppelpunkt oder Punkt).
5. Der Abschnitt "8. Offene Punkte vor Offertstellung" übernimmt die gelieferte Liste offener Muss-Fragen vollständig; du darfst zusätzlich aus den Antworten entstandene Klärungspunkte ergänzen, klar als solche markiert.
6. Struktur EXAKT (Markdown, ## je Abschnitt):

# Offerten-Brief: vR verwaltungen ag
(Metadaten: Datum des Briefs, Termin 05.08.2026, Quelle: Discovery-Tool)

## 1. Ausgangslage und Zielsetzung
## 2. Ist-Analyse Order2Cash
## 3. Soll-Konzept pebeFinance/M365
## 4. Mobile Lösung Hauswarte
## 5. Verrechnung und Reporting
## 6. Rahmenbedingungen (IT, Sicherheit, Compliance)
## 7. Vorgehen und Projektorganisation
## 8. Offene Punkte vor Offertstellung

Schreibe dicht und konkret: lieber wenige belegte Sätze als Füllprosa."""


def generate_brief(state):
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    user_text = (
        f"Briefdatum: {today}. Termin: {MEETING_DATE} bei {CLIENT_NAME}.\n\n"
        f"## Erfasste Fragen und Antworten (nach Offerten-Kapitel gruppiert)\n\n"
        f"{_answers_by_section(state)}\n\n"
        f"## Zusätzliche freie Notizen\n{state.get('extra_notes') or 'keine'}\n\n"
        f"## Offene Muss-Fragen (deterministisch ermittelt, vollständig in Abschnitt 8 übernehmen)\n"
        f"{_open_musts(state)}\n"
    )
    return _complete_with_continuation(
        _client(),
        model=MODEL_FAST,
        user_text=user_text,
        system=[{
            "type": "text",
            "text": _SYSTEM_BRIEF,
            "cache_control": {"type": "ephemeral"},
        }],
        max_tokens=8000,
        label="vrv_brief",
    )


# ---------------------------------------------------------------------------
# Prototyp-Spec.md (English, mirrors generate_claude_code_prompt discipline)
# ---------------------------------------------------------------------------

_SYSTEM_SPEC = """You write a prototype build spec from discovery-interview answers. The client is vR verwaltungen ag (Swiss property management, own caretaker/Hauswart team, pension fund administration, Treuhand; runs pebeFinance accounting, Microsoft 365). The builder is Automatisierbar (custom web platforms, PWAs, n8n, Anthropic API).

HARD RULES (same discipline as our production build prompts):
- Ground every statement in the provided answers; client field names and terms are ground truth, copy them verbatim.
- NO placeholders like TBD. Where the interview left something open, either mark a sensible default with "(MVP default — confirm with client)" or list it under "Open Clarification Points".
- Name exact tools and services (e.g. "pebeFinance CSV Buchungsimport", "Microsoft Graph API", specific n8n nodes) instead of generic phrases.
- Contradictions or missing load-bearing facts go to "Open Clarification Points", phrased as direct questions.
- Output is ONE markdown document, structure EXACTLY:

# Prototype Build Spec — <concrete name derived from the answers>
## Client
## Goal
## Current Process (As-Is)
(numbered: "Step N: who → action (tool; input→output; automation potential)")
## Prototype Scope (In / Out)
## Trigger
## Services & Auth
## Input Data Schema
## Business Logic
## Output & Actions
## Error Handling
## Volume & Timing
## MVP Assumptions
## Open Clarification Points
## Build Instructions
(numbered; end with a test plan of 3 concrete payloads)

Final line, verbatim: "Build this as a clickable prototype plus n8n workflow skeleton. Start with a working MVP. Flag any credentials or config the client needs to provide." """


def generate_spec(state):
    user_text = (
        f"Discovery answers from the {MEETING_DATE} on-site meeting at {CLIENT_NAME}, "
        f"grouped by offer section. Unanswered questions say KEINE ANGABE.\n\n"
        f"{_answers_by_section(state)}\n\n"
        f"## Free-form notes\n{state.get('extra_notes') or 'none'}\n\n"
        f"## Still-open must questions\n{_open_musts(state)}\n"
    )
    return _complete_with_continuation(
        _client(),
        model=MODEL_FAST,
        user_text=user_text,
        system=[{
            "type": "text",
            "text": _SYSTEM_SPEC,
            "cache_control": {"type": "ephemeral"},
        }],
        max_tokens=8000,
        label="vrv_spec",
    )
