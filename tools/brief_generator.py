"""brief_generator.py — Company Brief automation (Hub M9, cockpit engine).

Generates a self-contained HTML pre-meeting brief for a company, in three flavours chosen by
the linked lead's pipeline stage:

  - "wf"      Workflow-Interview brief  (deep pre-interview research: company, people,
                                         automation hypotheses, Gesprächsleitfaden)
  - "pilot"   Pilot-implementation brief (recap company + interview + the built product +
                                         good-to-know about the person)
  - "general" General brief             (any other meeting with a Pilot/Paying-stage client)

Design (WAT): the probabilistic LLM produces STRUCTURED CONTENT (validated JSON); a
deterministic renderer turns it into HTML in the equity-explainer aesthetic. Every brief
opens with an ELI5 "Was macht diese Firma eigentlich?" layer + a "Für Erwachsene" note.

Reuses: tools/notion_session.py (lead + interview-spec State JSON + page body),
tools/claude_client.py (Anthropic client + models), the Anthropic server-side web_search tool
(same pattern as claude_client.resolve_walkin_contact). Fails SAFE — a research or generation
failure degrades the brief, never crashes the caller.
"""

from __future__ import annotations

import html as _html
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import sys

import anthropic

# tools/ is on sys.path when imported from api.py (api.py:29). Guarantee it for standalone /
# test runs too, then import siblings flat (repo convention — tools/ has no __init__.py).
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import notion_session as ns  # noqa: E402
from claude_client import MODEL_CLASSIFY, MODEL_FAST, _parse_json  # noqa: E402  # type: ignore

# ---------------------------------------------------------------------------
# Stage -> brief type
# ---------------------------------------------------------------------------

# Maps the lead's Pipeline Stage (Interview Datenbank) to one of the three brief types.
STAGE_TO_TYPE: dict[str, str] = {
    "Workflow Interview": "wf",
    "Process Mapping": "wf",
    "Problem Interview": "wf",
    "Prototype Building": "pilot",
    "Prototype Testing": "pilot",
    "Pilot Client": "pilot",
    "Paying Client": "general",
}

BRIEF_LABEL = {"wf": "WF Brief", "pilot": "Pilot Brief", "general": "General Brief"}
BRIEF_TITLE = {
    "wf": "Workflow-Interview — Vorbereitung",
    "pilot": "Pilot-Implementierung — Vorbereitung",
    "general": "Kundentermin — Vorbereitung",
}

# Per-type model. WF benefits from a capable model + web research; overridable via env.
_MODEL_WF = os.environ.get("BRIEF_MODEL_WF", MODEL_FAST)
_MODEL_PILOT = os.environ.get("BRIEF_MODEL_PILOT", MODEL_FAST)
_MODEL_GENERAL = os.environ.get("BRIEF_MODEL_GENERAL", MODEL_FAST)
_MODEL_BY_TYPE = {"wf": _MODEL_WF, "pilot": _MODEL_PILOT, "general": _MODEL_GENERAL}


def classify_brief_type(pipeline_stage: str) -> str:
    """Return 'wf' | 'pilot' | 'general' for a Pipeline Stage, or '' to skip (OUT / unknown)."""
    return STAGE_TO_TYPE.get((pipeline_stage or "").strip(), "")


# ---------------------------------------------------------------------------
# Context gathering (Notion lead + interview spec + page body)
# ---------------------------------------------------------------------------

def _read_page_text(page_id: str, *, max_chars: int = 6000) -> str:
    """Read a Notion page body as plain text (paragraphs, headings, bullets). Best-effort —
    returns '' on any failure. Used for the walk-in 'Notiz vom Besuch' + any manual notes."""
    if not page_id:
        return ""
    try:
        import requests

        out: list[str] = []
        cursor: Optional[str] = None
        for _ in range(4):  # cap pagination
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            if cursor:
                url += f"&start_cursor={cursor}"
            r = requests.get(url, headers=ns._notion_headers(), timeout=10)
            r.raise_for_status()
            data = r.json()
            for b in data.get("results", []):
                bt = b.get("type", "")
                payload = b.get(bt, {}) if isinstance(b.get(bt), dict) else {}
                rt = payload.get("rich_text", []) if isinstance(payload, dict) else []
                text = "".join(seg.get("plain_text", "") for seg in rt).strip()
                if text:
                    out.append(text)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return "\n".join(out)[:max_chars]
    except Exception as e:  # noqa: BLE001
        print(f"[brief] page-body read failed for {page_id}: {e!r}", flush=True)
        return ""


def _interview_spec(lead: dict) -> dict:
    """Pull the interview end-product spec from the lead's State JSON (via its Session ID).
    Returns the fields a Pilot/General brief needs, or {} if no interview was run."""
    sid = (lead or {}).get("session_id") or ""
    if not sid:
        return {}
    try:
        st = ns.get_session(sid) or {}
    except Exception as e:  # noqa: BLE001
        print(f"[brief] get_session failed for {sid}: {e!r}", flush=True)
        return {}
    roi = st.get("roi") or {}
    return {
        "process_name": st.get("process_name") or roi.get("process", ""),
        "process_map": st.get("process_map") or [],
        "process_map_notes": st.get("process_map_notes", ""),
        "process_map_classification": st.get("process_map_classification") or [],
        "roi_chf_monthly": roi.get("chf_monthly_savings"),
        "roi_process": roi.get("process", ""),
        "spec_summary": st.get("spec_summary", ""),
        "claude_code_prompt": st.get("claude_code_prompt", ""),
        "additional_automations": st.get("additional_automations") or [],
        "interviewer": st.get("interviewer", ""),
        "round": st.get("round", 0),
    }


def gather_context(lead_page_id: str, brief_type: str) -> dict:
    """Assemble everything the LLM needs. Returns a context dict; raises ValueError only if the
    lead cannot be loaded at all (caller decides how to surface that)."""
    lead = ns.get_lead_by_page_id(lead_page_id)
    if not lead:
        raise ValueError(f"lead not found: {lead_page_id}")
    ctx: dict[str, Any] = {
        "brief_type": brief_type,
        "lead": lead,
        "firma": lead.get("firma") or lead.get("name") or "",
        "page_notes": _read_page_text(lead_page_id),
    }
    if brief_type in ("pilot", "general"):
        ctx["spec"] = _interview_spec(lead)
    return ctx


# ---------------------------------------------------------------------------
# LLM generation -> structured content
# ---------------------------------------------------------------------------

_JSON_SHAPE = """\
Antworte GANZ AM ENDE NUR mit einem JSON-Objekt (kein Text davor/danach), exakt dieser Form:
{
  "firma": "offizieller Firmenname",
  "summary": "EIN Satz (max 160 Zeichen): wer die Firma ist + wen ihr vermutlich trefft",
  "eli5_simple": "2-3 Sätze auf dem Niveau eines Drittklässlers: was macht diese Firma WIRKLICH? Konkret, anschaulich, ohne Fachjargon.",
  "eli5_grownup": "1-2 Sätze mit der präzisen, fachlich korrekten Beschreibung derselben Sache.",
  "sections": [ <Abschnitte, siehe unten> ],
  "sources": ["knowgravity.com", "Moneyhouse", ...]
}

Jeder Abschnitt in "sections" hat ein "type" und "title". Erlaubte Typen:
- {"type":"prose","title":"...","paragraphs":["...", "..."]}
- {"type":"factsheet","title":"...","rows":[["Label","Wert"], ...]}
- {"type":"people","title":"...","people":[{"name":"...","role":"...","note":"..."}]}
- {"type":"hypotheses","title":"...","items":[{"prozess":"...","haeufig":"ja|eher klein|?","teuer":"ja|?","strukturiert":"ja|eher ja|teils|selten","pruefen":"Was im Interview zu fragen ist"}]}
- {"type":"questions","title":"...","items":["Frage 1","Frage 2", ...]}
- {"type":"gates","title":"...","rows":[["Häufig","Frage, die es beantwortet"], ...]}
- {"type":"qa","title":"...","items":[{"q":"Was sie fragen könnten","a":"Eure Antwort"}]}
- {"type":"callout","variant":"grownup|analogy|merke","title":"...","body":"..."}
- {"type":"steps","title":"...","items":["Schritt 1", ...]}
"""

_RULES = """\
HARTE REGELN:
- Sprache: Deutsch (Schweizer Hochdeutsch, "ihr/euch" fürs Team). KEINE Gedankenstriche (—/–); nutze Komma/Doppelpunkt/Punkt. Zusammengesetzte Bindestriche (30-Minuten-Termin) sind erlaubt.
- ERFINDE NICHTS. Fakten (HR/UID, Namen, Zahlen) nur wenn belegt (Recherche oder gelieferte Daten). Unsicheres als "?" oder "im Interview verifizieren" markieren, nicht raten.
- Automatisierungs-Hypothesen sind UNVALIDIERT und dienen der Gesprächsvorbereitung — so framen, nie als fertige Lösung pitchen.
- Ton: sachlich, dicht, unter Profis. Kein Buzzword-Bingo, kein "KI-Revolution/disruptiv".
- Der eli5-Abschnitt ist Pflicht und muss die Frage "Was macht die Firma eigentlich?" so beantworten, dass es auch nach einmaligem Lesen hängen bleibt.
"""

_SYS_WF = """\
Du bist Researcher bei automatisierbar.ch (Schweizer Backoffice-Automatisierung für KMU). Du erstellst einen internen VORBEREITUNGS-BRIEF für ein Workflow-Interview (erstes tiefes Gespräch mit einem KMU). Ziel: das Team versteht die Firma, die Entscheidungsträger und die wahrscheinlichsten Gesprächspartner, und geht mit klugen Fragen + Hypothesen rein (Mom-Test: disqualifizieren, nicht verkaufen).

Nutze das web_search-Werkzeug, um die Firma zu recherchieren: offizielle Website, Handelsregister/Moneyhouse (Rechtsform, UID, Gründung, Zweck), Schlüsselpersonen + Rollen (Impressum, LinkedIn), was die Firma konkret tut. Recherchiere gezielt und sparsam.

Erzeuge diese Abschnitte (in dieser Reihenfolge, passe sie an die Firma an):
1. factsheet "Firmensteckbrief" (Firma, Sitz, Rechtsform/UID, Gründung, Grösse, Branche, Reichweite, Kontakt)
2. prose "Was die Firma konkret macht"
3. people "Entscheidungsträger / wen ihr trefft" (wer wahrscheinlich am Tisch sitzt + warum relevant)
4. hypotheses "Automatisierungs-Hypothesen" (3-5 vermutete Prozesse, gegen Häufig/Teuer/Strukturiert)
5. questions "Kluge Fragen, die ihr stellt" (5-7, Mom-Test-konform, nach konkreten letzten Ereignissen)
6. gates "Disqualifikations-Gates" (Häufig/Teuer/Strukturiert/Unterversorgt/Erreichbar)
7. qa "Was sie EUCH fragen könnten" (3-5 wahrscheinliche Fragen + eure ehrliche Antwort; Zero-Risk-Pilot, Datenschutz CH, kein Lock-in)
"""

_SYS_PILOT = """\
Du bist Vorbereitungs-Assistent bei automatisierbar.ch. Du erstellst einen internen BRIEF für ein Pilot-/Implementierungs-Treffen. Die Person, die hingeht, hat den Prototyp meist selbst gebaut — der Brief ist eine PRÄZISE WIEDERHOLUNG dessen, was besprochen wurde, plus was jetzt gezeigt/übergeben wird.

Dir werden die Interview-Daten geliefert (Prozess-Map, ROI, Spec-Zusammenfassung, der Claude-Code-Prompt = die gebaute Lösung). Nutze web_search nur falls nötig für aktuelle Fakten zur Person/Firma.

Erzeuge diese Abschnitte:
1. prose "Kurzprofil" (1 Absatz: wer die Firma ist)
2. prose "Was im Workflow-Interview herauskam" (der Schmerz, der Prozess, die ROI-Zahl)
3. prose "Das gebaute Produkt & wie es für den Kunden aussieht" (präzise: was tut die Lösung, wie bedient der Kunde sie, was ist das sichtbare Resultat — aus Spec + Prozess-Map)
4. people "Wen ihr trefft" (die Person + good-to-know: Rolle, was ihr über sie wisst)
5. steps "Ziel des Termins & nächster Schritt"
6. callout variant "grownup" "Offene Punkte / Risiken"
"""

_SYS_GENERAL = """\
Du bist Vorbereitungs-Assistent bei automatisierbar.ch. Du erstellst einen internen BRIEF für einen laufenden Kundentermin (Pilot- oder zahlender Kunde, kein Erstgespräch, keine Implementierung). Ziel: das Team ist zum Beziehungsstand, zur Historie und zu wahrscheinlichen Themen auf dem Laufenden.

Nutze die gelieferten Daten (Firma, Kontext, ggf. Interview-Spec) und web_search nur falls nötig.

Erzeuge diese Abschnitte:
1. prose "Kurzprofil & Beziehungsstatus" (wer die Firma ist, seit wann Kunde, was wir liefern)
2. prose "Bisherige Historie" (was zuletzt lief, offene Fäden)
3. people "Wen ihr trefft" (die Person + good-to-know)
4. prose "Aktueller Produkt-/Betreuungsstand"
5. steps "Mögliche Themen / Ziel des Termins"
6. callout variant "grownup" "Offene Punkte"
"""

_SYS_BY_TYPE = {"wf": _SYS_WF, "pilot": _SYS_PILOT, "general": _SYS_GENERAL}


def _build_user_prompt(ctx: dict) -> str:
    lead = ctx.get("lead", {})
    blocks = [
        f"FIRMA: {ctx.get('firma','')}",
        f"Ansprechpartner/Name (Lead): {lead.get('name','')}",
        f"Branche (Lead): {lead.get('branche','')}",
        f"Grösse (Lead): {lead.get('groesse','')}",
        f"Pipeline-Stufe: {lead.get('pipeline_stage','')}",
        f"Top-Problem (Lead): {lead.get('top_problem','') or '(keins erfasst)'}",
        f"Kontext-Karte (Lead, aus Website-Recherche): {lead.get('context','') or '(keine)'}",
    ]
    notes = (ctx.get("page_notes") or "").strip()
    if notes:
        blocks += ["", "NOTIZEN AUF DER LEAD-SEITE (Walk-in, Gesprächsnotizen — wörtlich):", notes[:4000]]
    spec = ctx.get("spec") or {}
    if spec:
        blocks += ["", "INTERVIEW- & PRODUKT-DATEN (aus dem geführten Workflow-Interview):"]
        if spec.get("process_name"):
            blocks.append(f"- Prozess: {spec['process_name']}")
        if spec.get("roi_chf_monthly") is not None:
            blocks.append(f"- Geschätzte Ersparnis: {spec['roi_chf_monthly']} CHF/Monat")
        if spec.get("process_map"):
            try:
                pm = " → ".join(str(s.get("step", s) if isinstance(s, dict) else s) for s in spec["process_map"])
            except Exception:  # noqa: BLE001
                pm = str(spec["process_map"])
            blocks.append(f"- Prozess-Map: {pm[:1500]}")
        if spec.get("process_map_notes"):
            blocks.append(f"- Prozess-Notizen: {spec['process_map_notes'][:1500]}")
        if spec.get("spec_summary"):
            blocks.append(f"- Spec-Zusammenfassung:\n{spec['spec_summary'][:3000]}")
        if spec.get("claude_code_prompt"):
            blocks.append(f"- Gebaute Lösung (Claude-Code-Prompt, = was existiert):\n{spec['claude_code_prompt'][:3000]}")
    blocks += ["", _JSON_SHAPE]
    return "\n".join(blocks)


def generate_brief_content(ctx: dict, brief_type: str, *, model: Optional[str] = None,
                           use_web_search: Optional[bool] = None) -> dict:
    """Call Claude once (web_search enabled for WF) -> validated structured content dict.
    Raises RuntimeError on missing key or unrecoverable failure (caller surfaces it)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    model = model or _MODEL_BY_TYPE.get(brief_type, MODEL_FAST)
    if use_web_search is None:
        use_web_search = brief_type == "wf"
    system = _SYS_BY_TYPE.get(brief_type, _SYS_WF) + "\n\n" + _RULES
    user = _build_user_prompt(ctx)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}] if use_web_search else []
    messages: list[dict] = [{"role": "user", "content": user}]

    def _call(msgs, with_tools):
        return client.messages.create(
            model=model, max_tokens=8000,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            tools=(tools if with_tools else []), messages=msgs,
        )

    def _text_of(resp) -> str:
        return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")

    # Research + write, resuming while the server-side web_search tool pauses the turn.
    resp = None
    last_err = None
    for _try in range(3):  # retry the whole exchange on hard API errors
        try:
            resp = _call(messages, with_tools=bool(tools))
            hops = 0
            while resp.stop_reason == "pause_turn" and hops < 8:
                messages.append({"role": "assistant", "content": resp.content})
                resp = _call(messages, with_tools=bool(tools))
                hops += 1
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            resp = None
            time.sleep(2 * (_try + 1))
    if resp is None:
        raise RuntimeError(f"Claude call failed: {last_err!r}")

    try:
        data = _parse_json(_text_of(resp))
    except Exception:  # noqa: BLE001
        data = None
    # After web research the model sometimes narrates and runs out of room before emitting the
    # JSON. Force a clean, tool-less follow-up that asks ONLY for the JSON (it still has all the
    # gathered context in `messages`).
    if not isinstance(data, dict) or not data.get("sections"):
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": (
            "Gib jetzt AUSSCHLIESSLICH das vollständige JSON-Objekt gemäss Vorgabe aus "
            "(alle Abschnitte, kein Text davor oder danach, nur das JSON).")})
        try:
            resp2 = _call(messages, with_tools=False)
            data = _parse_json(_text_of(resp2))
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Claude returned no usable brief content: {e}") from e
    if not isinstance(data, dict) or not data.get("sections"):
        raise RuntimeError("Claude returned no usable brief content")
    return data


# ---------------------------------------------------------------------------
# Deterministic HTML render (equity-explainer aesthetic)
# ---------------------------------------------------------------------------

def _esc(s: Any) -> str:
    return _html.escape(str(s if s is not None else ""))


_PILL = {
    "ja": "pill-yes", "eher ja": "pill-yes",
    "teils": "pill-mid", "eher klein": "pill-mid",
    "selten": "pill-no", "nein": "pill-no",
    "?": "pill-q", "": "pill-q",
}


def _pill(val: str) -> str:
    v = (val or "").strip().lower()
    cls = _PILL.get(v, "pill-mid")
    return f'<span class="pill {cls}">{_esc(val or "?")}</span>'


def _render_section(sec: dict, idx: int) -> str:
    typ = (sec.get("type") or "").strip()
    title = _esc(sec.get("title", ""))
    head = f'<h2><span class="num">{idx}</span>{title}</h2>' if title else ""

    if typ == "prose":
        body = "".join(f"<p>{_esc(p)}</p>" for p in sec.get("paragraphs", []) if p)
        return f"<section>{head}{body}</section>"

    if typ == "factsheet":
        rows = "".join(
            f'<tr><th class="fact">{_esc(r[0])}</th><td>{_esc(r[1])}</td></tr>'
            for r in sec.get("rows", []) if isinstance(r, (list, tuple)) and len(r) >= 2
        )
        return f'<section>{head}<table class="factsheet">{rows}</table></section>'

    if typ == "people":
        cards = ""
        for p in sec.get("people", []):
            cards += (
                '<div class="person"><div class="pname">'
                f'{_esc(p.get("name",""))}'
                f'<span class="prole">{_esc(p.get("role",""))}</span></div>'
                f'<p>{_esc(p.get("note",""))}</p></div>'
            )
        return f"<section>{head}{cards}</section>"

    if typ == "hypotheses":
        rows = ""
        for it in sec.get("items", []):
            rows += (
                "<tr>"
                f'<td><b>{_esc(it.get("prozess",""))}</b></td>'
                f'<td>{_pill(it.get("haeufig",""))}</td>'
                f'<td>{_pill(it.get("teuer",""))}</td>'
                f'<td>{_pill(it.get("strukturiert",""))}</td>'
                f'<td class="pruefen">{_esc(it.get("pruefen",""))}</td>'
                "</tr>"
            )
        return (
            f'<section>{head}<table class="hyp"><tr>'
            "<th>Vermuteter Prozess</th><th>Häufig?</th><th>Teuer?</th>"
            "<th>Strukturiert?</th><th>Im Interview prüfen</th></tr>"
            f"{rows}</table></section>"
        )

    if typ == "questions":
        items = "".join(f"<li>{_esc(q)}</li>" for q in sec.get("items", []) if q)
        return f"<section>{head}<ol class='q'>{items}</ol></section>"

    if typ == "steps":
        items = "".join(f"<li>{_esc(q)}</li>" for q in sec.get("items", []) if q)
        return f"<section>{head}<ol class='q'>{items}</ol></section>"

    if typ == "gates":
        rows = "".join(
            f"<tr><th class='fact'>{_esc(r[0])}</th><td>{_esc(r[1])}</td></tr>"
            for r in sec.get("rows", []) if isinstance(r, (list, tuple)) and len(r) >= 2
        )
        return f'<section>{head}<table class="factsheet">{rows}</table></section>'

    if typ == "qa":
        blocks = ""
        for it in sec.get("items", []):
            blocks += f'<h3 class="qa">„{_esc(it.get("q",""))}"</h3><p class="ans">{_esc(it.get("a",""))}</p>'
        return f"<section>{head}{blocks}</section>"

    if typ == "callout":
        variant = (sec.get("variant") or "grownup").strip()
        cls = {"grownup": "grownup", "analogy": "analogy", "merke": "merke"}.get(variant, "grownup")
        t = f"<b>{title}:</b> " if title else ""
        return f'<div class="{cls}">{t}{_esc(sec.get("body",""))}</div>'

    # Unknown type: render its title + any string body defensively.
    return f"<section>{head}<p>{_esc(sec.get('body',''))}</p></section>" if head else ""


_CSS = """\
@page { size: A4; margin: 15mm 14mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #1f2937; background:#fff; }
body { margin: 0; line-height: 1.5; font-size: 12pt; max-width: 820px; margin: 0 auto; padding: 0 4vw 40px; }
h1 { font-size: 26pt; line-height: 1.12; margin: 0 0 4px; color: #0f766e; }
h2 { font-size: 16pt; margin: 22px 0 6px; color: #0f766e; }
h3 { font-size: 12.5pt; margin: 12px 0 2px; color: #b45309; }
h3.qa { color:#0f766e; }
p { margin: 0 0 9px; }
p.ans { margin-top:0; }
p.ans::before { content:"→ "; color:#0f766e; font-weight:700; }
.lead { font-size: 13.5pt; color: #374151; }
.header { padding: 26px 0 14px; border-bottom: 2px solid #ccfbf1; margin-bottom: 8px; }
.brand { font-weight:700; color:#0f766e; letter-spacing:.2px; }
.badge { display:inline-block; margin-left:8px; padding:2px 10px; background:#ccfbf1; color:#0f766e; border-radius:999px; font-size:10pt; font-weight:600; vertical-align:middle; }
.meta { color:#6b7280; font-size:10.5pt; margin-top:4px; }
section { page-break-inside: avoid; margin: 0 0 6px; }
.num { display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:50%; background:#0f766e; color:#fff; font-weight:700; margin-right:9px; font-size:12pt; vertical-align:middle; }
.eli5 { background:#f0fdfa; border:1px solid #99f6e4; border-radius:14px; padding:16px 18px; margin:14px 0 6px; }
.eli5 .k { font-size:15pt; color:#0f766e; margin:0 0 6px; }
.grownup { background:#fff7ed; border:1px solid #fed7aa; border-left:5px solid #f59e0b; border-radius:10px; padding:10px 14px; margin:10px 0; font-size:11pt; }
.grownup b { color:#b45309; }
.analogy { background:#eff6ff; border:1px solid #bfdbfe; border-left:5px solid #3b82f6; border-radius:10px; padding:10px 14px; margin:10px 0; }
.analogy b { color:#1d4ed8; }
.merke { background:#f0fdf4; border:1px solid #bbf7d0; border-left:5px solid #16a34a; border-radius:10px; padding:10px 14px; margin:10px 0; }
.merke b { color:#15803d; }
.person { background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px; padding:10px 14px; margin:8px 0; }
.pname { font-weight:700; color:#111827; }
.prole { font-weight:400; color:#6b7280; margin-left:8px; font-size:11pt; }
table { width:100%; border-collapse:collapse; margin:8px 0; font-size:11pt; }
th, td { text-align:left; padding:7px 9px; border-bottom:1px solid #e5e7eb; vertical-align:top; }
th { background:#f0fdfa; color:#0f766e; }
th.fact { width:32%; }
table.hyp th { font-size:10pt; }
td.pruefen { color:#374151; font-size:10.5pt; }
ol.q { margin:6px 0 10px; padding-left:24px; }
ol.q li { margin:5px 0; }
.pill { display:inline-block; padding:1px 9px; border-radius:999px; font-size:10pt; font-weight:600; }
.pill-yes { background:#dcfce7; color:#15803d; }
.pill-mid { background:#fef9c3; color:#a16207; }
.pill-no { background:#fee2e2; color:#b91c1c; }
.pill-q { background:#f3f4f6; color:#6b7280; }
.footer { margin-top:26px; padding-top:10px; border-top:2px solid #ccfbf1; color:#6b7280; font-size:9.5pt; }
.sources { color:#6b7280; font-size:10pt; margin-top:10px; }
"""


def render_html(content: dict, brief_type: str, *, meta: Optional[dict] = None) -> str:
    """Turn validated content into a self-contained HTML brief. Pure/deterministic."""
    meta = meta or {}
    firma = _esc(content.get("firma") or meta.get("firma") or "Firma")
    label = _esc(BRIEF_LABEL.get(brief_type, "Brief"))
    subtitle = _esc(BRIEF_TITLE.get(brief_type, ""))
    date_str = _esc(meta.get("date") or datetime.now(timezone.utc).strftime("%d.%m.%Y"))

    sections_html = ""
    idx = 1
    # ELI5 block first (always).
    simple = content.get("eli5_simple", "")
    grownup = content.get("eli5_grownup", "")
    if simple or grownup:
        sections_html += (
            '<section><div class="eli5">'
            f'<p class="k"><span class="num">{idx}</span>Was macht diese Firma eigentlich?</p>'
            f"<p class='lead'>{_esc(simple)}</p>"
            + (f'<div class="grownup"><b>Für Erwachsene:</b> {_esc(grownup)}</div>' if grownup else "")
            + "</div></section>"
        )
        idx += 1

    for sec in content.get("sections", []):
        if not isinstance(sec, dict):
            continue
        if sec.get("type") == "callout":
            sections_html += _render_section(sec, idx)  # callouts don't consume a number
            continue
        sections_html += _render_section(sec, idx)
        idx += 1

    sources = content.get("sources") or []
    sources_html = ""
    if sources:
        sources_html = '<div class="sources">Quellen: ' + " · ".join(_esc(s) for s in sources) + "</div>"

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{label} — {firma}</title>
<style>{_CSS}</style></head><body>
<div class="header">
  <div><span class="brand">automatisierbar</span><span class="badge">{label}</span></div>
  <h1>{firma}</h1>
  <div class="meta">{subtitle} · Interne Vorbereitung · vertraulich · {date_str}</div>
</div>
{sections_html}
<div class="footer">
  automatisierbar · vertrauliche interne Gesprächsvorbereitung · {date_str}.
  Automatisierungs-Hypothesen sind unvalidiert und dienen ausschliesslich der Vorbereitung.
  {sources_html}
</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:40] or "firma"


def generate(lead_page_id: str, brief_type: Optional[str] = None, *,
             model: Optional[str] = None) -> dict:
    """Full pipeline: gather -> generate -> render. Returns
    {ok, html, summary, brief_type, firma, slug, token}. `brief_type` auto-derived from the
    lead's pipeline stage when omitted; raises ValueError if the stage maps to no brief."""
    lead = ns.get_lead_by_page_id(lead_page_id)
    if not lead:
        raise ValueError(f"lead not found: {lead_page_id}")
    if not brief_type:
        brief_type = classify_brief_type(lead.get("pipeline_stage", ""))
    if brief_type not in ("wf", "pilot", "general"):
        raise ValueError(
            f"no brief type for stage {lead.get('pipeline_stage','')!r} (lead {lead_page_id})"
        )

    ctx = gather_context(lead_page_id, brief_type)
    content = generate_brief_content(ctx, brief_type, model=model)
    firma = content.get("firma") or ctx.get("firma") or lead.get("name") or "Firma"
    html_doc = render_html(content, brief_type, meta={"firma": firma})
    return {
        "ok": True,
        "html": html_doc,
        "summary": (content.get("summary") or "")[:200],
        "brief_type": brief_type,
        "firma": firma,
        "slug": _slugify(firma),
        "token": uuid.uuid4().hex,
    }
