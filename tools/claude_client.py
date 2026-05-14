"""claude_client.py — Claude API calls for the automatisierbar survey app."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"       # reserved (not currently used at runtime — Render's 30s gunicorn timeout would kill it)
MODEL_FAST = "claude-sonnet-4-6"  # used for all interactive endpoints (round eval, prompt, spec)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# ---------------------------------------------------------------------------
# Shared rule for both evaluator prompts: never trap the user in MC.
# ---------------------------------------------------------------------------

_FRAGE_TYP_REGEL = """\
FRAGE-TYPEN (WICHTIG):
- Standard ist `type: "text"`. Nutze freitext, wann immer Freitext mehr Information liefert.
- `type: "choice"` nur wenn 2–4 Optionen wirklich >90% der Antworten abdecken
  (z.B. Auth-Typ: OAuth2 / API-Key / Service Account).
- Bei JEDER `choice`-Frage MUSS die letzte Option `"Andere…"` sein, damit der Klient
  immer einen Freitext-Ausweg hat.
- Niemals den Klienten in eine Multiple-Choice einzwängen, wenn du nicht sicher bist."""


# ---------------------------------------------------------------------------
# System prompts (cached)
# ---------------------------------------------------------------------------

_SYSTEM_EVALUATE_CONTEXT = f"""\
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

{_FRAGE_TYP_REGEL}

Antworte NUR als gültiges JSON (kein Markdown, kein Text davor/danach):
{{
  "status": "needs_process_selection" | "needs_technical_detail",
  "questions": [
    {{ "id": "q1", "text": "...", "type": "text" }},
    {{ "id": "q2", "text": "...", "type": "choice", "options": ["Option A", "Option B", "Andere…"] }}
  ]
}}
Maximal 8 Fragen. Mindestens 3.\
"""

_SYSTEM_EVALUATE_ANSWERS = f"""\
Du bist Automatisierungsexperte bei automatisierbar.ch (Schweizer n8n-Automatisierungsberatung).

AUFGABE: Prüfe ob alle Informationen vorhanden sind, um eine vollständige n8n-Automatisierung zu bauen.

VOLLSTÄNDIGKEITS-CHECKLISTE — prüfe jeden Punkt:
1. AUSLÖSER: Was startet die Automation? (Webhook-URL, Schedule mit Uhrzeit, E-Mail-Eingang, etc.)
2. DIENSTE: Welche Tools/APIs? (exakte Namen, Auth-Typ, Zugangsdaten vorhanden?)
3. INPUT-DATEN: Genaue Felder mit Typen und Beispielwerten (z.B. {{ name: "Müller", betrag: 1200 }})
4. LOGIK: Alle IF/THEN-Regeln, Berechnungen, Filterkriterien mit konkreten Schwellwerten
5. OUTPUT: Was soll passieren? Wohin? Mit welchem genauen Inhalt/Format?
6. FEHLER: Retry? Benachrichtigung? Wer wird informiert?
7. ZEIT & VOLUMEN: Wie viele Stunden/Woche verbringt der Klient aktuell mit diesem Prozess? Wie viele Datensätze/Vorgänge pro Tag oder Woche?

PROZESS-MAP NUTZUNG:
Wenn der Klient eine Prozess-Map (Ist-Zustand A→Z) ausgefüllt hat, MUSST du jede neue Frage
an einen konkreten Schritt verankern: "In Schritt 3 (Sarah lädt Excel hoch) — welches Format
hat die Datei genau?". Frage NICHT mehr abstrakt nach Tools/Daten, wenn die Prozess-Map
diese Info schon liefert.

DATEIEN & EXTRAS:
Der Sidebar-Block (DATEIEN, ZUSÄTZLICHE NOTIZEN) ist Teil der Antworten — wenn dort eine
Excel-Spaltenliste oder ein Screenshot-Auszug steht, behandle ihn als gegebene Information.
Frage nicht erneut nach Spaltennamen, die in der Excel-Vorschau bereits sichtbar sind.

STATUS-ENTSCHEIDUNG (kritisch):

Drei mögliche Status — wähle den passenden:

(A) "needs_more" — fehlt noch Information.
    - Setze, wenn entweder der Prozess noch nicht klar gewählt ist (mehrere Prozesse genannt,
      keiner herausgestochen), ODER wenn die technischen Details unvollständig sind.
    - Stelle bis zu 6 gezielte Fragen.

(B) "ready_for_process_map" — Prozess ist gewählt + Haupttools bekannt, ABER die Prozess-Map
    ist noch leer (PROZESS-MAP-Block fehlt im Kontext).
    - Setze NUR, wenn die Prozess-Map noch nicht ausgefüllt ist UND du jetzt einen klaren
      Prozess + mindestens 2 Tools identifiziert hast.
    - Gib `process_name` (kurzer Name des gewählten Prozesses) und `tools_identified`
      (Array der bisher genannten Tools) zurück.
    - Lieber eine Runde mehr Fragen als die falsche Prozesswahl: wenn du unsicher bist,
      welcher Prozess gemeint ist, bleibe bei "needs_more" und frage konkret nach.

(C) "complete" — alle 7 Punkte der Checkliste klar UND Prozess-Map ist ausgefüllt
    (PROZESS-MAP-Block ist im Kontext mit ≥2 Schritten).
    - Niemals "complete" setzen, solange die Prozess-Map leer ist — selbst wenn die
      Q&A alle 7 Punkte abdeckt.

WICHTIG zu Punkt 7: Die Zeitangabe MUSS vom Klienten kommen — niemals schätzen oder erfinden.
Frage konkret: "Wie viele Stunden pro Woche verbringen Sie oder Ihr Team aktuell mit diesem Prozess?"
Frage konkret: "Wie viele [Rechnungen / Anfragen / Einträge] bearbeiten Sie pro Tag oder Woche?"

Für technische Details die der Klient nicht kennen kann (z.B. genaue Datenbankstruktur):
Mache sinnvolle MVP-Annahmen und liste sie unter "assumptions".
Beispiel: "Für den MVP verwenden wir Google Sheets statt der internen Datenbank."

{_FRAGE_TYP_REGEL}

ROI-SCHÄTZUNG bei complete (V3: ZWEI-BAR HONEST ROI — Pflicht):

Basiere AUSSCHLIESSLICH auf den vom Klienten genannten Zahlen.

Zerlege die Zeit nach Automation in ZWEI Komponenten:

(A) `minutes_per_week_machine_after` — System-Durchlaufzeit (was n8n/Tools übernehmen
    pro Woche, ohne Mensch). Standard: 15 Min/Woche für Monitoring.

(B) `minutes_per_week_human_after` — Verbleibender MENSCHLICHER Aufwand (Review,
    Freigaben, Eskalationen, Sonderfälle). MUSS > 0 sein wenn der Prozess einen
    Pflicht-Review oder eine menschliche Freigabe enthält. Sei konservativ:
    lieber Stunden als Minuten wenn realistisch.

Berechnung:
- `minutes_per_week_human_after` = Σ(units_per_week × minutes_per_unit) für jeden
  Review/Freigabe-Schritt aus der Prozess-Map oder Q&A.
- `chf_monthly_savings` = (hours_per_week_now − (machine + human)/60) × 4.3 × chf_hourly_rate.
- Wenn `chf_monthly_savings` < 0 → komm bei complete NICHT raus; setze
  status=needs_more und frag nach realistischeren Zahlen.

`human_residual_breakdown` — listet die Annahmen hinter (B) transparent:
ein Array von Objekten {{task, units_per_week, minutes_per_unit}}. Pflicht wenn (B) > 15.

VERBOTEN:
- `minutes_per_week_human_after` auf 0 setzen, wenn die Prozess-Map einen
  Review-Schritt hat oder die Q&A "Pflicht-Sichtkontrolle" / "Freigabe" / "Eskalation" erwähnt.
- Eine ROI-Zahl ausgeben, die suggeriert "48h → 15 Min" ohne ehrliche Mensch-Restzeit.
- Sich auf den Klienten verlassen, dass er die Restzeit kennt — DU rechnest sie aus
  Volumen × angenommener Prüfzeit/Einheit.

Antworte NUR als gültiges JSON (kein Markdown, kein Text davor/danach):

Bei needs_more:
{{
  "status": "needs_more",
  "questions": [
    {{ "id": "q1", "text": "...", "type": "text" }}
  ],
  "assumptions": []
}}

Bei ready_for_process_map:
{{
  "status": "ready_for_process_map",
  "process_name": "Mahnungsversand für überfällige Rechnungen",
  "tools_identified": ["Bexio", "Outlook 365", "Google Sheets"],
  "assumptions": []
}}

Bei complete (V3 two-bar ROI schema):
{{
  "status": "complete",
  "assumptions": ["Für den MVP verwenden wir Google Sheets statt Bexio.", "..."],
  "roi": {{
    "process": "Automatischer Mahnungsversand per E-Mail",
    "hours_per_week_now": 12,
    "minutes_per_week_machine_after": 15,
    "minutes_per_week_human_after": 75,
    "human_residual_breakdown": [
      {{"task": "Pflicht-Sichtkontrolle pro Beleg", "units_per_week": 150, "minutes_per_unit": 0.5}}
    ],
    "chf_hourly_rate": 80,
    "chf_monthly_savings": 3608,
    "complexity": "medium",
    "build_time_days": "4-6"
  }}
}}

WICHTIG zur Backwards-Compat:
- Lege `minutes_per_week_after` IMMER ZUSÄTZLICH bei (= machine + human, in Minuten).
  Das ist nur für altes Frontend-Display — V3-UI nutzt machine_after + human_after separat.\
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


def _format_process_map(process_map: list, notes: str = "") -> str:
    if not process_map:
        return ""
    lines = ["=== PROZESS-MAP (Ist-Zustand A→Z) ==="]
    for i, step in enumerate(process_map, start=1):
        lines.append(
            f"Schritt {step.get('step', i)}: "
            f"{step.get('who', '?')} → {step.get('action', '?')} "
            f"(Tool: {step.get('tool', '?')}; "
            f"in: {step.get('data_in', '–')} → out: {step.get('data_out', '–')}; "
            f"automatisierbar: {step.get('automatable', 'partial')})"
        )
    if notes:
        lines.append(f"\nNotizen: {notes}")
    return "\n".join(lines)


def _format_attachments(attachments: list) -> str:
    if not attachments:
        return ""
    parts = ["=== DATEIEN (vom Klienten hochgeladen) ==="]
    for a in attachments:
        name = a.get("filename", "datei")
        kind = a.get("kind", "text")
        text = a.get("extracted_text", "")
        parts.append(f"\n--- {name} [{kind}] ---\n{text}")
    return "\n".join(parts)


def _format_extras(extra_context: str) -> str:
    if not (extra_context or "").strip():
        return ""
    return f"=== ZUSÄTZLICHE NOTIZEN (Sidebar) ===\n{extra_context.strip()}"


def _format_assumptions(assumptions: list) -> str:
    """Format the identified MVP assumptions so the spec generator can paste
    them verbatim into the `## MVP Assumptions` section instead of inventing new ones."""
    if not assumptions:
        return ""
    lines = ["=== IDENTIFIZIERTE MVP-ANNAHMEN (aus Q&A — wortgleich übernehmen) ==="]
    for a in assumptions:
        if not a:
            continue
        lines.append(f"- {a}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _build_user_message(
    *,
    context: str,
    all_qa: list = None,
    process_map: list = None,
    process_map_notes: str = "",
    process_map_skipped: bool = False,
    extra_context: str = "",
    attachments: list = None,
    assumptions: list = None,
) -> str:
    """Compose the user-side message block, including only sections that have content."""
    blocks = [f"URSPRÜNGLICHER KONTEXT:\n{context}"]
    pm = _format_process_map(process_map or [], process_map_notes)
    if pm:
        blocks.append(pm)
    elif process_map_skipped:
        # User saw the process-map screen but skipped — don't re-trigger ready_for_process_map.
        blocks.append(
            "=== PROZESS-MAP (Ist-Zustand A→Z) ===\n"
            "(Vom Klienten übersprungen — keine strukturierte Map vorhanden. "
            "Nutze die Q&A und Kontext als einzige Quelle für den Ist-Zustand. "
            "Frage NICHT erneut nach der Prozess-Map.)"
        )
    ex = _format_extras(extra_context)
    if ex:
        blocks.append(ex)
    at = _format_attachments(attachments or [])
    if at:
        blocks.append(at)
    if all_qa:
        blocks.append(f"BISHER GESAMMELTE ANTWORTEN:\n{_format_qa(all_qa)}")
    asm = _format_assumptions(assumptions or [])
    if asm:
        blocks.append(asm)
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Long-form generation with stop_reason="max_tokens" continuation loop.
# Used by generate_spec_summary + generate_claude_code_prompt so long specs
# (> max_tokens) get assembled across multiple calls instead of being truncated
# mid-sentence. Emits a stats line per call so future cutoffs stay visible.
# ---------------------------------------------------------------------------

_CONTINUATION_NUDGE = (
    "Bitte fahre genau dort fort wo du aufgehört hast — keine Wiederholung, "
    "kein neuer Anfang, kein 'Fortsetzung:' Prefix. Direkt weiterschreiben."
)


def _complete_with_continuation(
    client: anthropic.Anthropic,
    *,
    model: str,
    user_text: str,
    system: list = None,
    max_tokens: int = 8000,
    max_continuations: int = 3,
    label: str = "generate",
) -> str:
    """Run messages.create; on stop_reason == 'max_tokens', send the partial
    assistant text back with a continuation nudge until the model stops naturally
    or we hit `max_continuations`. Returns the concatenated text."""
    messages: list = [{"role": "user", "content": user_text}]
    full_text = ""
    total_input = 0
    total_output = 0
    continuations = 0
    final_stop = "end_turn"
    final_chunk_len = 0

    for _ in range(max_continuations + 1):
        kwargs = {"model": model, "max_tokens": max_tokens, "messages": list(messages)}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        chunk = resp.content[0].text if resp.content else ""
        full_text += chunk
        final_chunk_len = len(chunk)
        try:
            total_input += int(getattr(resp.usage, "input_tokens", 0) or 0)
            total_output += int(getattr(resp.usage, "output_tokens", 0) or 0)
        except Exception:
            pass
        final_stop = getattr(resp, "stop_reason", None) or "unknown"
        if final_stop != "max_tokens":
            break
        continuations += 1
        # Build the continuation: append assistant's partial + nudge user.
        messages.append({"role": "assistant", "content": chunk})
        messages.append({"role": "user", "content": _CONTINUATION_NUDGE})

    print(
        f"[claude-stats] label={label} stop_reason={final_stop} "
        f"continuations={continuations} input_tokens={total_input} "
        f"output_tokens={total_output} chars={len(full_text)} "
        f"last_chunk_chars={final_chunk_len}",
        flush=True,
    )
    return full_text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_context(
    context: str,
    *,
    extra_context: str = "",
    attachments: list = None,
) -> dict[str, Any]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_content = _build_user_message(
        context=context,
        extra_context=extra_context,
        attachments=attachments,
    )
    message = client.messages.create(
        model=MODEL_FAST,
        max_tokens=2000,
        system=[{
            "type": "text",
            "text": _SYSTEM_EVALUATE_CONTEXT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )
    return _parse_json(message.content[0].text)


def evaluate_answers(
    context: str,
    all_qa: list,
    *,
    process_map: list = None,
    process_map_notes: str = "",
    process_map_skipped: bool = False,
    extra_context: str = "",
    attachments: list = None,
) -> dict[str, Any]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_content = _build_user_message(
        context=context,
        all_qa=all_qa,
        process_map=process_map,
        process_map_notes=process_map_notes,
        process_map_skipped=process_map_skipped,
        extra_context=extra_context,
        attachments=attachments,
    )
    message = client.messages.create(
        model=MODEL_FAST,
        max_tokens=2000,
        system=[{
            "type": "text",
            "text": _SYSTEM_EVALUATE_ANSWERS,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )
    return _parse_json(message.content[0].text)


def classify_process_map_automatability(
    process_map: list,
    *,
    context: str = "",
) -> list[dict]:
    """Classify each step in the process map as yes/partial/no automatable.
    Single Sonnet call, deterministic JSON array output.
    Returns [{step: int, automatable: "yes"|"partial"|"no", reason: str}, ...]
    or [] if classification fails (caller falls back to "partial" for all).
    """
    if not process_map:
        return []
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    pm_text = _format_process_map(process_map)
    msg = client.messages.create(
        model=MODEL_FAST,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": (
                "Klassifiziere für jeden Prozess-Schritt unten, wie gut er sich automatisieren "
                "lässt — als n8n-Workflow oder ähnliche Tools.\n\n"
                "Kriterien:\n"
                "- 'yes': Vollständig automatisierbar via API/Regel (Datentransfer, Schwellwert-Check, "
                "  Templating, Notification).\n"
                "- 'partial': Grossteils automatisierbar, aber Mensch wird für eine Entscheidung oder "
                "  einen Edge-Case in der Schleife gebraucht (Review-Schritt, Sonderfälle).\n"
                "- 'no': Nicht sinnvoll automatisierbar — kritische Entscheidung, Verhandlung, "
                "  Kreativarbeit, sensibler Kundenkontakt.\n\n"
                f"KONTEXT: {context[:500]}\n\n"
                f"{pm_text}\n\n"
                "Antworte NUR als gültiges JSON-Array (kein Markdown, kein Text davor/danach):\n"
                '[{"step": 1, "automatable": "yes", "reason": "kurze deutsche Begründung, max. 80 Zeichen"}]\n\n'
                "Genau ein Objekt pro Schritt, in der Reihenfolge der Prozess-Map. Die Begründung "
                "soll dem Klienten beim Verständnis helfen, nicht technisch sein."
            ),
        }],
    )
    text = msg.content[0].text
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        return []
    try:
        parsed = json.loads(m.group())
        if not isinstance(parsed, list):
            return []
        # Sanitize each entry — normalize automatable values to allowed set
        out = []
        for i, entry in enumerate(parsed, start=1):
            if not isinstance(entry, dict):
                continue
            auto = str(entry.get("automatable", "partial")).lower()
            if auto not in ("yes", "partial", "no"):
                auto = "partial"
            out.append({
                "step": int(entry.get("step") or i),
                "automatable": auto,
                "reason": str(entry.get("reason", ""))[:200],
            })
        return out
    except Exception:
        return []


def extract_process_map_draft(
    context: str,
    *,
    attachments: list = None,
    extra_context: str = "",
    all_qa: list = None,
) -> dict:
    """V3 P1.4 — Extract a draft process-map from the client's free narrative.

    Reads the customer's prose (and any uploaded files / round 1 answers if present)
    and returns a structured `process_map` they then REVIEW/CORRECT on screen
    instead of filling from scratch. Lower friction, fewer empty rows.

    Returns:
        {
          "steps": [{"step": 1, "who": "...", "action": "...", "tool": "...",
                     "data_in": "...", "data_out": "..."}, ...],
          "confidence": "high" | "medium" | "low",
          "missing": ["unknown step between scan and upload", ...]
        }
    On any failure: `{"steps": [], "confidence": "low", "missing": []}` so the
    frontend can fall back to an empty review form.
    """
    if not (context or "").strip():
        return {"steps": [], "confidence": "low", "missing": []}

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_content = _build_user_message(
        context=context,
        all_qa=all_qa or [],
        extra_context=extra_context,
        attachments=attachments,
    )
    system_prompt = (
        "Du bist Automatisierungsexperte bei automatisierbar.ch.\n\n"
        "AUFGABE: Lies die freie Erzählung des Klienten und extrahiere die einzelnen "
        "Schritte des aktuellen (Ist-Zustand) Prozesses. Erfinde NICHTS. Wenn ein "
        "Schritt unklar ist, lass das entsprechende Feld leer und notiere die "
        "Unklarheit unter `missing`.\n\n"
        "Felder pro Schritt:\n"
        "- `who`: Person/Rolle/System, das den Schritt ausführt (z.B. 'Andrea', 'Mandant', 'Bexio').\n"
        "- `action`: Was passiert (kurzer Verbsatz, deutsch).\n"
        "- `tool`: Konkretes Tool (Gmail, Bexio, Excel, Telefon, persönlich, etc.).\n"
        "- `data_in`: Was reinkommt (PDF, E-Mail, Anruf, vorheriger Schritt-Output).\n"
        "- `data_out`: Was rausgeht (Eintrag in Bexio, E-Mail versendet, Status-Update).\n\n"
        "Confidence:\n"
        "- 'high': Erzählung beschreibt 3+ Schritte klar mit Akteur+Tool.\n"
        "- 'medium': Schritte erkennbar aber Akteure oder Tools fehlen.\n"
        "- 'low': Erzählung zu vage, weniger als 2 Schritte erkennbar.\n\n"
        "Antworte NUR als gültiges JSON (kein Markdown davor/danach):\n"
        '{\n'
        '  "steps": [\n'
        '    {"step": 1, "who": "Andrea", "action": "Empfängt Belege per Mail", '
        '"tool": "Outlook", "data_in": "Mail mit PDF", "data_out": "Beleg in Posteingang"}\n'
        '  ],\n'
        '  "confidence": "high|medium|low",\n'
        '  "missing": ["kurze Beschreibung was unklar war"]\n'
        '}'
    )
    try:
        msg = client.messages.create(
            model=MODEL_FAST,
            max_tokens=1500,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_content}],
        )
        parsed = _parse_json(msg.content[0].text)
        # Sanitize
        steps = []
        for i, s in enumerate(parsed.get("steps", []) or [], start=1):
            if not isinstance(s, dict):
                continue
            steps.append({
                "step": int(s.get("step") or i),
                "who": str(s.get("who", ""))[:200],
                "action": str(s.get("action", ""))[:500],
                "tool": str(s.get("tool", ""))[:200],
                "data_in": str(s.get("data_in", ""))[:300],
                "data_out": str(s.get("data_out", ""))[:300],
            })
        confidence = parsed.get("confidence", "medium")
        if confidence not in ("high", "medium", "low"):
            confidence = "medium"
        missing = [str(m)[:200] for m in (parsed.get("missing") or []) if m]
        if not steps:
            confidence = "low"
        return {"steps": steps, "confidence": confidence, "missing": missing}
    except Exception as e:
        print(f"[claude-stats] label=extract_process_map_draft error={e!r}", flush=True)
        return {"steps": [], "confidence": "low", "missing": []}


def generate_spec_summary(
    context: str,
    all_qa: list,
    *,
    process_map: list = None,
    process_map_notes: str = "",
    process_map_skipped: bool = False,
    extra_context: str = "",
    attachments: list = None,
    assumptions: list = None,
) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_content = _build_user_message(
        context=context,
        all_qa=all_qa,
        process_map=process_map,
        process_map_notes=process_map_notes,
        process_map_skipped=process_map_skipped,
        extra_context=extra_context,
        attachments=attachments,
        assumptions=assumptions,
    )
    return _complete_with_continuation(
        client,
        model=MODEL_FAST,
        max_tokens=8000,
        label="spec_summary",
        user_text=(
            "Erstelle eine vollständige Automatisierungs-Spezifikation basierend auf diesen Informationen.\n\n"
            "Formatiere sie als strukturiertes Dokument mit diesen Abschnitten:\n"
            "1. Automatisierungs-Ziel\n"
            "2. Aktueller Prozess (Ist-Zustand) — als nummerierte Liste, eine Zeile pro Schritt\n"
            "3. Auslöser (Trigger)\n"
            "4. Dienste & Zugangsdaten\n"
            "5. Eingehende Daten (Schema)\n"
            "6. Geschäftslogik & Regeln\n"
            "7. Ausgabe & Aktionen\n"
            "8. Fehlerbehandlung\n"
            "9. Volumen & Timing\n"
            "10. MVP-Annahmen — falls der IDENTIFIZIERTE-MVP-ANNAHMEN-Block unten existiert, "
            "übernimm jeden Punkt WORTGLEICH. Ergänze nur echte Lücken; erfinde keine eigenen "
            "Defaults wenn der Klient zu einem Punkt schon eine Aussage gemacht hat.\n\n"
            f"{user_content}\n\n"
            "Schreibe auf Deutsch. Sei präzise und technisch — ein Entwickler muss danach sofort loslegen können."
        ),
    )


def generate_claude_code_prompt(
    context: str,
    all_qa: list,
    roi: dict,
    lead_info: dict = None,
    *,
    process_map: list = None,
    process_map_notes: str = "",
    process_map_skipped: bool = False,
    extra_context: str = "",
    attachments: list = None,
    assumptions: list = None,
) -> str:
    """Generate a ready-to-paste Claude Code prompt from the collected session data."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

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

    payload = _build_user_message(
        context=context,
        all_qa=all_qa,
        process_map=process_map,
        process_map_notes=process_map_notes,
        process_map_skipped=process_map_skipped,
        extra_context=extra_context,
        attachments=attachments,
        assumptions=assumptions,
    )

    return _complete_with_continuation(
        client,
        model=MODEL_FAST,
        max_tokens=8000,
        label="claude_code_prompt",
        user_text=(
            "You are writing a Claude Code prompt that a developer will paste into Claude Code. "
            "Claude Code will then build the n8n workflow end-to-end without asking the developer any questions.\n\n"
            "Write in English. Use ONLY the data provided below. Use exact tool names, field names, "
            "thresholds, and Tagesangaben from the Q&A and process map — never abstract them.\n\n"
            "STRUCTURE — exactly these sections, in this order:\n"
            "# Automation Build Spec — <ConcreteProcessName>\n"
            "## Client\n  one paragraph: company, industry, size, the problem this solves\n"
            "## Goal\n  one sentence with measurable outcome (e.g. 'Cut Mahnungsversand from 3h/week to 15min/week')\n"
            "## Current Process (As-Is)\n"
            "  Numbered list, one line per step, format: 'Step N: <who> → <action> (tool: <tool>; in: <data_in> → out: <data_out>; auto: <yes|partial|no>)'.\n"
            "  Source from PROZESS-MAP if present; otherwise reconstruct from Q&A. This is the anchor every later step references.\n"
            "## Trigger\n  exact n8n trigger node + config (e.g. 'Schedule Trigger, daily 08:00 Europe/Zurich')\n"
            "## Services & Auth\n  list every external service: n8n node name → credential type → required scopes\n"
            "## Input Data Schema\n  JSON example with the user's actual field names and example values\n"
            "## Business Logic\n  numbered IF/THEN rules with concrete thresholds from the Q&A\n"
            "## Output & Actions\n  for each output: target system, payload mapping, recipient\n"
            "## Error Handling\n  retry policy + failure notification target (concrete addresses/channels)\n"
            "## Volume & Timing\n  records/day from Q&A, peak burst, latency tolerance\n"
            "## MVP Assumptions\n"
            "  If the user-message contains an IDENTIFIZIERTE-MVP-ANNAHMEN block, copy every line VERBATIM into this section. "
            "  Add additional defaults only for fields truly absent from Q&A AND not contradicted by the client. "
            "  Mark every default the model invents itself with '(MVP default — confirm with client)'. "
            "  NEVER fabricate an assumption that contradicts an explicit client statement — those go in the next section.\n"
            "## Offene Klärungspunkte\n"
            "  Collect EVERY point where (a) a sensible default would CONTRADICT what the client actually said, or "
            "  (b) information is genuinely missing and matters for build. Format each as a numbered item that explicitly "
            "  references the client's statement and proposes a path forward.\n"
            "  Example: '1. Zentrale Beleg-E-Mail — Kunde sagte: \"wir haben keine zentrale Adresse\". "
            "  Vorschlag: belege@firma.ch einrichten. ENTSCHEIDUNG vor Build nötig.'\n"
            "  If no contradictions or open questions remain, write a single line: 'Keine offenen Punkte.'\n"
            "## Build Instructions\n"
            "  Numbered steps a developer follows: 1) Create credential X, 2) Add node Y with config Z, "
            "  3) Wire to node W, … For each manual step in 'Current Process (As-Is)' marked auto:yes or auto:partial, "
            "  the build instructions MUST explicitly say which n8n node automates it. "
            "  End with a test plan: 3 sample payloads (happy path, edge case, failure).\n\n"
            "HARD RULES:\n"
            "- NEVER write 'To be defined', 'TBD', 'not specified', 'request from client', or any placeholder in MVP Assumptions or Build Instructions. "
            "  If data is missing AND not contradicted, pick a concrete MVP default and mark '(MVP default — confirm with client)'. "
            "  If data is missing AND the client explicitly said the opposite, put it in `## Offene Klärungspunkte` instead.\n"
            "- Use exact n8n node names: 'Schedule Trigger', 'HTTP Request', 'Gmail', 'Google Sheets', 'IF', 'Set', etc.\n"
            "- Reference the user's actual field names from the Q&A and any uploaded files (e.g. 'Rechnungsnummer', 'Fälligkeitsdatum'), not generic 'field_1'.\n"
            "- If files were uploaded (DATEIEN section), use the column names / structure they reveal as ground truth.\n"
            "- Sei vollständig, nicht knapp. Lieber alle Build-Schritte ausführlich beschreiben als mid-section abbrechen.\n\n"
            "End with this exact line (and nothing after it):\n"
            "'Build this as an n8n workflow. Start with a working MVP. Flag any credentials or config the client needs to provide.'\n\n"
            f"=== CLIENT INFO ===\n{lead_section or '(no lead linked — use generic placeholder values from MVP defaults)'}\n\n"
            f"{payload}\n\n"
            f"=== ROI ESTIMATE ===\n{roi_section or '(not yet calculated)'}"
        ),
    )


# ---------------------------------------------------------------------------
# Weekly LinkedIn brief synthesis
# ---------------------------------------------------------------------------

class LinkedInBriefError(RuntimeError):
    """Raised when the synthesis call fails terminally after all retries."""


def _load_synthesis_prompt() -> str:
    path = _PROMPTS_DIR / "linkedin_brief_synthesis.md"
    if not path.exists():
        raise LinkedInBriefError(f"synthesis prompt missing at {path}")
    return path.read_text(encoding="utf-8")


def _excerpt_business_context(max_chars: int = 4000) -> str:
    """Pull §1 (Offer) + §2 (ICP) from references/business-context.md.

    Best-effort: missing file or unparseable markdown returns empty string.
    """
    path = _PROMPTS_DIR.parent / "references" / "business-context.md"
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""

    start_marker = "## 1. Offer & Delivery"
    end_marker = "## 3. "
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker)) if start != -1 else -1
    if start == -1:
        return ""
    excerpt = text[start: end if end != -1 else start + max_chars]
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rstrip() + "\n\n[…trimmed]"
    return excerpt


def generate_linkedin_brief(signals: dict[str, Any], *, model: str = MODEL_FAST,
                            max_tokens: int = 3000, max_retries: int = 3) -> str:
    """Synthesize the weekly LinkedIn content brief from the signals dict.

    Returns the markdown brief body (no frontmatter — the orchestrator owns
    Notion property assignment). Raises LinkedInBriefError on terminal
    failure so the caller can fall back to a stub brief.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LinkedInBriefError("ANTHROPIC_API_KEY not set")

    system_prompt = _load_synthesis_prompt()
    bc_excerpt = _excerpt_business_context()

    user_payload = {
        "signals": signals,
        "business_context_excerpt": bc_excerpt,
    }
    user_content = (
        "Hier sind die signals der Woche und ein Auszug aus dem business-context. "
        "Erzeuge den Brief strikt nach dem Output-Schema deines System-Prompts.\n\n"
        f"```json\n{json.dumps(user_payload, ensure_ascii=False, indent=2)}\n```"
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": user_content}],
            )
            text = "".join(
                block.text for block in message.content
                if getattr(block, "type", "") == "text"
            ).strip()
            if not text:
                raise LinkedInBriefError("empty response from synthesis call")
            return text
        except anthropic.APIStatusError as e:
            last_err = e
            status = getattr(e, "status_code", 0)
            if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                # Exponential backoff: 0.2s, 0.8s, 3.2s
                time.sleep(0.2 * (4 ** attempt))
                continue
            raise LinkedInBriefError(f"synthesis failed: HTTP {status}: {e}") from e
        except anthropic.APIConnectionError as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(0.2 * (4 ** attempt))
                continue
            raise LinkedInBriefError(f"synthesis connection error: {e}") from e
        except Exception as e:
            last_err = e
            raise LinkedInBriefError(f"synthesis failed: {type(e).__name__}: {e}") from e

    # Unreachable but keep for safety.
    raise LinkedInBriefError(f"synthesis exhausted retries: {last_err}")
