"""sync_company_state.py — pull live company state from Notion (+ git + decisions log)
into a flat snapshot at references/company-state/ that paperclip agents read via the
recall-learnings skill.

Outputs four files, each idempotent + overwritten on every run:

  references/company-state/founder-syncs.md   ← last 2 entries from Meeting Notes DB
  references/company-state/active-clients.md  ← Lead-DB filtered by Pipeline Stage
  references/company-state/this-week.md       ← aggregated 7-day signals
  references/company-state/team-capacity.md   ← derived from business-context + latest sync

Runs locally (operator MacBook) or on VPS (systemd timer). On VPS, output lands
directly in /home/paperclip/_context/references/company-state/ which is the
agent mount — no further sync needed.

Reuses tools/signals/*.py modules where possible. New inline helpers for the
Meeting Notes body pull + Lead-DB stage filter since those shapes aren't
covered by notion_diff.py (which is count-oriented).

Usage:
    python3 tools/sync_company_state.py                  # full refresh
    python3 tools/sync_company_state.py --dry-run        # no file writes
    python3 tools/sync_company_state.py --only founder   # only founder-syncs.md

Env vars:
    NOTION_API_KEY                  required
    MEETING_NOTES_DB_ID             optional, defaults to hardcoded Meeting Notes
    NOTION_LEADS_DB_ID              optional, defaults to hardcoded Lead-DB
    NOTION_CALL_ANALYTICS_DB_ID     optional
    NOTION_LINKEDIN_DB_ID           optional
    NOTION_WEEKLY_REPORTS_DB_ID     optional
    N8N_API_KEY                     optional (signal collector skips if missing)
    BRIEF_PERSON                    optional, defaults to Joaquin (affects team-capacity)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

# Repo root resolves whether run from MacBook or VPS mount.
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "references" / "company-state"

# Pull signal collectors that already exist
sys.path.insert(0, str(REPO_ROOT))
from tools.signals import notion_diff, decisions_signals, git_signals  # noqa: E402

try:
    from tools.signals import n8n_signals  # optional
except Exception:
    n8n_signals = None

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"

# Hardcoded fallbacks (override via env).
# NOTE: Meeting Notes DB has BOTH a database ID and a data source ID — the Notion
# REST API /v1/databases/{id}/query wants the DATABASE ID. The data source ID
# (collection://31cbebb0-c2f9-80d3-ab7f-000bf3f6dee1) is for MCP / view URLs only.
MEETING_NOTES_DB = "31cbebb0-c2f9-801b-ba71-c5144a5432da"  # Meeting Notes (Founder Sync DB)
LEADS_DB_FALLBACK = "31cbebb0-c2f9-8047-9e9f-fc59851f8a34"  # Lead-DB / Interview-DB

# Pipeline-Stage values we treat as "active client" — derived from actual Lead-DB
# schema (Pipeline Stage is a Notion status property). Verified 2026-06-01 against
# collection://31cbebb0-c2f9-8047-9e9f-fc59851f8a34. Operator can tune via env
# ACTIVE_CLIENT_STAGES (comma-separated) if the schema changes.
ACTIVE_CLIENT_STAGES = {
    "Paying Client",
    "Pilot Client",
    "Prototype Testing",
    "Prototype Building",
    "Process Mapping",
    "Workflow Interview",   # included — represents the active intake step
}
# Allow env override
_env_stages = os.environ.get("ACTIVE_CLIENT_STAGES", "")
if _env_stages:
    ACTIVE_CLIENT_STAGES = {s.strip() for s in _env_stages.split(",") if s.strip()}

# Per-file cap (bytes) — keeps recall-learnings context budget bounded
CAP_FOUNDER_SYNCS = 4500
CAP_ACTIVE_CLIENTS = 3500
CAP_THIS_WEEK = 3500
CAP_TEAM_CAPACITY = 1500

# Per-founder-sync entry cap (chars of body)
CAP_PER_SYNC = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M")


def _today() -> date:
    return date.today()


def _load_env_from_dotenv() -> None:
    """Minimal .env loader for local runs. On VPS systemd, env comes from EnvironmentFile."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def _notion_headers() -> dict:
    tok = os.environ.get("NOTION_API_KEY")
    if not tok:
        raise SystemExit("NOTION_API_KEY missing — cannot proceed.")
    return {
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _query_db(db_id: str, body: dict, limit: int = 50) -> list[dict]:
    """Page-respecting Notion query. Caller passes filter/sort."""
    out: list[dict] = []
    cursor: str | None = None
    while True:
        b = dict(body)
        if cursor:
            b["start_cursor"] = cursor
        b.setdefault("page_size", min(100, limit - len(out)))
        r = requests.post(
            f"{API}/databases/{db_id}/query",
            headers=_notion_headers(),
            json=b,
            timeout=20,
        )
        if r.status_code != 200:
            print(f"  WARN: Notion query {db_id[:8]} returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return out
        data = r.json()
        out.extend(data.get("results", []))
        if len(out) >= limit or not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return out[:limit]


def _fetch_page_blocks(page_id: str) -> list[dict]:
    """Fetch the body blocks of a Notion page (one level, no recursion into nested children).
    Good enough for the founder-sync flat-paragraph format observed in real entries."""
    out: list[dict] = []
    cursor: str | None = None
    for _ in range(5):  # at most ~500 blocks
        url = f"{API}/blocks/{page_id}/children"
        params = {"page_size": "100"}
        if cursor:
            params["start_cursor"] = cursor
        r = requests.get(url, headers=_notion_headers(), params=params, timeout=20)
        if r.status_code != 200:
            print(f"  WARN: block fetch {page_id[:8]} returned {r.status_code}", file=sys.stderr)
            break
        data = r.json()
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return out


def _block_to_text(block: dict) -> str:
    """Render a single Notion block into plain markdown-ish text. Lossy but readable."""
    btype = block.get("type", "")
    obj = block.get(btype, {}) or {}
    rt = obj.get("rich_text") or obj.get("text") or []
    text = "".join(rt_seg.get("plain_text", "") for rt_seg in rt)

    if not text and btype not in {"divider", "child_database"}:
        return ""

    if btype == "heading_1":
        return f"\n### {text}\n"
    if btype == "heading_2":
        return f"\n**{text}**\n"
    if btype == "heading_3":
        return f"\n_{text}_\n"
    if btype == "bulleted_list_item":
        return f"- {text}\n"
    if btype == "numbered_list_item":
        return f"1. {text}\n"
    if btype == "to_do":
        checked = "x" if obj.get("checked") else " "
        return f"- [{checked}] {text}\n"
    if btype == "quote":
        return f"> {text}\n"
    if btype == "code":
        return f"```\n{text}\n```\n"
    if btype == "divider":
        return "---\n"
    if btype == "paragraph":
        return f"{text}\n" if text else ""

    # File / image / embed / synced_block / etc. — drop
    return ""


# ────────────────────────────────────────────────────────────────────────────
# Cleaning helpers — strip noise from founder-sync bodies
# ────────────────────────────────────────────────────────────────────────────

# Drop standard KPI/definition glossary blocks that appear in the 2026-05-30 sync.
# These are reference definitions, not week-specific signal.
_KPI_NOISE_PATTERNS = [
    r"^KPI = Key Performance Indicator.*$",
    r"^EBITDA stands for Earnings Before Interest.*$",
    r"^\*\*SMB\*\* \(Small and Medium-Sized Business\).*$",
    r"^P&L Profit and Loss.*$",
    r"^Definitions:\s*$",
    r"^Marketing:\s*$",
    r"^Sales:\s*$",
    r"^Customer Service\s*$",
    r"^Operations & Project Management\s*$",
    r"^General Leadership\s*$",
    r"^CAC = .*$",
    r"^Conversion Rate = .*$",
    r"^CLV / LTV = .*$",
    r"^\*\*Lead Response Time:\*\*.*$",
    r"^\*\*Average Sales Cycle Time:\*\*.*$",
    r"^\*\*Monthly Recurring Revenue \(MRR\):\*\*.*$",
    r"^\*\*Net Promoter Score \(NPS\):\*\*.*$",
    r"^\*\*Customer Satisfaction Score \(CSAT\):\*\*.*$",
    r"^\*\*First Contact Resolution \(FCR\):\*\*.*$",
    r"^\*\*Order Fulfillment Time:\*\*.*$",
    r"^\*\*Resource Utilization Rate:\*\*.*$",
    r"^\*\*Inventory Turnover:\*\*.*$",
    r"^\*\*Profit Margin:\*\*.*$",
    r"^\*\*Employee Turnover Rate:\*\*.*$",
]

# Drop S3 image URLs, file:// attachments, prod-files-secure URLs
_URL_DROP_RE = re.compile(
    r"https?://(prod-files-secure\.s3\.|s3\.[a-z0-9-]+\.amazonaws\.com)\S+",
    re.IGNORECASE,
)


def _clean_sync_body(text: str) -> str:
    lines = text.splitlines()
    keep: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            keep.append("")
            continue
        if _URL_DROP_RE.search(line):
            line = _URL_DROP_RE.sub("[image]", line)
        if any(re.match(p, line) for p in _KPI_NOISE_PATTERNS):
            continue
        # Drop standalone tab-indented KPI lines under the dropped headings
        if line.startswith("\t") and any(
            kw in line for kw in (":", "%", "rate", "rate of")
        ) and any(kw in line for kw in ("CAC", "CLV", "MRR", "NPS", "Resolution")):
            continue
        keep.append(line)
    # Collapse 3+ consecutive blank lines
    cleaned: list[str] = []
    blanks = 0
    for l in keep:
        if not l.strip():
            blanks += 1
            if blanks <= 1:
                cleaned.append("")
        else:
            blanks = 0
            cleaned.append(l)
    return "\n".join(cleaned).strip()


# ────────────────────────────────────────────────────────────────────────────
# Builder 1 — founder-syncs.md
# ────────────────────────────────────────────────────────────────────────────


def build_founder_syncs(limit: int = 2) -> str:
    db = os.environ.get("MEETING_NOTES_DB_ID", MEETING_NOTES_DB)
    pages = _query_db(
        db,
        {
            "sorts": [{"property": "Date of Meeting", "direction": "descending"}],
            "page_size": min(10, limit * 3),
        },
        limit=limit * 3,
    )
    if not pages:
        return _frontmatter("founder-syncs", "Latest founder syncs from Meeting Notes DB", "notion") + \
               "\n_(no Meeting Notes pages found — DB may be empty or NOTION_API_KEY misconfigured)_\n"

    # Only keep entries that actually have a Date of Meeting set
    dated = []
    for p in pages:
        dprop = (p.get("properties", {}).get("Date of Meeting") or {}).get("date")
        d = (dprop or {}).get("start", "")[:10] if dprop else ""
        if d:
            dated.append((d, p))
        if len(dated) >= limit:
            break

    out = [_frontmatter("founder-syncs", f"Last {len(dated)} founder sync(s) from Meeting Notes DB", "notion")]
    out.append("")
    out.append("Format: each entry is the Notion page body, lightly cleaned (KPI/definition")
    out.append("boilerplate dropped, S3 image URLs collapsed). Read this first when planning")
    out.append("anything that depends on team state, active clients, or current priorities.")
    out.append("")

    for d, page in dated:
        page_id = page["id"]
        blocks = _fetch_page_blocks(page_id)
        raw = "".join(_block_to_text(b) for b in blocks)
        cleaned = _clean_sync_body(raw)
        if len(cleaned) > CAP_PER_SYNC:
            cleaned = cleaned[:CAP_PER_SYNC].rstrip() + "\n\n_(truncated for length cap)_"
        url = page.get("url", "")
        out.append("")
        out.append(f"## {d} Founder Sync")
        out.append("")
        if url:
            out.append(f"[source notion page]({url})")
            out.append("")
        out.append(cleaned)
        out.append("")

    text = "\n".join(out)
    if len(text) > CAP_FOUNDER_SYNCS:
        text = text[:CAP_FOUNDER_SYNCS].rstrip() + "\n\n_(file capped at " + str(CAP_FOUNDER_SYNCS) + " bytes)_\n"
    return text


# ────────────────────────────────────────────────────────────────────────────
# Builder 2 — active-clients.md
# ────────────────────────────────────────────────────────────────────────────


def _extract_lead_row(page: dict) -> dict:
    p = page.get("properties", {})

    def _txt(k: str) -> str:
        rt = p.get(k, {}).get("rich_text", [])
        return "".join(seg.get("plain_text", "") for seg in rt).strip()

    def _title(k: str) -> str:
        t = p.get(k, {}).get("title", [])
        return "".join(seg.get("plain_text", "") for seg in t).strip()

    def _sel(k: str) -> str:
        s = p.get(k, {}).get("select") or {}
        return s.get("name", "")

    def _stat(k: str) -> str:
        prop = p.get(k, {})
        s = prop.get("status") or prop.get("select") or {}
        return s.get("name", "")

    def _person(k: str) -> str:
        people = p.get(k, {}).get("people", [])
        return ", ".join(person.get("name", "") for person in people if person.get("name"))

    return {
        "name": _title("Name"),
        "firma": _txt("Firma"),
        "branche": _sel("Branche"),
        "stage": _stat("Pipeline Stage"),
        "owner": _person("Verantwortlich") or _person("Owner") or "",
        "last_edited": page.get("last_edited_time", "")[:10],
        "url": page.get("url", ""),
        "id": page.get("id", ""),
    }


def build_active_clients() -> str:
    db = os.environ.get("NOTION_LEADS_DB_ID", LEADS_DB_FALLBACK)
    # Server-side filter on Pipeline Stage — the Lead-DB has hundreds of cold
    # leads, so client-side filtering would miss active-stage rows past the first
    # page. Status property accepts `{"status": {"equals": "<name>"}}`.
    stage_filters = [
        {"property": "Pipeline Stage", "status": {"equals": s}}
        for s in sorted(ACTIVE_CLIENT_STAGES)
    ]
    pages = _query_db(
        db,
        {"filter": {"or": stage_filters}, "page_size": 100},
        limit=100,
    )
    rows = [_extract_lead_row(p) for p in pages]
    active = [r for r in rows if r["stage"] in ACTIVE_CLIENT_STAGES]

    # Sort by Pipeline Stage importance + last edited
    stage_order = {
        "Paying": 0, "Customer": 0,
        "Pilot live": 1, "Pilot running": 1, "Pilot in build": 2, "Pilot": 2,
        "Hot lead": 3, "Hot": 3,
        "Qualified": 4,
    }
    active.sort(key=lambda r: (stage_order.get(r["stage"], 99), r["last_edited"]), reverse=False)

    out = [_frontmatter(
        "active-clients",
        f"{len(active)} active client(s) from Lead-DB Pipeline Stage filter",
        "notion",
    )]
    out.append("")
    out.append("Clients in active stages: Paying / Pilot (in build, running, live) / Hot lead / Qualified.")
    out.append("Use this when planning a new build or interpreting a brief — knowing who's currently")
    out.append("in pilot prevents stack/scope/timing conflicts.")
    out.append("")

    if not active:
        out.append("_(no clients currently in active pipeline stages — Lead-DB may be empty or fully cold)_")
        return "\n".join(out)

    # Group by stage
    by_stage: dict[str, list[dict]] = {}
    for r in active:
        by_stage.setdefault(r["stage"], []).append(r)

    for stage in sorted(by_stage.keys(), key=lambda s: stage_order.get(s, 99)):
        out.append(f"## {stage} ({len(by_stage[stage])})")
        out.append("")
        for r in by_stage[stage]:
            name = r["firma"] or r["name"] or "(no name)"
            bits = [f"**{name}**"]
            if r["branche"]:
                bits.append(f"({r['branche']})")
            if r["owner"]:
                bits.append(f"— owner: {r['owner']}")
            if r["last_edited"]:
                bits.append(f"— last touched {r['last_edited']}")
            out.append("- " + " ".join(bits))
        out.append("")

    text = "\n".join(out)
    if len(text) > CAP_ACTIVE_CLIENTS:
        text = text[:CAP_ACTIVE_CLIENTS].rstrip() + "\n\n_(file capped at " + str(CAP_ACTIVE_CLIENTS) + " bytes)_\n"
    return text


# ────────────────────────────────────────────────────────────────────────────
# Builder 3 — this-week.md
# ────────────────────────────────────────────────────────────────────────────


def build_this_week() -> str:
    today = _today()
    week_end = today + timedelta(days=1)  # exclusive upper bound = tomorrow
    week_start = today - timedelta(days=7)

    # Git
    try:
        git_data = git_signals.collect(week_start, week_end)
    except Exception as e:
        git_data = {"available": False, "error": str(e)}

    # Decisions
    try:
        dec_data = decisions_signals.collect(week_start, week_end)
    except Exception as e:
        dec_data = {"available": False, "error": str(e)}

    # Notion diffs (Leads + Calls + LinkedIn + Weekly reports)
    try:
        notion_data = notion_diff.collect(week_start, week_end)
    except Exception as e:
        notion_data = {"available": False, "error": str(e)}

    # n8n executions (optional)
    n8n_data: dict[str, Any] = {"available": False}
    if n8n_signals is not None and os.environ.get("N8N_API_KEY"):
        try:
            n8n_data = n8n_signals.collect(week_start, week_end)
        except Exception as e:
            n8n_data = {"available": False, "error": str(e)}

    out = [_frontmatter(
        "this-week",
        f"7-day signals window: {week_start} → {today}",
        "git+decisions+notion+n8n",
    )]
    out.append("")
    out.append(f"Window: **{week_start}** → **{today}** (exclusive upper bound {week_end}).")
    out.append("")

    # Git
    out.append("## Code shipped")
    out.append("")
    if git_data.get("available", True) and git_data.get("commits_total", 0) > 0:
        out.append(f"- **{git_data.get('commits_total', 0)}** commits this window.")
        buckets = git_data.get("buckets") or {}
        for k, v in sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)[:5]:
            out.append(f"  - {k}: {v}")
        recent = git_data.get("recent") or []
        for c in recent[:3]:
            msg = c.get("subject", "")[:80] if isinstance(c, dict) else str(c)[:80]
            out.append(f"  - _{msg}_")
    else:
        out.append("- (no commits this window)")
    out.append("")

    # Decisions
    out.append("## Decisions logged")
    out.append("")
    if dec_data.get("available", True):
        entries = dec_data.get("entries") or []
        if entries:
            for e in entries[:5]:
                title = (e.get("title") or "").strip()[:100]
                out.append(f"- {title}")
        else:
            out.append("- (no `decisions/log.md` entries this window)")
    else:
        out.append(f"- (decisions signal unavailable: {dec_data.get('error', 'unknown')})")
    out.append("")

    # Notion
    out.append("## Notion movement (last 7 days)")
    out.append("")
    if notion_data.get("available", True):
        for key, info in (notion_data.get("dbs") or {}).items():
            if not info.get("available"):
                continue
            label = info.get("label", key)
            total = info.get("total", 0)
            out.append(f"- **{label}**: {total} pages edited")
            breakdown = info.get("breakdown") or {}
            if breakdown:
                for stage, count in list(breakdown.items())[:4]:
                    out.append(f"  - {stage}: {count}")
    else:
        out.append(f"- (notion signal unavailable: {notion_data.get('error', 'unknown')})")
    out.append("")

    # n8n
    if n8n_data.get("available"):
        out.append("## n8n executions (last 7 days)")
        out.append("")
        out.append(f"- Total executions: {n8n_data.get('total', 0)}")
        success_rate = n8n_data.get("success_rate")
        if success_rate is not None:
            out.append(f"- Success rate: {success_rate}")
        out.append("")

    text = "\n".join(out)
    if len(text) > CAP_THIS_WEEK:
        text = text[:CAP_THIS_WEEK].rstrip() + "\n\n_(file capped at " + str(CAP_THIS_WEEK) + " bytes)_\n"
    return text


# ────────────────────────────────────────────────────────────────────────────
# Builder 4 — team-capacity.md
# ────────────────────────────────────────────────────────────────────────────


def build_team_capacity() -> str:
    """Derive team capacity from business-context.md §6 + override notes from the latest sync.
    For v1 this is mostly a pointer + reminder — explicit override capture is later work."""
    out = [_frontmatter(
        "team-capacity",
        "Team availability + current commitments (derived view)",
        "business-context + meeting-notes",
    )]
    out.append("")
    out.append("Static team blocks from `references/business-context.md` §6. Override notes")
    out.append("from `founder-syncs.md` (last sync) take precedence when a team member is")
    out.append("flagged sick / on holiday / blocked.")
    out.append("")
    out.append("## Baseline (from business-context.md)")
    out.append("")
    out.append("- **Joaquin** — 16h/week until 2026-06-19, full-time afterward; CEO / founder, owns build pipeline")
    out.append("- **Nico** — full-time, owns cold-call + pilots")
    out.append("- **Tej** — ramping up, focused on customer meetings + Juglans")
    out.append("- **Patrik** — ramping up, cold calls + walk-ins")
    out.append("")
    out.append("All four start HSG study programme **2026-09-07** — capacity drops materially.")
    out.append("")
    out.append("## Active commitments (from latest founder sync)")
    out.append("")
    out.append("Read `founder-syncs.md` for the latest. Examples of what to look for there:")
    out.append("- Who's on which client this week (Bieri = Nico, Juglans = Tej, etc.)")
    out.append("- Blockers (e.g. Bieri install gated on customer's IT contact)")
    out.append("- Schedule changes (e.g. Joaquin's auto accident → no calling Friday)")
    out.append("")
    out.append("This file is a stable derivation — the founder syncs file is the authoritative")
    out.append("live signal. If the two disagree, the founder sync wins.")
    text = "\n".join(out)
    if len(text) > CAP_TEAM_CAPACITY:
        text = text[:CAP_TEAM_CAPACITY].rstrip() + "\n\n_(file capped at " + str(CAP_TEAM_CAPACITY) + " bytes)_\n"
    return text


# ────────────────────────────────────────────────────────────────────────────
# Frontmatter + INDEX
# ────────────────────────────────────────────────────────────────────────────


def _frontmatter(scope: str, description: str, source: str) -> str:
    return f"""---
name: company-state-{scope}
description: {description}
type: company-state
scope: {scope}
last_refreshed: {_now_iso()}
source: {source}
---

# Company State — {scope}
"""


def build_index() -> str:
    return f"""# Company State — Index

Live snapshot of company state, refreshed by `tools/sync_company_state.py` (runs daily on VPS via systemd timer). Read by every paperclip agent at activation via the `recall-learnings` skill.

**Last refreshed:** {_now_iso()}

## Files

- [founder-syncs.md](founder-syncs.md) — last 2 entries from Meeting Notes DB, lightly cleaned
- [active-clients.md](active-clients.md) — Lead-DB rows in active pipeline stages (Paying / Pilot / Hot / Qualified)
- [this-week.md](this-week.md) — 7-day signals: git commits, decisions log entries, Notion movement, n8n executions
- [team-capacity.md](team-capacity.md) — derived view of who's available + active commitments

## Refresh

- **Local:** `bash tools/paperclip/scripts/sync-company-state.sh`
- **VPS:** systemd timer fires twice daily (06:00 + 14:00 Europe/Zurich); see `install-linkedin-brief-vps.sh`

## Cleaning rules (founder syncs)

KPI/definition glossary blocks are dropped (the long "EBITDA stands for…" / "MRR / NPS / CSAT" lists). S3 attachment URLs are collapsed to `[image]`. Each entry is capped at {CAP_PER_SYNC} chars to keep the recall-learnings context budget bounded.
"""


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────


BUILDERS = {
    "founder-syncs": ("founder-syncs.md", build_founder_syncs),
    "active-clients": ("active-clients.md", build_active_clients),
    "this-week": ("this-week.md", build_this_week),
    "team-capacity": ("team-capacity.md", build_team_capacity),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="render but don't write files")
    ap.add_argument(
        "--only",
        choices=list(BUILDERS.keys()) + ["all"],
        default="all",
        help="render only one builder",
    )
    args = ap.parse_args(argv)

    _load_env_from_dotenv()

    if not os.environ.get("NOTION_API_KEY"):
        print("ERROR: NOTION_API_KEY not set (.env missing or empty?). Aborting.", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    selected = list(BUILDERS.keys()) if args.only == "all" else [args.only]

    written: list[tuple[str, int]] = []
    failed: list[str] = []
    for key in selected:
        filename, fn = BUILDERS[key]
        t0 = time.time()
        try:
            content = fn()
        except Exception as e:
            failed.append(f"{key}: {e}")
            print(f"  FAIL {key}: {e}", file=sys.stderr)
            continue
        dest = OUTPUT_DIR / filename
        if args.dry_run:
            print(f"  DRY-RUN would write {dest} ({len(content)} bytes, {time.time()-t0:.1f}s)")
        else:
            dest.write_text(content)
            print(f"  wrote {dest.relative_to(REPO_ROOT)} ({len(content)} bytes, {time.time()-t0:.1f}s)")
        written.append((filename, len(content)))

    # INDEX.md last
    if args.only == "all" and not args.dry_run:
        idx_path = OUTPUT_DIR / "INDEX.md"
        idx_path.write_text(build_index())
        print(f"  wrote {idx_path.relative_to(REPO_ROOT)}")

    total_bytes = sum(n for _, n in written)
    print(f"\n[sync-company-state] DONE. {len(written)} file(s), {total_bytes} bytes total. failed={len(failed)}")
    if failed:
        for f in failed:
            print(f"  FAIL: {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
