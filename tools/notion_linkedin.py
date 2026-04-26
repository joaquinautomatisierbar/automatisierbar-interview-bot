"""notion_linkedin.py — Notion integration for LinkedIn engagement bot.

Three responsibilities:
  1. top20_leads()           — Pull and rank top 20 leads from the Interview-Datenbank
  2. log_activity(...)       — Append a row to the LinkedIn Activity DB
  3. create_activity_db(...) — One-time setup: create the LinkedIn Activity DB

Reuses Notion plumbing from notion_session.py:
  - _notion_headers, _query_db, _rt, _leads_db
  - _extract_lead pattern (re-implemented to avoid circular import)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import requests

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"

PRIORITY_BRANCHEN = ["Recht", "Treuhand", "Immobilien", "Handwerk", "Beratung"]
EXCLUDE_STAGES = {"Pilot Client", "Paying Client"}

LINKEDIN_ACTIVITY_DB_ENV = "NOTION_LINKEDIN_DB_ID"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_db(database_id: str, page_size: int = 100, start_cursor: str | None = None) -> dict:
    body: dict = {"page_size": page_size}
    if start_cursor:
        body["start_cursor"] = start_cursor
    r = requests.post(f"{API}/databases/{database_id}/query", headers=_headers(), json=body)
    r.raise_for_status()
    return r.json()


def _rt(text: str) -> list:
    text = str(text or "")
    return [{"type": "text", "text": {"content": text[:1999]}}] if text else []


# ---------------------------------------------------------------------------
# Lead extraction (mirrors notion_session._extract_lead, kept independent)
# ---------------------------------------------------------------------------

def _lead_props(page: dict) -> dict:
    props = page["properties"]

    def title(k):
        t = props.get(k, {}).get("title", [])
        return t[0]["plain_text"] if t else ""

    def text(k):
        rt = props.get(k, {}).get("rich_text", [])
        return rt[0]["plain_text"] if rt else ""

    def select(k):
        s = props.get(k, {}).get("select") or {}
        return s.get("name", "")

    def status_or_select(k):
        prop = props.get(k, {})
        s = prop.get("status") or prop.get("select") or {}
        return s.get("name", "")

    return {
        "page_id": page["id"],
        "name": title("Name"),
        "firma": text("Firma"),
        "branche": select("Branche"),
        "groesse": select("Größe"),
        "top_problem": text("Top Problem"),
        "context": text("Context"),
        "problem_cluster": select("Problem Cluster"),
        "pipeline_stage": status_or_select("Pipeline Stage"),
    }


# ---------------------------------------------------------------------------
# 1) Top-20 lead ranking
# ---------------------------------------------------------------------------

_LEADS_DB_HARDCODED = "31cbebb0-c2f9-8075-b996-000b1747664a"  # Interview Datenbank


def _leads_db_id() -> str:
    # NOTION_DATABASE_ID is the Sessions DB on Render — do NOT use it here.
    # Use NOTION_LEADS_DB_ID if set, otherwise the hardcoded Interview Datenbank.
    return os.environ.get("NOTION_LEADS_DB_ID") or _LEADS_DB_HARDCODED


def top20_leads() -> list[dict]:
    """Return up to 20 leads ranked for LinkedIn engagement.

    Filter: pipeline_stage NOT in {Pilot Client, Paying Client}, must have firma.
    Sort:   priority branche first, then leads with top_problem populated.
    """
    leads: list[dict] = []
    cursor: str | None = None
    seen = 0
    # Pull up to 300 leads max to stay fast — adjust if DB is larger
    while seen < 300:
        page = _query_db(_leads_db_id(), page_size=100, start_cursor=cursor)
        for p in page.get("results", []):
            try:
                lead = _lead_props(p)
            except Exception:
                continue
            if not lead["firma"] or not lead["name"]:
                continue
            if lead["pipeline_stage"] in EXCLUDE_STAGES:
                continue
            leads.append(lead)
        cursor = page.get("next_cursor")
        seen += len(page.get("results", []))
        if not page.get("has_more") or not cursor:
            break

    def sort_key(lead: dict) -> tuple:
        branche_rank = (
            PRIORITY_BRANCHEN.index(lead["branche"])
            if lead["branche"] in PRIORITY_BRANCHEN
            else len(PRIORITY_BRANCHEN)
        )
        has_problem = 0 if lead["top_problem"].strip() else 1
        return (branche_rank, has_problem, lead["firma"].lower())

    leads.sort(key=sort_key)
    return leads[:20]


def linkedin_search_url(firma: str) -> str:
    """Build a LinkedIn People search URL for finding the owner of a company."""
    q = quote_plus(f"Inhaber {firma}".strip())
    return f"https://www.linkedin.com/search/results/people/?keywords={q}&origin=SWITCH_SEARCH_VERTICAL"


def format_top20_markdown(leads: list[dict]) -> str:
    """Format top-20 leads as a Telegram-friendly Markdown list."""
    if not leads:
        return "Keine passenden Leads gefunden."
    lines = [f"*Top {len(leads)} LinkedIn-Targets*\n"]
    for i, lead in enumerate(leads, 1):
        firma = lead["firma"]
        branche = lead["branche"] or "—"
        url = linkedin_search_url(firma)
        problem = lead["top_problem"][:80] + ("…" if len(lead["top_problem"]) > 80 else "")
        problem_line = f"\n  _{problem}_" if problem.strip() else ""
        lines.append(f"{i}. *{firma}* ({branche}) — [LinkedIn-Suche]({url}){problem_line}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2) Activity logging
# ---------------------------------------------------------------------------

def _activity_db_id() -> str:
    db_id = os.environ.get(LINKEDIN_ACTIVITY_DB_ENV, "").strip()
    if not db_id:
        raise RuntimeError(f"{LINKEDIN_ACTIVITY_DB_ENV} not set")
    return db_id


def log_activity(
    *,
    typ: str,                # "Comment" | "Post" | "DM" | "Connection"
    post_summary: str,
    branche: str = "Andere",
    variant: str = "keine",  # "Erfahrung" | "Sicht" | "Frage" | "keine"
    comment_text: str = "",
    post_source: str = "",
    outcome: str = "offen",
) -> dict:
    """Append one row to the LinkedIn Activity DB."""
    title = f"{typ} · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} · {(post_summary[:60]).strip()}"
    body = {
        "parent": {"database_id": _activity_db_id()},
        "properties": {
            "Name": {"title": [{"type": "text", "text": {"content": title[:1999]}}]},
            "Datum": {"date": {"start": datetime.now(timezone.utc).date().isoformat()}},
            "Typ": {"select": {"name": typ}},
            "Author-Branche": {"select": {"name": branche or "Andere"}},
            "Variante": {"select": {"name": variant or "keine"}},
            "Outcome": {"select": {"name": outcome or "offen"}},
            "Post-Quelle": {"rich_text": _rt(post_source)},
            "Post-Summary": {"rich_text": _rt(post_summary)},
            "Kommentar": {"rich_text": _rt(comment_text)},
        },
    }
    r = requests.post(f"{API}/pages", headers=_headers(), json=body)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# 3) One-time DB setup
# ---------------------------------------------------------------------------

def create_activity_db(parent_page_id: str) -> str:
    """Create the 'LinkedIn Activity' database under the given parent page.

    Returns the new database ID. After running, set NOTION_LINKEDIN_DB_ID to this value.
    """
    body = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "LinkedIn Activity"}}],
        "properties": {
            "Name": {"title": {}},
            "Datum": {"date": {}},
            "Typ": {
                "select": {
                    "options": [
                        {"name": "Comment", "color": "green"},
                        {"name": "Post", "color": "purple"},
                        {"name": "DM", "color": "blue"},
                        {"name": "Connection", "color": "yellow"},
                    ]
                }
            },
            "Author-Branche": {
                "select": {
                    "options": [
                        {"name": "Recht", "color": "blue"},
                        {"name": "Treuhand", "color": "green"},
                        {"name": "Immobilien", "color": "orange"},
                        {"name": "Handwerk", "color": "brown"},
                        {"name": "Beratung", "color": "purple"},
                        {"name": "Tech", "color": "pink"},
                        {"name": "Andere", "color": "default"},
                    ]
                }
            },
            "Variante": {
                "select": {
                    "options": [
                        {"name": "Erfahrung", "color": "green"},
                        {"name": "Sicht", "color": "blue"},
                        {"name": "Frage", "color": "purple"},
                        {"name": "keine", "color": "gray"},
                    ]
                }
            },
            "Outcome": {
                "select": {
                    "options": [
                        {"name": "offen", "color": "default"},
                        {"name": "Reaktion", "color": "green"},
                        {"name": "Profilbesuch", "color": "blue"},
                        {"name": "DM erhalten", "color": "purple"},
                        {"name": "nichts", "color": "gray"},
                    ]
                }
            },
            "Post-Quelle": {"rich_text": {}},
            "Post-Summary": {"rich_text": {}},
            "Kommentar": {"rich_text": {}},
        },
    }
    r = requests.post(f"{API}/databases", headers=_headers(), json=body)
    r.raise_for_status()
    return r.json()["id"]


# ---------------------------------------------------------------------------
# CLI for one-time setup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python notion_linkedin.py create-db <parent_page_id>")
        print("  python notion_linkedin.py top20")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "create-db":
        if len(sys.argv) < 3:
            print("Need parent_page_id (32-hex Notion page ID, with or without dashes)")
            sys.exit(1)
        page_id = sys.argv[2].replace("-", "")
        # Format with dashes
        formatted = f"{page_id[0:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:32]}"
        db_id = create_activity_db(formatted)
        print(f"Created DB: {db_id}")
        print(f"Set env var: NOTION_LINKEDIN_DB_ID={db_id}")
    elif cmd == "top20":
        leads = top20_leads()
        print(format_top20_markdown(leads))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
