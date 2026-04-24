"""notion_session.py — Notion session persistence + lead lookup for automatisierbar survey.

Renamed from notion_client.py to avoid shadowing the `notion-client` pip package.

Sessions database: NOTION_DATABASE_ID env var (separate sessions DB)
Leads database:    31cbebb0-c2f9-8075-b996-000b1747664a (Interview Datenbank)
"""

import json
import os
import uuid
from typing import Optional

CHUNK = 1999
LEADS_DB_ID = "31cbebb0-c2f9-8075-b996-000b1747664a"
ALLOWED_STAGES = {
    "Workflow Interview", "Process Mapping", "Prototype Building",
    "Prototype Testing", "Pilot Client", "Paying Client",
}


def _client():
    from notion_client import Client  # pip: notion-client — now resolves correctly
    return Client(auth=os.environ["NOTION_API_KEY"])


def _db() -> str:
    return os.environ["NOTION_DATABASE_ID"]


def _pack(state: dict) -> list:
    s = json.dumps(state, ensure_ascii=False)
    return [{"type": "text", "text": {"content": s[i:i + CHUNK]}}
            for i in range(0, len(s), CHUNK)]


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
    try:
        n = _client()
        r = n.databases.query(
            database_id=_db(),
            filter={"property": "Session ID", "rich_text": {"equals": session_id}},
        )
        page = r["results"][0] if r["results"] else None
        return page, n
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Sessions DB
# ---------------------------------------------------------------------------

def create_session(context: str) -> str:
    session_id = str(uuid.uuid4())
    state = {
        "session_id": session_id,
        "status": "active",
        "round": 0,
        "context": context,
        "all_qa": [],
        "current_questions": [],
        "roi": None,
        "lead_page_id": None,
    }
    try:
        n = _client()
        n.pages.create(
            parent={"database_id": _db()},
            properties={
                "Name": {"title": [{"text": {"content": f"Interview {session_id[:8]}"}}]},
                "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
                "Status": {"select": {"name": "active"}},
                "State": {"rich_text": _pack(state)},
            },
        )
    except Exception as e:
        print(f"[notion] create_session failed: {e}")
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    page, _ = _find_page(session_id)
    if not page:
        return None
    return _unpack(page["properties"].get("State", {}).get("rich_text", []))


def update_session(session_id: str, updates: dict) -> None:
    page, n = _find_page(session_id)
    if not page or not n:
        return
    state = _unpack(page["properties"].get("State", {}).get("rich_text", [])) or {}
    state.update(updates)
    try:
        n.pages.update(
            page_id=page["id"],
            properties={
                "State": {"rich_text": _pack(state)},
                "Status": {"select": {"name": state.get("status", "active")}},
            },
        )
    except Exception as e:
        print(f"[notion] update_session failed: {e}")


def available() -> bool:
    return bool(os.environ.get("NOTION_API_KEY") and os.environ.get("NOTION_DATABASE_ID"))


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


def search_leads(query: str) -> list:
    if not available():
        return []
    try:
        n = _client()
        r = n.databases.query(
            database_id=LEADS_DB_ID,
            filter={"property": "Name", "title": {"contains": query}},
            page_size=12,
        )
        results = []
        for page in r["results"]:
            lead = _extract_lead(page)
            if not lead["name"]:
                continue
            if lead["pipeline_stage"] and lead["pipeline_stage"] not in ALLOWED_STAGES:
                continue
            results.append(lead)
            if len(results) >= 6:
                break
        return results
    except Exception as e:
        print(f"[notion] search_leads failed: {e}")
        return []


def link_session_to_lead(lead_page_id: str, session_id: str) -> None:
    if not available() or not lead_page_id:
        return
    try:
        n = _client()
        n.pages.update(
            page_id=lead_page_id,
            properties={
                "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
            },
        )
    except Exception as e:
        print(f"[notion] link_session_to_lead failed: {e}")


def write_qa_to_page(lead_page_id: str, round_num: int, qa_list: list) -> None:
    if not available() or not lead_page_id:
        return
    try:
        n = _client()
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
        n.blocks.children.append(block_id=lead_page_id, children=blocks)
    except Exception as e:
        print(f"[notion] write_qa_to_page failed: {e}")


def write_roi_to_page(lead_page_id: str, roi: dict, assumptions: list) -> None:
    if not available() or not lead_page_id:
        return
    try:
        n = _client()
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
        n.blocks.children.append(block_id=lead_page_id, children=blocks)
    except Exception as e:
        print(f"[notion] write_roi_to_page failed: {e}")
