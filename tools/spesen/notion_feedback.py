"""notion_feedback.py — best-effort mirror of KnowSpesen feedback into a Notion DB.

When NOTION_API_KEY + SPESEN_FEEDBACK_DB_ID are set, each new feedback also becomes
a row in the "KnowSpesen Feedback" Notion database (Operations Cockpit) so the
operator can read/triage in Notion. Fully best-effort: any failure (no env, no
access, network) just returns False and never blocks the DB store.
"""

from __future__ import annotations

import os

NOTION_VERSION = "2022-06-28"


def mirror(app_id: int, name: str, text: str, status: str = "Offen", datum_iso: str = "") -> bool:
    key = os.environ.get("NOTION_API_KEY", "")
    db = os.environ.get("SPESEN_FEEDBACK_DB_ID", "")
    if not key or not db:
        return False
    try:
        import requests
        props = {
            "Feedback": {"title": [{"text": {"content": (text or "")[:1900]}}]},
            "KnowBody": {"rich_text": [{"text": {"content": (name or "")[:200]}}]},
            "Status": {"select": {"name": status}},
            "App-ID": {"number": app_id},
        }
        if datum_iso:
            props["Datum"] = {"date": {"start": datum_iso}}
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers={"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VERSION,
                     "Content-Type": "application/json"},
            json={"parent": {"database_id": db}, "properties": props}, timeout=15)
        if r.status_code not in (200, 201):
            print(f"[spesen-feedback-notion] HTTP {r.status_code}: {r.text[:200]}", flush=True)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[spesen-feedback-notion] error={e!r}", flush=True)
        return False
