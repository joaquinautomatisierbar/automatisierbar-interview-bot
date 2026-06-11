"""Decisions-log signal collector for the weekly LinkedIn brief.

Parses decisions/log.md for entries in the [week_start, week_end) window.
Format expected (from decisions/log.md header):

    ## YYYY-MM-DD — Short title

    **Decision:** ...
    **Why:** ...
    **Alternatives considered:** ...
    **Owner:** ...

Returns deterministic entry list. No LLM, no mutation.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview")
LOG_PATH_DEFAULT = REPO_ROOT / "decisions" / "log.md"

# Heading: "## 2026-05-09 — Lead Scraper v2: …" or "## 2026-05-09 - …"
_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+[—\-–]\s+(.+?)\s*$")
# Field lines: "**Decision:** ...", "**Why:** ...", etc.
_FIELD_RE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")


def collect(week_start: date, week_end: date, log_path: Path = LOG_PATH_DEFAULT) -> dict[str, Any]:
    """Return {available, count, entries[]} for entries in [week_start, week_end)."""
    if not log_path.exists():
        return {"available": False, "reason": "log file missing", "count": 0, "entries": []}

    try:
        text = log_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"available": False, "reason": f"read failed: {e}", "count": 0, "entries": []}

    sections = _split_sections(text)
    in_window: list[dict[str, Any]] = []
    for sec in sections:
        try:
            d = datetime.strptime(sec["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if not (week_start <= d < week_end):
            continue
        in_window.append({
            "date": sec["date"],
            "title": sec["title"],
            "decision": sec.get("Decision", "").strip(),
            "why": sec.get("Why", "").strip(),
            "alternatives": _truncate(sec.get("Alternatives considered", "").strip(), 400),
            "owner": sec.get("Owner", "").strip(),
        })

    in_window.sort(key=lambda e: e["date"])
    return {
        "available": True,
        "count": len(in_window),
        "entries": in_window,
        "window": {"start": week_start.isoformat(), "end": week_end.isoformat()},
    }


def _split_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_field: str | None = None
    buf: list[str] = []

    def flush_field():
        nonlocal current_field, buf
        if current is not None and current_field is not None:
            current[current_field] = "\n".join(buf).strip()
        current_field = None
        buf = []

    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            flush_field()
            if current is not None:
                sections.append(current)
            current = {"date": m.group(1), "title": m.group(2)}
            continue
        if current is None:
            continue
        # Horizontal rule (---) separates sections — close out the current field
        # but don't start a new section yet (next ## heading does that).
        if line.strip() == "---":
            flush_field()
            continue
        m = _FIELD_RE.match(line)
        if m:
            flush_field()
            current_field = m.group(1).strip()
            buf = [m.group(2)]
            continue
        if current_field is not None:
            buf.append(line)
    flush_field()
    if current is not None:
        sections.append(current)
    return sections


def _truncate(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


if __name__ == "__main__":
    from datetime import timedelta
    today = date.today()
    result = collect(today - timedelta(days=14), today + timedelta(days=1))
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
