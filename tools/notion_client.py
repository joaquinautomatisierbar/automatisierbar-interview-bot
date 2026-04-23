"""notion_client.py — Notion session persistence for the automatisierbar survey app.

Each client session maps to one Notion database row. The full session state
(context, Q&A rounds, ROI, current questions) is stored as a JSON blob in the
"State" rich_text property, split into 2000-char chunks.

Required Notion database properties:
  - Name         (title)
  - Session ID   (rich_text)
  - Status       (select: active | complete)
  - State        (rich_text)

Env vars needed:  NOTION_API_KEY, NOTION_DATABASE_ID
"""

import json
import os
import uuid
from typing import Optional

CHUNK = 1999  # Notion rich_text element limit


def _client():
    from notion_client import Client
    return Client(auth=os.environ["NOTION_API_KEY"])


def _db() -> str:
    return os.environ["NOTION_DATABASE_ID"]


def _pack(state: dict) -> list:
    """Serialize state dict into list of Notion rich_text elements."""
    s = json.dumps(state, ensure_ascii=False)
    return [{"type": "text", "text": {"content": s[i:i + CHUNK]}}
            for i in range(0, len(s), CHUNK)]


def _unpack(rich_text: list) -> Optional[dict]:
    """Reconstruct state dict from Notion rich_text elements."""
    try:
        joined = "".join(r["text"]["content"] for r in rich_text)
        return json.loads(joined)
    except Exception:
        return None


def _find_page(session_id: str):
    """Return (page, notion_client) or (None, None)."""
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
# Public API
# ---------------------------------------------------------------------------

def create_session(context: str) -> str:
    """Create a Notion page for a new session. Returns session_id."""
    session_id = str(uuid.uuid4())
    state = {
        "session_id": session_id,
        "status": "active",
        "round": 0,
        "context": context,
        "all_qa": [],
        "current_questions": [],
        "roi": None,
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
    """Return session state dict, or None if not found."""
    page, _ = _find_page(session_id)
    if not page:
        return None
    return _unpack(page["properties"].get("State", {}).get("rich_text", []))


def update_session(session_id: str, updates: dict) -> None:
    """Merge updates into session state and save to Notion."""
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
    """Return True if Notion env vars are configured."""
    return bool(os.environ.get("NOTION_API_KEY") and os.environ.get("NOTION_DATABASE_ID"))
