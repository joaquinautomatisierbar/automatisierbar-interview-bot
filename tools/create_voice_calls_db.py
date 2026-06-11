#!/usr/bin/env python3
"""One-off: create the Notion "Voice Calls" DB as a sibling of the Voice Sessions DB.

Durable per-call store for the cold-call Analyse page. Idempotent: if a "Voice Calls"
database already exists under the same parent page, prints its id instead of creating
a duplicate.

Run:  python3 tools/create_voice_calls_db.py
Then bake the printed id into api.py (VOICE_CALLS_DB_ID default).
"""
import os
import sys
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
VOICE_SESSIONS_DB_ID = os.environ.get(
    "VOICE_SESSIONS_DB_ID", "377bebb0-c2f9-8109-ad8b-c6aab96640dd")
NOTION_VERSION = "2022-06-28"


def _load_dotenv() -> None:
    """Idempotent .env loader (does NOT override already-set env vars)."""
    env_path = _REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"}


# Voice Calls schema — one row per fired call (connected AND no-answer).
PROPERTIES = {
    "Call": {"title": {}},
    "Call ID": {"rich_text": {}},
    "Date": {"date": {}},
    "Branche": {"select": {}},
    "Firma": {"rich_text": {}},
    "Lead ID": {"rich_text": {}},
    "Batch ID": {"rich_text": {}},
    "Script Version": {"select": {}},
    "Connected": {"checkbox": {}},
    "Bucket": {"select": {"options": [
        {"name": "hot", "color": "green"},
        {"name": "followup", "color": "yellow"},
        {"name": "cold", "color": "orange"},
        {"name": "hangup", "color": "red"},
        {"name": "noanswer", "color": "gray"},
        {"name": "auswerten", "color": "purple"},
    ]}},
    "Duration s": {"number": {}},
    "Cost CHF": {"number": {"format": "number"}},
    "Top Problem": {"rich_text": {}},
    "Schmerzscore": {"number": {}},
    "Payment": {"checkbox": {}},
    "Interview Completed": {"checkbox": {}},
    "Disclose AI": {"checkbox": {}},
}


def main() -> int:
    _load_dotenv()
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key:
        print("ERROR: NOTION_API_KEY not set (.env or env).", file=sys.stderr)
        return 1
    h = _headers(key)

    # 1. find the Voice Sessions DB parent page
    r = requests.get(f"https://api.notion.com/v1/databases/{VOICE_SESSIONS_DB_ID}",
                     headers=h, timeout=20)
    if not r.ok:
        print(f"ERROR fetching Voice Sessions DB: {r.status_code} {r.text[:300]}", file=sys.stderr)
        return 1
    parent = r.json().get("parent", {})
    if parent.get("type") != "page_id" or not parent.get("page_id"):
        print(f"ERROR: Voice Sessions DB parent is not a page ({parent}). "
              f"Set the target page manually.", file=sys.stderr)
        return 1
    parent_page = parent["page_id"]

    # 2. idempotency — reuse an existing "Voice Calls" DB under the same parent
    s = requests.post("https://api.notion.com/v1/search", headers=h,
                      json={"query": "Voice Calls", "filter": {"value": "database", "property": "object"}},
                      timeout=20)
    if s.ok:
        for res in s.json().get("results", []):
            title = "".join(t.get("plain_text", "") for t in res.get("title", []))
            p = res.get("parent", {})
            if title.strip() == "Voice Calls" and p.get("page_id") == parent_page:
                print(f"EXISTING Voice Calls DB found:\n  VOICE_CALLS_DB_ID = {res.get('id')}")
                return 0

    # 3. create the DB
    body = {
        "parent": {"type": "page_id", "page_id": parent_page},
        "title": [{"type": "text", "text": {"content": "Voice Calls"}}],
        "description": [{"type": "text", "text": {"content":
            "Durable per-call store for the cold-call Analyse page (one row per fired call)."}}],
        "properties": PROPERTIES,
    }
    c = requests.post("https://api.notion.com/v1/databases", headers=h, json=body, timeout=30)
    if not c.ok:
        print(f"ERROR creating DB: {c.status_code} {c.text[:400]}", file=sys.stderr)
        return 1
    new_id = c.json().get("id")
    print("CREATED Voice Calls DB ✓")
    print(f"  parent_page = {parent_page}")
    print(f"  VOICE_CALLS_DB_ID = {new_id}")
    print("\nNext: bake this id into api.py as the VOICE_CALLS_DB_ID default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
