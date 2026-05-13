"""notion_session.py — Notion session persistence + lead lookup for automatisierbar survey.

All Notion calls go through the REST API directly via `requests` (the
notion-client SDK shipped on Render is missing methods we need).

Session storage:
- Primary: state lives on the lead's page in the Leads DB (uses `State` rich_text
  property, auto-provisioned on first write). Session ID is also written to
  the lead's `Session ID` property for resume.
- Fallback: NOTION_DATABASE_ID points at a separate Sessions DB used only for
  lead-less sessions; can be omitted if every interview starts from a lead.

Leads DB ID: NOTION_LEADS_DB_ID env var, falls back to hardcoded fallback below.
"""

import json
import os
import uuid
from typing import Optional

import requests

CHUNK = 1999
_LEADS_DB_ID_FALLBACK = "31cbebb0-c2f9-8047-9e9f-fc59851f8a34"  # Interview Datenbank


def _leads_db() -> str:
    # NOTION_DATABASE_ID is the Sessions DB — never the Leads DB.
    # Allow override via NOTION_LEADS_DB_ID, otherwise use the hardcoded Leads DB.
    return os.environ.get("NOTION_LEADS_DB_ID") or _LEADS_DB_ID_FALLBACK
ALLOWED_STAGES = {
    "Workflow Interview", "Process Mapping", "Prototype Building",
    "Prototype Testing", "Pilot Client", "Paying Client",
}


def _notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


_state_prop_ensured: dict = {}  # db_id -> True once schema is confirmed


def _ensure_state_property(database_id: str) -> None:
    """Idempotently ensure the database has a `State` rich_text property.
    Cached per db_id for the lifetime of the process."""
    if _state_prop_ensured.get(database_id):
        return
    try:
        r = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=_notion_headers(),
            timeout=10,
        )
        r.raise_for_status()
        if "State" not in r.json().get("properties", {}):
            patch = requests.patch(
                f"https://api.notion.com/v1/databases/{database_id}",
                headers=_notion_headers(),
                json={"properties": {"State": {"rich_text": {}}}},
                timeout=10,
            )
            patch.raise_for_status()
        _state_prop_ensured[database_id] = True
    except Exception as e:
        print(f"[notion] _ensure_state_property failed: {e}")


def _update_page(page_id: str, properties: dict) -> dict:
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_notion_headers(),
        json={"properties": properties},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _create_page(database_id: str, properties: dict) -> dict:
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_notion_headers(),
        json={"parent": {"database_id": database_id}, "properties": properties},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _append_blocks(block_id: str, children: list) -> dict:
    r = requests.patch(
        f"https://api.notion.com/v1/blocks/{block_id}/children",
        headers=_notion_headers(),
        json={"children": children},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _query_db(database_id: str, filter_body: dict = None, page_size: int = 100,
              start_cursor: str = None) -> dict:
    body: dict = {"page_size": page_size}
    if filter_body:
        body["filter"] = filter_body
    if start_cursor:
        body["start_cursor"] = start_cursor
    r = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=_notion_headers(),
        json=body,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _query_db_all(database_id: str, filter_body: dict = None, max_pages: int = 20) -> list:
    """Paginate through all results — Notion caps at 100 per request."""
    all_results = []
    cursor = None
    for _ in range(max_pages):
        r = _query_db(database_id, filter_body=filter_body, page_size=100, start_cursor=cursor)
        all_results.extend(r.get("results", []))
        if not r.get("has_more"):
            break
        cursor = r.get("next_cursor")
        if not cursor:
            break
    return all_results


def _db() -> str:
    return os.environ["NOTION_DATABASE_ID"]


_NOTION_RT_MAX_SEGMENTS = 100  # Notion API limit per rich_text property


def _pack(state: dict) -> list:
    s = json.dumps(state, ensure_ascii=False)
    segments = [{"type": "text", "text": {"content": s[i:i + CHUNK]}}
                for i in range(0, len(s), CHUNK)]
    if len(segments) > _NOTION_RT_MAX_SEGMENTS:
        # Should be unreachable with current input limits (8k context + 20 × 4k answers
        # over ~5 rounds ≈ 60-80kB << 100 × 1999 = ~200kB). Surface a clear error if hit.
        raise RuntimeError(
            f"Session state too large for Notion rich_text ({len(segments)} segments, "
            f"max {_NOTION_RT_MAX_SEGMENTS}). Trim earlier rounds or shorten answers."
        )
    return segments


def _unpack(rich_text: list) -> Optional[dict]:
    try:
        joined = "".join(r["text"]["content"] for r in rich_text)
        return json.loads(joined)
    except Exception:
        return None


def _rt(text: str) -> list:
    chunks = []
    for i in range(0, len(str(text)), CHUNK):
        chunks.append({"type": "text", "text": {"content": str(text)[i:i + CHUNK]}})
    return chunks or [{"type": "text", "text": {"content": ""}}]


def _find_page(session_id: str):
    """Find a session by Session ID. Looks in Leads DB first (primary store).
    Falls back to Sessions DB if NOTION_DATABASE_ID is set (lead-less sessions).
    Returns (page_dict_or_None, None) — second tuple slot kept for legacy callsites."""
    try:
        r = _query_db(
            _leads_db(),
            filter_body={"property": "Session ID", "rich_text": {"equals": session_id}},
            page_size=1,
        )
        if r.get("results"):
            return r["results"][0], None
    except Exception as e:
        print(f"[notion] _find_page leads lookup failed: {e}")

    if os.environ.get("NOTION_DATABASE_ID"):
        try:
            r = _query_db(
                _db(),
                filter_body={"property": "Session ID", "rich_text": {"equals": session_id}},
                page_size=1,
            )
            if r.get("results"):
                return r["results"][0], None
        except Exception as e:
            print(f"[notion] _find_page sessions lookup failed: {e}")

    return None, None


# ---------------------------------------------------------------------------
# Session storage (lead page primary, Sessions DB fallback)
# ---------------------------------------------------------------------------

def create_session(context: str, lead_page_id: Optional[str] = None) -> str:
    session_id = str(uuid.uuid4())
    state = {
        "session_id": session_id,
        "status": "active",
        "round": 0,
        "context": context,
        "all_qa": [],
        "current_questions": [],
        "roi": None,
        "lead_page_id": lead_page_id,
        # New: process map (guided A→Z walkthrough), filled before Q&A rounds.
        "process_map": [],
        "process_map_notes": "",
        # New: attachments (Excel/CSV/PDF/image) accumulated in the sidebar.
        "attachments": [],
        # New: free-text "Extras & Dateien" notes pad — autosaved by frontend.
        "extra_context": "",
    }

    # Primary path: store on the lead page (auto-provisions State property if missing)
    if lead_page_id:
        _ensure_state_property(_leads_db())
        try:
            _update_page(lead_page_id, {
                "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
                "State": {"rich_text": _pack(state)},
            })
            return session_id
        except Exception as e:
            raise RuntimeError(f"Failed to write session to lead page: {e}") from e

    # Fallback: create page in Sessions DB
    if not os.environ.get("NOTION_DATABASE_ID"):
        raise RuntimeError("Cannot create lead-less session: NOTION_DATABASE_ID env var not set")
    try:
        _create_page(_db(), {
            "Name": {"title": [{"text": {"content": f"Interview {session_id[:8]}"}}]},
            "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
            "Status": {"select": {"name": "active"}},
            "State": {"rich_text": _pack(state)},
        })
        return session_id
    except Exception as e:
        raise RuntimeError(f"Failed to create session in Sessions DB: {e}") from e


def get_session(session_id: str) -> Optional[dict]:
    page, _ = _find_page(session_id)
    if not page:
        return None
    return _unpack(page["properties"].get("State", {}).get("rich_text", []))


def update_session(session_id: str, updates: dict) -> None:
    page, _ = _find_page(session_id)
    if not page:
        return
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    state.update(updates)

    # Only update properties that exist on this page (Lead pages don't have Status)
    props_update: dict = {"State": {"rich_text": _pack(state)}}
    if "Status" in page.get("properties", {}):
        props_update["Status"] = {"select": {"name": state.get("status", "active")}}

    try:
        _update_page(page["id"], props_update)
    except Exception as e:
        raise RuntimeError(f"Failed to persist session state to Notion: {e}") from e


def available() -> bool:
    """Notion is available if we have an API key. Sessions DB no longer required —
    sessions are stored on lead pages by default."""
    return bool(os.environ.get("NOTION_API_KEY"))


# ---------------------------------------------------------------------------
# Sidebar / process-map mutators (operate on the State JSON)
# ---------------------------------------------------------------------------

# Hard cap for total serialized State JSON. Notion rich_text holds 100 segments ×
# 1999 chars ≈ 200kB; 180k leaves headroom for follow-up Q&A rounds.
MAX_STATE_BYTES = 180_000


def _state_size(state: dict) -> int:
    return len(json.dumps(state, ensure_ascii=False).encode("utf-8"))


def add_attachment(session_id: str, attachment: dict) -> dict:
    """Append `attachment` to state.attachments. Returns a status dict.
    Rejects if the resulting state would exceed MAX_STATE_BYTES (frontend should
    show 'Speicher voll, Datei vorher löschen').
    """
    page, _ = _find_page(session_id)
    if not page:
        raise RuntimeError("session not found")
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    state.setdefault("attachments", [])

    candidate = dict(state)
    candidate["attachments"] = state["attachments"] + [attachment]
    if _state_size(candidate) > MAX_STATE_BYTES:
        return {"ok": False, "reason": "state_full",
                "message": "Speicher voll — bitte vorhandene Datei löschen, bevor weitere hinzugefügt werden."}
    if len(candidate["attachments"]) > 10:
        return {"ok": False, "reason": "too_many",
                "message": "Maximal 10 Dateien pro Sitzung. Bitte vorhandene Datei löschen."}

    state["attachments"] = candidate["attachments"]
    _update_page(page["id"], {"State": {"rich_text": _pack(state)}})
    return {"ok": True, "count": len(state["attachments"])}


def remove_attachment(session_id: str, idx: int) -> bool:
    page, _ = _find_page(session_id)
    if not page:
        return False
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    atts = state.get("attachments", [])
    if not (0 <= idx < len(atts)):
        return False
    atts.pop(idx)
    state["attachments"] = atts
    _update_page(page["id"], {"State": {"rich_text": _pack(state)}})
    return True


def update_extras(session_id: str, extra_context: str) -> bool:
    """Persist the sidebar notes pad. Idempotent — frontend autosaves every 2s."""
    page, _ = _find_page(session_id)
    if not page:
        return False
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    state["extra_context"] = (extra_context or "")[:8000]
    _update_page(page["id"], {"State": {"rich_text": _pack(state)}})
    return True


def update_process_map(session_id: str, process_map: list, process_map_notes: str = "") -> bool:
    """Persist the captured A→Z walkthrough (list of step rows + optional notes)."""
    page, _ = _find_page(session_id)
    if not page:
        return False
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    state["process_map"] = process_map or []
    state["process_map_notes"] = (process_map_notes or "")[:4000]
    _update_page(page["id"], {"State": {"rich_text": _pack(state)}})
    return True


# ---------------------------------------------------------------------------
# Leads DB (Interview Datenbank)
# ---------------------------------------------------------------------------

def _extract_lead(page: dict) -> dict:
    props = page["properties"]

    def _text(key):
        rt = props.get(key, {}).get("rich_text", [])
        return rt[0]["plain_text"] if rt else ""

    def _title(key):
        t = props.get(key, {}).get("title", [])
        return t[0]["plain_text"] if t else ""

    def _select(key):
        s = props.get(key, {}).get("select") or {}
        return s.get("name", "")

    def _status_or_select(key):
        prop = props.get(key, {})
        s = prop.get("status") or prop.get("select") or {}
        return s.get("name", "")

    return {
        "page_id": page["id"],
        "name": _title("Name"),
        "firma": _text("Firma"),
        "branche": _select("Branche"),
        "groesse": _select("Größe"),
        "top_problem": _text("Top Problem"),
        "context": _text("Context"),
        "problem_cluster": _select("Problem Cluster"),
        "pipeline_stage": _status_or_select("Pipeline Stage"),
        "session_id": _text("Session ID"),
    }


def get_lead_by_page_id(page_id: str) -> Optional[dict]:
    """Fetch a single lead page by ID and extract its fields. Reuses _extract_lead."""
    if not available() or not page_id:
        return None
    try:
        r = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=_notion_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return _extract_lead(r.json())
    except Exception as e:
        print(f"[notion] get_lead_by_page_id failed: {e}")
        return None


def _active_stage_filter() -> dict:
    """OR-filter matching Pipeline Stage against ALLOWED_STAGES, trying both
    `status` and `select` property types since we don't know which the DB uses."""
    return {
        "or": [
            *[{"property": "Pipeline Stage", "status": {"equals": s}} for s in ALLOWED_STAGES],
            *[{"property": "Pipeline Stage", "select": {"equals": s}} for s in ALLOWED_STAGES],
        ]
    }


def _query_active_leads() -> list:
    """Try server-side filter first (fast). On Notion 400 (wrong property type),
    fall back to status-only, then select-only."""
    try:
        return _query_db_all(_leads_db(), filter_body=_active_stage_filter(), max_pages=3)
    except requests.HTTPError:
        pass
    for prop_type in ("status", "select"):
        try:
            f = {"or": [{"property": "Pipeline Stage", prop_type: {"equals": s}} for s in ALLOWED_STAGES]}
            return _query_db_all(_leads_db(), filter_body=f, max_pages=3)
        except requests.HTTPError:
            continue
    return []


def search_leads(query: str) -> list:
    if not available():
        return []
    try:
        pages = _query_active_leads()
        q = query.lower()
        results = []
        for page in pages:
            lead = _extract_lead(page)
            if not lead["name"]:
                continue
            if q not in lead["name"].lower() and q not in (lead["firma"] or "").lower():
                continue
            results.append(lead)
            if len(results) >= 8:
                break
        return results
    except Exception as e:
        print(f"[notion] search_leads failed: {e}")
        return []


def link_session_to_lead(lead_page_id: str, session_id: str) -> None:
    """No-op — create_session now writes Session ID to the lead page directly
    when lead_page_id is provided. Kept for backwards compatibility."""
    return


def write_qa_to_page(lead_page_id: str, round_num: int, qa_list: list) -> None:
    if not available() or not lead_page_id:
        return
    try:
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": _rt(f"Runde {round_num}")},
            }
        ]
        for item in qa_list:
            q = item.get("question", "")
            a = item.get("answer", "nicht beantwortet")
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": _rt(f"❓ {q}")},
            })
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": _rt(f"💬 {a}")},
            })
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        _append_blocks(lead_page_id, blocks)
    except Exception as e:
        print(f"[notion] write_qa_to_page failed: {e}")


def _mermaid_label(text: str, limit: int = 32) -> str:
    """Sanitize a step field for inclusion in a Mermaid node label.
    Mermaid breaks on quotes and angle brackets — we strip them rather than escape."""
    if not text:
        return "—"
    # Normalize whitespace, strip mermaid-hostile characters, cap length.
    cleaned = " ".join(str(text).split())
    cleaned = cleaned.replace('"', "'").replace("<", "‹").replace(">", "›").replace("|", "/")
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1] + "…"
    return cleaned


def _build_mermaid(process_map: list) -> str:
    """Render the process map as a Mermaid flowchart. Notion natively renders
    `mermaid`-language code blocks. Generated deterministically — no LLM call."""
    if not process_map:
        return ""
    cls_for = {"yes": "auto", "partial": "partial", "no": "manual"}
    lines = ["flowchart TD"]
    for i, step in enumerate(process_map, start=1):
        who = _mermaid_label(step.get("who"), 24)
        action = _mermaid_label(step.get("action"), 36)
        tool = _mermaid_label(step.get("tool"), 18)
        cls = cls_for.get((step.get("automatable") or "partial").lower(), "partial")
        label = f"{who}<br/>{action}<br/>{tool}"
        lines.append(f'  S{i}["{label}"]:::{cls}')
    for i in range(1, len(process_map)):
        lines.append(f"  S{i} --> S{i+1}")
    lines.append("  classDef manual fill:#fee,stroke:#c33,color:#000")
    lines.append("  classDef partial fill:#ffd,stroke:#cc3,color:#000")
    lines.append("  classDef auto fill:#dfe,stroke:#393,color:#000")
    return "\n".join(lines)


def _table_rows_for_process_map(process_map: list) -> list:
    """Build Notion `table_row` children for the process-map table block."""
    def cell(text):
        return [{"type": "text", "text": {"content": str(text)[:1999]}}]
    auto_label = {"yes": "✓ ja", "partial": "~ teils", "no": "✗ nein"}
    header = {"type": "table_row", "table_row": {"cells": [
        cell("#"), cell("Wer"), cell("Was"), cell("Tool"),
        cell("Daten rein"), cell("Daten raus"), cell("Auto?"),
    ]}}
    rows = [header]
    for i, step in enumerate(process_map, start=1):
        rows.append({"type": "table_row", "table_row": {"cells": [
            cell(step.get("step", i)),
            cell(step.get("who", "")),
            cell(step.get("action", "")),
            cell(step.get("tool", "")),
            cell(step.get("data_in", "")),
            cell(step.get("data_out", "")),
            cell(auto_label.get((step.get("automatable") or "partial").lower(), "—")),
        ]}})
    return rows


_PAYOFF_HEADING = "Aktueller Prozess (Ist-Zustand)"


def _page_already_has_payoff(lead_page_id: str) -> bool:
    """Idempotency: scan top-level blocks for our heading. We don't recurse into
    children — payoff is always written at top-level and the heading text is unique."""
    try:
        cursor = None
        for _ in range(8):  # cap at 8 pages of pagination (~800 blocks)
            url = f"https://api.notion.com/v1/blocks/{lead_page_id}/children?page_size=100"
            if cursor:
                url += f"&start_cursor={cursor}"
            r = requests.get(url, headers=_notion_headers(), timeout=10)
            r.raise_for_status()
            data = r.json()
            for block in data.get("results", []):
                if block.get("type") == "heading_2":
                    rt = block.get("heading_2", {}).get("rich_text", [])
                    text = "".join(seg.get("plain_text", "") for seg in rt)
                    if _PAYOFF_HEADING in text:
                        return True
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return False
    except Exception as e:
        print(f"[notion] _page_already_has_payoff lookup failed: {e}")
        return False  # On error, prefer writing (rare duplicates beat missing payoff)


def write_payoff_to_page(
    lead_page_id: str,
    process_map: list,
    process_map_notes: str,
    claude_code_prompt: str,
) -> bool:
    """Append the end-of-interview payoff: process map (mermaid + table) + Claude Code prompt.
    Idempotent — skips if the heading 'Aktueller Prozess (Ist-Zustand)' is already on the page.
    Returns True if written, False if skipped or failed."""
    if not available() or not lead_page_id:
        return False
    if _page_already_has_payoff(lead_page_id):
        print(f"[notion] payoff already on page {lead_page_id}, skipping")
        return False

    blocks = []

    # Process-map section
    if process_map:
        blocks.append({"object": "block", "type": "heading_2",
                       "heading_2": {"rich_text": _rt(_PAYOFF_HEADING)}})
        mermaid_src = _build_mermaid(process_map)
        if mermaid_src:
            blocks.append({"object": "block", "type": "code",
                           "code": {"language": "mermaid", "rich_text": _rt(mermaid_src)}})
        if process_map_notes:
            blocks.append({"object": "block", "type": "paragraph",
                           "paragraph": {"rich_text": _rt(f"Notizen: {process_map_notes}")}})
        # Toggle with the structured table inside
        toggle_children = [{
            "object": "block", "type": "table",
            "table": {
                "table_width": 7,
                "has_column_header": True,
                "has_row_header": False,
                "children": _table_rows_for_process_map(process_map),
            },
        }]
        blocks.append({"object": "block", "type": "toggle",
                       "toggle": {"rich_text": _rt("Schritt-Details (Tabelle)"),
                                  "children": toggle_children}})

    # Claude Code build prompt section
    if claude_code_prompt:
        blocks.append({"object": "block", "type": "heading_2",
                       "heading_2": {"rich_text": _rt("Build Prompt für Claude Code")}})
        blocks.append({"object": "block", "type": "callout",
                       "callout": {
                           "icon": {"type": "emoji", "emoji": "📋"},
                           "rich_text": _rt(
                               "Diesen Prompt in Claude Code einfügen, um die Automation zu bauen."
                           ),
                       }})
        # Notion code blocks require rich_text segments capped at 2000 chars each;
        # _rt already handles chunking. Use language="markdown" so the prompt syntax-highlights.
        blocks.append({"object": "block", "type": "code",
                       "code": {"language": "markdown", "rich_text": _rt(claude_code_prompt)}})

    if not blocks:
        return False

    try:
        # Notion appends max 100 blocks per call — payoff is always under 10, so safe.
        _append_blocks(lead_page_id, blocks)
        return True
    except Exception as e:
        print(f"[notion] write_payoff_to_page failed: {e}")
        return False


# ---------------------------------------------------------------------------
# LinkedIn Content Briefs DB (weekly brief storage)
# ---------------------------------------------------------------------------

def find_brief_for_week(briefs_db_id: str, week_of_iso: str) -> Optional[dict]:
    """Return the existing brief page for week_of (YYYY-MM-DD) or None.
    Used by the orchestrator to enforce idempotency."""
    try:
        r = _query_db(
            briefs_db_id,
            filter_body={
                "property": "Week Of",
                "date": {"equals": week_of_iso},
            },
            page_size=1,
        )
        results = r.get("results", [])
        return results[0] if results else None
    except Exception as e:
        print(f"[notion] find_brief_for_week failed: {e}")
        return None


def _md_body_to_blocks(body_md: str) -> list[dict]:
    """Render the brief body as a single markdown code block.
    Notion natively renders `markdown` code blocks, and the brand chat
    reads via notion-fetch which returns the raw rich_text — clean both ways.
    Splits at 1999-char boundaries via _rt to respect Notion's per-segment cap.
    """
    return [{
        "object": "block",
        "type": "code",
        "code": {
            "language": "markdown",
            "rich_text": _rt(body_md),
        },
    }]


def create_brief_page(
    *,
    briefs_db_id: str,
    week_of_iso: str,
    title: str,
    body_md: str,
    status: str = "Draft",
    extra_props: Optional[dict] = None,
) -> dict:
    """Create a new row in the LinkedIn Content Briefs DB with the brief
    body as a markdown code block. Returns the created page object."""
    if not available():
        raise RuntimeError("NOTION_API_KEY not set")

    properties: dict = {
        "Name": {"title": [{"type": "text", "text": {"content": title[:1999]}}]},
        "Week Of": {"date": {"start": week_of_iso}},
        "Status": {"select": {"name": status}},
    }
    if extra_props:
        properties.update(extra_props)

    body = {
        "parent": {"database_id": briefs_db_id},
        "properties": properties,
        "children": _md_body_to_blocks(body_md),
    }
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_notion_headers(),
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def replace_brief_body(page_id: str, body_md: str) -> None:
    """Idempotent body refresh: archive existing children, append new code block.
    Used when --force overwrites an existing week's brief."""
    # 1) Fetch all top-level children
    try:
        cursor = None
        block_ids: list[str] = []
        for _ in range(8):
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            if cursor:
                url += f"&start_cursor={cursor}"
            r = requests.get(url, headers=_notion_headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            block_ids.extend(b["id"] for b in data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        # 2) Archive each (Notion delete = archive)
        for bid in block_ids:
            try:
                requests.delete(
                    f"https://api.notion.com/v1/blocks/{bid}",
                    headers=_notion_headers(),
                    timeout=10,
                )
            except Exception:
                pass
        # 3) Append fresh content
        _append_blocks(page_id, _md_body_to_blocks(body_md))
    except Exception as e:
        raise RuntimeError(f"replace_brief_body failed: {e}") from e


def update_brief_props(page_id: str, props: dict) -> None:
    """Patch select/number/title properties on an existing brief page."""
    _update_page(page_id, props)


def create_briefs_db(parent_page_id: str) -> str:
    """Bootstrap helper: create the 'LinkedIn Content Briefs' DB under parent_page_id.
    Returns the new DB ID — caller persists it as NOTION_BRIEFS_DB_ID in .env."""
    body = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "LinkedIn Content Briefs"}}],
        "properties": {
            "Name": {"title": {}},
            "Week Of": {"date": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Draft", "color": "yellow"},
                        {"name": "Reviewed", "color": "blue"},
                        {"name": "Posted", "color": "green"},
                        {"name": "Skipped", "color": "gray"},
                    ]
                }
            },
            "Commit Count": {"number": {"format": "number"}},
            "Decision Count": {"number": {"format": "number"}},
            "Posted URL": {"url": {}},
        },
    }
    r = requests.post(
        "https://api.notion.com/v1/databases",
        headers=_notion_headers(),
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def write_roi_to_page(lead_page_id: str, roi: dict, assumptions: list) -> None:
    if not available() or not lead_page_id:
        return
    try:
        lines = [
            f"Prozess: {roi.get('process', '')}",
            f"Jetzt: {roi.get('hours_per_week_now', '')} Std/Woche  →  {roi.get('minutes_per_week_after', '')} Min/Woche",
            f"Einsparung: CHF {roi.get('chf_monthly_savings', '')} / Monat",
            f"Entwicklungszeit: {roi.get('build_time_days', '')}",
            f"Komplexität: {roi.get('complexity', '')}",
        ]
        blocks = [
            {"object": "block", "type": "heading_2",
             "heading_2": {"rich_text": _rt("ROI Schätzung")}},
            {"object": "block", "type": "paragraph",
             "paragraph": {"rich_text": _rt("\n".join(lines))}},
        ]
        if assumptions:
            blocks.append({"object": "block", "type": "heading_3",
                           "heading_3": {"rich_text": _rt("MVP-Annahmen")}})
            for a in assumptions:
                blocks.append({
                    "object": "block", "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": _rt(a)},
                })
        _append_blocks(lead_page_id, blocks)
    except Exception as e:
        print(f"[notion] write_roi_to_page failed: {e}")
