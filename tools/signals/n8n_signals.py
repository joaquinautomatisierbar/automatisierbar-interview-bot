"""n8n execution-stats signal collector for the weekly LinkedIn brief.

Hits the n8n REST API directly. Best-effort: if N8N_API_KEY or N8N_BASE_URL
is missing, returns available=False without raising. Brief still ships.

Default base URL inferred from references/business-context.md:
  https://oojoaquin.app.n8n.cloud
Override via env var N8N_BASE_URL.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

import requests


DEFAULT_BASE_URL = "https://oojoaquin.app.n8n.cloud"


def _base_url() -> str:
    return os.environ.get("N8N_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _api_key() -> str | None:
    return os.environ.get("N8N_API_KEY")


def _headers(key: str) -> dict:
    return {
        "X-N8N-API-KEY": key,
        "Accept": "application/json",
    }


def _list_workflows(base: str, key: str) -> dict[str, str]:
    """Fetch workflow id→name map. Single best-effort API call.
    Returns empty dict on failure (callers use ID as fallback)."""
    out: dict[str, str] = {}
    try:
        cursor: str | None = None
        for _ in range(5):
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            r = requests.get(
                f"{base}/api/v1/workflows",
                headers=_headers(key),
                params=params,
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            for wf in data.get("data", []):
                wid = wf.get("id")
                wname = wf.get("name")
                if wid and wname:
                    out[wid] = wname
            cursor = data.get("nextCursor")
            if not cursor:
                break
    except Exception:
        pass
    return out


def _list_executions(after_iso: str, base: str, key: str,
                     max_pages: int = 5) -> list[dict]:
    """Page through /api/v1/executions, capping at max_pages * 100 rows."""
    out: list[dict] = []
    cursor: str | None = None
    for _ in range(max_pages):
        params: dict[str, Any] = {"limit": 100, "includeData": "false"}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(
                f"{base}/api/v1/executions",
                headers=_headers(key),
                params=params,
                timeout=20,
            )
            r.raise_for_status()
        except Exception:
            break
        data = r.json()
        page = data.get("data", [])
        if not page:
            break
        # n8n REST API doesn't support startedAfter filter in all versions —
        # we filter client-side. Stop once we drop below the window.
        keep_going = False
        for ex in page:
            started = ex.get("startedAt", "")
            if not started:
                continue
            if started >= after_iso:
                out.append(ex)
                keep_going = True
        cursor = data.get("nextCursor")
        if not cursor or not keep_going:
            break
    return out


def collect(week_start: date, week_end: date) -> dict[str, Any]:
    """Return execution counts + per-workflow + success/fail split."""
    key = _api_key()
    if not key:
        return {
            "available": False,
            "reason": "N8N_API_KEY not set (skip is fine)",
            "total": 0,
        }

    base = _base_url()
    after_iso = datetime.combine(week_start, datetime.min.time(),
                                 tzinfo=timezone.utc).isoformat()
    before_iso = datetime.combine(week_end, datetime.min.time(),
                                  tzinfo=timezone.utc).isoformat()

    try:
        execs = _list_executions(after_iso, base, key)
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}: {e}", "total": 0}

    in_window = [e for e in execs
                 if (e.get("startedAt", "") >= after_iso
                     and e.get("startedAt", "") < before_iso)]

    if not in_window:
        return {
            "available": True,
            "total": 0,
            "success": 0,
            "failure": 0,
            "by_workflow": {},
            "window": {"start": week_start.isoformat(), "end": week_end.isoformat()},
        }

    success = sum(1 for e in in_window if e.get("status") == "success")
    failure = sum(1 for e in in_window
                  if e.get("status") in ("error", "crashed", "failed"))

    # Resolve workflow IDs → human-readable names (single best-effort fetch).
    workflow_names = _list_workflows(base, key)

    def _wf_label(execution: dict) -> str:
        wid = execution.get("workflowId")
        name = (execution.get("workflowName")
                or workflow_names.get(wid or "")
                or wid
                or "unknown")
        return name

    by_workflow: Counter = Counter()
    by_workflow_status: dict[str, dict[str, int]] = {}
    for e in in_window:
        name = _wf_label(e)
        by_workflow[name] += 1
        status = e.get("status", "unknown")
        d = by_workflow_status.setdefault(name, {"success": 0, "failure": 0, "other": 0})
        if status == "success":
            d["success"] += 1
        elif status in ("error", "crashed", "failed"):
            d["failure"] += 1
        else:
            d["other"] += 1

    return {
        "available": True,
        "total": len(in_window),
        "success": success,
        "failure": failure,
        "by_workflow": dict(by_workflow.most_common(10)),
        "by_workflow_status": by_workflow_status,
        "window": {"start": week_start.isoformat(), "end": week_end.isoformat()},
    }


if __name__ == "__main__":
    import json
    from datetime import timedelta
    today = date.today()
    result = collect(today - timedelta(days=7), today)
    print(json.dumps(result, indent=2, ensure_ascii=False))
