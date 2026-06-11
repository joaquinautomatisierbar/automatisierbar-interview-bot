"""Git-log signal collector for the weekly LinkedIn brief.

Returns commits in [week_start, week_end) plus per-area buckets (workflows/,
tools/, prompts/, references/, decisions/) and the top 3 commits by churn.
Pure read-only `git log` — no mutation.
"""

from __future__ import annotations

import subprocess
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview")

AREA_PREFIXES = {
    "workflows": "workflows/",
    "tools": "tools/",
    "prompts": "prompts/",
    "references": "references/",
    "decisions": "decisions/",
    "claude": ".claude/",
    "api": "api.py",
    "frontend": "frontend/",
}

_FENCE = "===END==="


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command. Empty string on failure (signals are best-effort)."""
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if r.returncode != 0:
            return ""
        return r.stdout
    except Exception:
        return ""


def _bucket_for(path: str) -> str:
    for area, prefix in AREA_PREFIXES.items():
        if path.startswith(prefix):
            return area
    return "other"


def collect(week_start: date, week_end: date, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Collect git-log signals for the half-open window [week_start, week_end).

    Returns:
        {
          "commit_count": int,
          "commits": [{"sha": "...", "subject": "...", "date": "YYYY-MM-DD",
                       "files_changed": int, "insertions": int, "deletions": int,
                       "areas": ["workflows", "tools"]}, ...],
          "top_by_churn": [...same shape, max 3],
          "area_counts": {"workflows": 5, "tools": 12, ...},
          "available": True/False,
        }
    """
    if not (repo_root / ".git").exists():
        return _empty(reason="not a git repo")

    since = f"{week_start.isoformat()} 00:00:00"
    until = f"{week_end.isoformat()} 00:00:00"

    fmt = f"%H%x09%ad%x09%s{_FENCE}"
    raw = _run_git(
        ["log", f"--since={since}", f"--until={until}",
         f"--pretty=format:{fmt}", "--date=short", "--shortstat"],
        cwd=repo_root,
    )
    if not raw.strip():
        return _empty(reason="no commits in window")

    entries: list[dict[str, Any]] = []
    chunks = raw.split(_FENCE)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = [ln for ln in chunk.split("\n") if ln.strip()]
        if not lines:
            continue
        head = lines[0]
        parts = head.split("\t", 2)
        if len(parts) < 3:
            continue
        sha, dt, subject = parts[0], parts[1], parts[2]

        # Optional shortstat line: " 3 files changed, 12 insertions(+), 4 deletions(-)"
        files_changed = insertions = deletions = 0
        for ln in lines[1:]:
            ln = ln.strip()
            if "file" in ln and "changed" in ln:
                for tok in ln.split(","):
                    tok = tok.strip()
                    if "file" in tok:
                        files_changed = _first_int(tok)
                    elif "insertion" in tok:
                        insertions = _first_int(tok)
                    elif "deletion" in tok:
                        deletions = _first_int(tok)

        # Files-changed list for area buckets
        files_raw = _run_git(
            ["show", "--name-only", "--pretty=format:", sha],
            cwd=repo_root,
        )
        files = [f for f in files_raw.split("\n") if f.strip()]
        areas = sorted({_bucket_for(f) for f in files})

        entries.append({
            "sha": sha[:8],
            "subject": subject,
            "date": dt,
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "areas": areas,
        })

    # Area counts
    area_counts: Counter = Counter()
    for e in entries:
        for a in e["areas"]:
            area_counts[a] += 1

    top_by_churn = sorted(
        entries,
        key=lambda e: (e["insertions"] + e["deletions"]),
        reverse=True,
    )[:3]

    return {
        "available": True,
        "commit_count": len(entries),
        "commits": entries,
        "top_by_churn": top_by_churn,
        "area_counts": dict(area_counts),
        "window": {"start": week_start.isoformat(), "end": week_end.isoformat()},
    }


def _empty(reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "reason": reason,
        "commit_count": 0,
        "commits": [],
        "top_by_churn": [],
        "area_counts": {},
    }


def _first_int(s: str) -> int:
    digits = "".join(c for c in s if c.isdigit())
    return int(digits) if digits else 0


if __name__ == "__main__":
    # Self-test: scan last 7 days
    from datetime import timedelta
    today = date.today()
    result = collect(today - timedelta(days=7), today)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
