"""Notion DB diff signal collector for the weekly LinkedIn brief.

Queries 4 known DBs and counts pages last_edited within [week_start, week_end):

  - Lead-DB / Interview-Datenbank   (NOTION_LEADS_DB_ID, fallback hardcoded)
  - LinkedIn Activity DB            (NOTION_LINKEDIN_DB_ID — optional)
  - Call Analytics DB               (NOTION_CALL_ANALYTICS_DB_ID — optional)
  - Weekly Call Reports DB          (NOTION_WEEKLY_REPORTS_DB_ID — optional)

For Lead-DB, also breaks down by Pipeline Stage transitions in the window.
For LinkedIn Activity, breaks down by Typ (Comment/Post/DM/Connection).

Best-effort: any DB that fails or is missing returns `available: false`.
Snapshot persistence is intentionally minimal — Notion `last_edited_time`
already gives us a reliable window filter, so we don't need delta state.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

import requests


NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"

# Hardcoded fallback (matches notion_session.py)
_LEADS_DB_FALLBACK = "31cbebb0-c2f9-8047-9e9f-fc59851f8a34"

DB_TARGETS = [
    {
        "key": "leads",
        "label": "Interview-Datenbank (Leads)",
        "env": "NOTION_LEADS_DB_ID",
        "fallback": _LEADS_DB_FALLBACK,
        "extract": "lead",
    },
    {
        "key": "linkedin_activity",
        "label": "LinkedIn Activity",
        "env": "NOTION_LINKEDIN_DB_ID",
        "fallback": None,
        "extract": "linkedin",
    },
    {
        "key": "call_analytics",
        "label": "Call Analytics",
        "env": "NOTION_CALL_ANALYTICS_DB_ID",
        "fallback": None,
        "extract": "call",
    },
    {
        "key": "weekly_reports",
        "label": "Weekly Call Reports",
        "env": "NOTION_WEEKLY_REPORTS_DB_ID",
        "fallback": None,
        "extract": "generic",
    },
]


def _headers() -> dict:
    key = os.environ.get("NOTION_API_KEY", "")
    if not key:
        raise RuntimeError("NOTION_API_KEY not set")
    return {
        "Authorization": f"Bearer {key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_db_filtered(database_id: str, edited_after_iso: str,
                       edited_before_iso: str, max_pages: int = 5) -> list[dict]:
    """Pull pages last_edited in [after, before). Cap at max_pages * 100 rows."""
    body_base: dict = {
        "filter": {
            "and": [
                {"timestamp": "last_edited_time",
                 "last_edited_time": {"on_or_after": edited_after_iso}},
                {"timestamp": "last_edited_time",
                 "last_edited_time": {"before": edited_before_iso}},
            ]
        },
        "page_size": 100,
    }
    out: list[dict] = []
    cursor: str | None = None
    for _ in range(max_pages):
        body = dict(body_base)
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(
            f"{API}/databases/{database_id}/query",
            headers=_headers(),
            json=body,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return out


def _extract_lead(page: dict) -> dict:
    p = page.get("properties", {})

    def _txt(k):
        rt = p.get(k, {}).get("rich_text", [])
        return rt[0].get("plain_text", "") if rt else ""

    def _title(k):
        t = p.get(k, {}).get("title", [])
        return t[0].get("plain_text", "") if t else ""

    def _sel(k):
        s = p.get(k, {}).get("select") or {}
        return s.get("name", "")

    def _stat(k):
        prop = p.get(k, {})
        s = prop.get("status") or prop.get("select") or {}
        return s.get("name", "")

    return {
        "name": _title("Name"),
        "firma": _txt("Firma"),
        "branche": _sel("Branche"),
        "pipeline_stage": _stat("Pipeline Stage"),
        "last_edited": page.get("last_edited_time", "")[:10],
    }


def _extract_linkedin(page: dict) -> dict:
    p = page.get("properties", {})

    def _sel(k):
        s = p.get(k, {}).get("select") or {}
        return s.get("name", "")

    def _txt(k):
        rt = p.get(k, {}).get("rich_text", [])
        return rt[0].get("plain_text", "") if rt else ""

    return {
        "typ": _sel("Typ"),
        "branche": _sel("Author-Branche"),
        "variant": _sel("Variante"),
        "outcome": _sel("Outcome"),
        "post_summary": _txt("Post-Summary")[:140],
        "last_edited": page.get("last_edited_time", "")[:10],
    }


def _extract_call(page: dict) -> dict:
    p = page.get("properties", {})

    def _sel(k):
        s = p.get(k, {}).get("select") or {}
        return s.get("name", "")

    def _stat(k):
        prop = p.get(k, {})
        s = prop.get("status") or prop.get("select") or {}
        return s.get("name", "")

    def _txt(k):
        rt = p.get(k, {}).get("rich_text", [])
        return rt[0].get("plain_text", "") if rt else ""

    return {
        "outcome": _stat("Outcome") or _sel("Outcome"),
        "branche": _sel("Branche"),
        "failure_mode": _sel("Failure Mode"),
        "firma": _txt("Firma"),
        "last_edited": page.get("last_edited_time", "")[:10],
    }


def _extract_generic(page: dict) -> dict:
    p = page.get("properties", {})

    def _title():
        for v in p.values():
            if v.get("type") == "title":
                t = v.get("title", [])
                return t[0].get("plain_text", "") if t else ""
        return ""

    return {
        "title": _title(),
        "last_edited": page.get("last_edited_time", "")[:10],
    }


_EXTRACTORS = {
    "lead": _extract_lead,
    "linkedin": _extract_linkedin,
    "call": _extract_call,
    "generic": _extract_generic,
}


def _fmt_iso(d: date) -> str:
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).isoformat()


def _summarize_db(target: dict, pages: list[dict]) -> dict[str, Any]:
    extract = _EXTRACTORS[target["extract"]]
    rows = [extract(pg) for pg in pages]

    summary: dict[str, Any] = {
        "label": target["label"],
        "key": target["key"],
        "row_count": len(rows),
        "available": True,
    }

    if target["extract"] == "lead":
        stages = Counter(r["pipeline_stage"] or "—" for r in rows)
        branchen = Counter(r["branche"] or "—" for r in rows)
        notable = [r for r in rows
                   if r["pipeline_stage"] in {"Pilot Client", "Prototype Building",
                                              "Prototype Testing", "Process Mapping"}]
        summary["pipeline_stages"] = dict(stages.most_common())
        summary["branchen_top"] = dict(branchen.most_common(5))
        summary["notable_rows"] = [
            {"firma": r["firma"], "branche": r["branche"], "stage": r["pipeline_stage"]}
            for r in notable[:10]
        ]
    elif target["extract"] == "linkedin":
        typen = Counter(r["typ"] or "—" for r in rows)
        outcomes = Counter(r["outcome"] or "—" for r in rows)
        summary["typ_breakdown"] = dict(typen.most_common())
        summary["outcome_breakdown"] = dict(outcomes.most_common())
        summary["sample_summaries"] = [r["post_summary"] for r in rows[:5] if r["post_summary"]]
    elif target["extract"] == "call":
        outcomes = Counter(r["outcome"] or "—" for r in rows)
        failures = Counter(r["failure_mode"] or "—" for r in rows if r["outcome"] != "Hot")
        summary["outcome_breakdown"] = dict(outcomes.most_common())
        summary["failure_mode_breakdown"] = dict(failures.most_common())
        summary["hot_leads"] = [
            {"firma": r["firma"], "branche": r["branche"]}
            for r in rows if r["outcome"] == "Hot"
        ][:10]
    else:
        summary["recent_titles"] = [r["title"] for r in rows[:10] if r["title"]]

    return summary


def collect(week_start: date, week_end: date) -> dict[str, Any]:
    """Return per-DB diff summaries. Best-effort — failures don't block."""
    after = _fmt_iso(week_start)
    before = _fmt_iso(week_end)

    if not os.environ.get("NOTION_API_KEY"):
        return {
            "available": False,
            "reason": "NOTION_API_KEY not set",
            "dbs": {},
        }

    dbs: dict[str, Any] = {}
    overall_count = 0
    for target in DB_TARGETS:
        db_id = os.environ.get(target["env"]) or target["fallback"]
        if not db_id:
            dbs[target["key"]] = {
                "label": target["label"],
                "available": False,
                "reason": f"{target['env']} not set",
                "row_count": 0,
            }
            continue
        try:
            pages = _query_db_filtered(db_id, after, before)
            summary = _summarize_db(target, pages)
            dbs[target["key"]] = summary
            overall_count += summary["row_count"]
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", "?")
            dbs[target["key"]] = {
                "label": target["label"],
                "available": False,
                "reason": f"HTTP {status}",
                "row_count": 0,
            }
        except Exception as e:
            dbs[target["key"]] = {
                "label": target["label"],
                "available": False,
                "reason": f"{type(e).__name__}: {e}",
                "row_count": 0,
            }

    return {
        "available": True,
        "total_pages_edited": overall_count,
        "dbs": dbs,
        "window": {"start": week_start.isoformat(), "end": week_end.isoformat()},
    }


if __name__ == "__main__":
    import json
    from datetime import timedelta
    today = date.today()
    result = collect(today - timedelta(days=7), today)
    print(json.dumps(result, indent=2, ensure_ascii=False))
