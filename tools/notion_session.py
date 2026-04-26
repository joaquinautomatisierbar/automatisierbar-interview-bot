"""notion_session.py — Notion session persistence + lead lookup for automatisierbar survey.

Renamed from notion_client.py to avoid shadowing the `notion-client` pip package.

Sessions database: NOTION_DATABASE_ID env var (separate sessions DB)
Leads database:    31cbebb0-c2f9-8075-b996-000b1747664a (Interview Datenbank)
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


def _client():
    from notion_client import Client
    return Client(auth=os.environ["NOTION_API_KEY"])


def _notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _query_db(database_id: str, filter_body: dict = None, page_size: int = 100) -> dict:
    body: dict = {"page_size": page_size}
    if filter_body:
        body["filter"] = filter_body
    r = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=_notion_headers(),
        json=body,
    )
    r.raise_for_status()
    return r.json()


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
        r = _query_db(
            _db(),
            filter_body={"property": "Session ID", "rich_text": {"equals": session_id}},
            page_size=1,
        )
        page = r["results"][0] if r["results"] else None
        return page, _client()
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
        r = _query_db(_leads_db(), page_size=100)
        q = query.lower()
        results = []
        for page in r["results"]:
            lead = _extract_lead(page)
            if not lead["name"]:
                continue
            if q not in lead["name"].lower() and q not in (lead["firma"] or "").lower():
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
