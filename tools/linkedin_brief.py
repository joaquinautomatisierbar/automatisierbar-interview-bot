"""linkedin_brief.py — orchestrator for the weekly LinkedIn content brief.

Aggregates 4 signal sources (git, decisions/log.md, Notion DB diffs,
n8n executions) → calls Claude for synthesis → writes the brief to a
Notion page in the "LinkedIn Content Briefs" DB → fires a Telegram
checkpoint with the page URL.

Usage examples:

    # Dry-run for last week (Mon-Sun ending most-recent Friday):
    python tools/linkedin_brief.py --dry-run

    # Specific week, real write:
    python tools/linkedin_brief.py --week-of 2026-05-09

    # Ad-hoc midweek run:
    python tools/linkedin_brief.py --week-of 2026-05-12

    # Synthetic fixture for testing (no live signal calls):
    python tools/linkedin_brief.py --dry-run --fixture .tmp/test_signals.json

    # Bootstrap the Notion DB once:
    python tools/linkedin_brief.py --bootstrap-db --parent-page-id <pid>

Environment variables:
    ANTHROPIC_API_KEY              required for synthesis
    NOTION_API_KEY                 required for any Notion read/write
    NOTION_BRIEFS_DB_ID            required for live write
    NOTION_LEADS_DB_ID             optional, falls back to hardcoded
    NOTION_LINKEDIN_DB_ID          optional, skipped if missing
    NOTION_CALL_ANALYTICS_DB_ID    optional, skipped if missing
    NOTION_WEEKLY_REPORTS_DB_ID    optional, skipped if missing
    N8N_API_KEY                    optional, skipped if missing
    N8N_BASE_URL                   defaults to https://oojoaquin.app.n8n.cloud
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Make `from tools.signals import …` resolvable when run as a script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import claude_client, notion_session  # noqa: E402
from tools.signals import (  # noqa: E402
    decisions_signals,
    git_signals,
    n8n_signals,
    notion_diff,
)


# ---------------------------------------------------------------------------
# .env loading (lightweight — avoids new dependency)
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """Load .env from the repo root if present. Idempotent.
    Doesn't override variables already set in the environment."""
    env_path = _REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception as e:
        print(f"[brief] .env load warning: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _previous_friday(today: date) -> date:
    """Return the most recent Friday on or before today."""
    # Mon=0, Fri=4
    delta = (today.weekday() - 4) % 7
    return today - timedelta(days=delta)


def _upcoming_friday(today: date) -> date:
    """Return the next Friday strictly after today, or today if it's Friday.
    Used by --create-page when Joaquin pre-creates next week's brief mid-week.
    """
    # Mon=0, Fri=4
    weekday = today.weekday()
    if weekday == 4:
        return today
    if weekday < 4:
        return today + timedelta(days=4 - weekday)
    return today + timedelta(days=4 - weekday + 7)


def _iso_week_label(d: date) -> str:
    iso = d.isocalendar()
    return f"KW-{iso.week:02d}"


# ---------------------------------------------------------------------------
# Telegram notification (best-effort)
# ---------------------------------------------------------------------------

def _fire_marketing_dispatcher(*, brief_url: str, brief_db_id: str,
                               post_variants_db_id: str, person: str,
                               iso_week: str) -> None:
    """POST to the Marketing PR Dispatcher n8n webhook (Phase 10).

    Fire-and-forget — failures don't break the brief flow. Gated by
    MARKETING_DISPATCHER_WEBHOOK_URL env var (so this stays a no-op until
    Phase 10 is wired in n8n).
    """
    import urllib.error
    import urllib.request

    webhook_url = os.environ.get("MARKETING_DISPATCHER_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return  # Phase 10 not yet activated

    payload = {
        "brief_url": brief_url,
        "brief_db_id": brief_db_id,
        "post_variants_db_id": post_variants_db_id,
        "person": person,
        "iso_week": iso_week,
    }
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[brief] marketing dispatcher fired: HTTP {resp.status}",
                  file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"[brief] marketing dispatcher fire failed (non-fatal): {e}",
              file=sys.stderr)
    except Exception as e:
        print(f"[brief] marketing dispatcher unexpected error (non-fatal): {e}",
              file=sys.stderr)


def _telegram(mode: str, msg: str) -> None:
    """Send a Telegram notification. Tries two paths in order:
       1. `.claude/hooks/notify-telegram.sh` if present (operator MacBook context — preserves
          tag/halt behavior wired through the hook)
       2. Direct HTTPS to Telegram Bot API (VPS context — hook script doesn't exist there)
       Silent on failure either way; brief generation never blocks on Telegram."""
    script = _REPO_ROOT / ".claude" / "hooks" / "notify-telegram.sh"
    if script.exists():
        try:
            subprocess.run(
                ["bash", str(script), mode, msg],
                cwd=str(_REPO_ROOT),
                timeout=10,
                capture_output=True,
                check=False,
            )
            return
        except Exception as e:
            print(f"[brief] telegram {mode} hook dispatch failed: {e}", file=sys.stderr)

    # Direct HTTP fallback (VPS systemd timer path).
    token = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    project = (_REPO_ROOT.name or "linkedin-brief").replace("_", " ")
    prefixed = f"[{project}] [{mode}] {msg}"
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": prefixed[:4000]},
            timeout=8,
        )
    except Exception as e:
        print(f"[brief] telegram {mode} HTTP dispatch failed: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Signal aggregation
# ---------------------------------------------------------------------------

@dataclass
class Window:
    start: date           # inclusive (Saturday of previous week)
    end: date             # exclusive (Saturday of current week / Friday +1)
    week_of: date         # Friday — the brief's "week of" anchor
    label: str            # "KW-19 · 2026-05-04 bis 2026-05-10"


def _build_window(week_of: date) -> Window:
    """Derive the 7-day window ending on `week_of` (Friday)."""
    end = week_of + timedelta(days=1)  # exclusive
    start = week_of - timedelta(days=6)
    label = f"{_iso_week_label(week_of)} · {start.isoformat()} bis {week_of.isoformat()}"
    return Window(start=start, end=end, week_of=week_of, label=label)


def collect_signals(window: Window) -> dict[str, Any]:
    """Run all signal collectors. Each is best-effort."""
    return {
        "week_label": window.label,
        "week_of": window.week_of.isoformat(),
        "git": git_signals.collect(window.start, window.end),
        "decisions": decisions_signals.collect(window.start, window.end),
        "notion": notion_diff.collect(window.start, window.end),
        "n8n": n8n_signals.collect(window.start, window.end),
    }


# ---------------------------------------------------------------------------
# Empty-week + stub-brief paths (no LLM call)
# ---------------------------------------------------------------------------

def _is_empty_week(signals: dict[str, Any]) -> bool:
    """True if every signal source reports zero meaningful activity."""
    g = signals["git"]
    d = signals["decisions"]
    n = signals["notion"]
    e = signals["n8n"]
    if g.get("commit_count", 0) > 0:
        return False
    if d.get("count", 0) > 0:
        return False
    if n.get("available") and n.get("total_pages_edited", 0) > 0:
        return False
    if e.get("available") and e.get("total", 0) > 0:
        return False
    return True


def _empty_brief(window: Window) -> str:
    return (
        f"# Brief {_iso_week_label(window.week_of)} · {window.week_of.isoformat()}\n\n"
        "## Zahlen der Woche\n"
        "- Stille Woche — keine signifikanten Builds oder Pipeline-Veränderungen.\n\n"
        "## Was gebaut wurde\n"
        "- Nichts erfasst in der Datenlage dieser Woche.\n\n"
        "## Strategische Entscheidungen\n"
        "- Keine neuen Decisions diese Woche.\n\n"
        "## Operative Wins\n"
        "- Keine messbaren Wins in der Pipeline diese Woche.\n\n"
        "## Post-Angle-Vorschläge\n\n"
        "Datenlage zu dünn für authentische Angles. Statt einen Post zu erzwingen: "
        "Vorschlag, einen Reflection-Post zu schreiben — *warum* es eine ruhige Woche "
        "war (Verkauf, Recovery, Ferien, Recherche). Oder die Woche überspringen.\n\n"
        "## Roh-Material\n\n"
        "```json\n{}\n```\n"
    )


def _stub_brief(window: Window, signals: dict[str, Any], reason: str) -> str:
    """Fallback when synthesis fails. Raw signals only, no Angles."""
    git = signals["git"]
    dec = signals["decisions"]
    notion = signals["notion"]
    n8n = signals["n8n"]
    body = [
        f"# Brief {_iso_week_label(window.week_of)} · {window.week_of.isoformat()} (STUB)\n",
        f"> ⚠ Synthese fehlgeschlagen: {reason}. Manuell überarbeiten.\n",
        "## Zahlen der Woche",
        f"- Commits: {git.get('commit_count', 0)}",
        f"- Decisions: {dec.get('count', 0)}",
        f"- Notion edits: {notion.get('total_pages_edited', 0)}",
        f"- n8n executions: {n8n.get('total', 0)}",
        "",
        "## Roh-Material\n",
        "```json",
        json.dumps({
            "git_commits": [c.get("subject", "") for c in git.get("commits", [])],
            "decisions": [{"date": e["date"], "title": e["title"]}
                          for e in dec.get("entries", [])],
            "notion_dbs": {
                k: {"row_count": v.get("row_count", 0)}
                for k, v in (notion.get("dbs") or {}).items()
            },
            "n8n_top": n8n.get("by_workflow", {}),
        }, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(body) + "\n"


# ---------------------------------------------------------------------------
# Brief building (synthesis or empty-week stub)
# ---------------------------------------------------------------------------

@dataclass
class BriefResult:
    body_md: str
    is_empty: bool
    is_stub: bool
    word_count: int
    error: str | None = None


def build_brief(signals: dict[str, Any], window: Window) -> BriefResult:
    """Decide which path to take and produce the brief markdown body."""
    if _is_empty_week(signals):
        body = _empty_brief(window)
        return BriefResult(body_md=body, is_empty=True, is_stub=False,
                           word_count=len(body.split()))

    try:
        body = claude_client.generate_linkedin_brief(signals)
    except claude_client.LinkedInBriefError as e:
        body = _stub_brief(window, signals, str(e))
        return BriefResult(body_md=body, is_empty=False, is_stub=True,
                           word_count=len(body.split()), error=str(e))

    return BriefResult(body_md=body, is_empty=False, is_stub=False,
                       word_count=len(body.split()))


# ---------------------------------------------------------------------------
# Body post-processing
# ---------------------------------------------------------------------------

_ROH_HEADER = "## Roh-Material"

# Tool/brand names the synthesis prompt forbids in prose. Allowed inside the
# Roh-Material JSON block (which preserves exact strings for the brand chat).
_FORBIDDEN_TOOL_TERMS = [
    "n8n", "Notion", "Apify", "Telegram",
    # Don't list "AI"/"KI" here — too many false positives in German compounds
    # ("AI-Klassifikation" appears in voice-reminders by design).
]


def _truncate_roh_material(body_md: str) -> str:
    """Drop the Roh-Material section to keep the brief under the word cap.
    The brand chat doesn't strictly need Roh-Material — angles + sections
    above carry the load. Returns body without the trailing JSON block."""
    idx = body_md.find(_ROH_HEADER)
    if idx == -1:
        return body_md.rstrip() + "\n"
    head = body_md[:idx].rstrip()
    return head + "\n\n" + _ROH_HEADER + "\n\n_(Roh-Material gekürzt — Brief war über 1000 Wörter.)_\n"


def _detect_tool_name_leaks(body_md: str) -> list[str]:
    """Return forbidden tool terms found in user-facing prose.

    USER-FACING = "Zahlen der Woche" / "Was gebaut wurde" /
    "Strategische Entscheidungen" / "Operative Wins" + the
    "Konkreter Aufhänger" and "Zahl/Story-Pointe" lines inside Angles
    (those become the post). META lines (Auslöser, Voice-Reminder) and
    fenced code blocks are excluded — synthesis prompt explicitly allows
    tool references there.
    """
    user_facing_sections = {
        "## Zahlen der Woche",
        "## Was gebaut wurde",
        "## Strategische Entscheidungen",
        "## Operative Wins",
    }
    angle_user_lines = ("**Konkreter Aufhänger", "**Zahl/Story-Pointe")
    angle_meta_lines = ("**Auslöser", "**Voice-Reminder", "**Hinweis")

    cleaned: list[str] = []
    in_code = False
    in_user_section = False
    in_angles = False

    for line in body_md.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Section tracking
        if stripped.startswith("## "):
            in_user_section = stripped in user_facing_sections
            in_angles = stripped == "## Post-Angle-Vorschläge"
            continue
        # Inside Angles, keep only the user-facing bullet lines
        if in_angles:
            # Strip leading "- "
            content = stripped.lstrip("- ").lstrip()
            if any(content.startswith(p) for p in angle_user_lines):
                cleaned.append(line)
            elif any(content.startswith(p) for p in angle_meta_lines):
                continue
            else:
                # Could be a heading like ### Angle 1 — H10 (...)
                # — those don't usually contain tool names; skip safely.
                continue
        elif in_user_section:
            cleaned.append(line)

    text = "\n".join(cleaned).lower()
    found = []
    for term in _FORBIDDEN_TOOL_TERMS:
        if term.lower() in text:
            found.append(term)
    return found


# ---------------------------------------------------------------------------
# Notion write path
# ---------------------------------------------------------------------------

def _brief_title(window: Window) -> str:
    return f"Brief {_iso_week_label(window.week_of)} · {window.week_of.isoformat()}"


_BACKUP_DIR = _REPO_ROOT / ".tmp"

# Status values that mean "the page is locked from auto-overwrite."
# Friday script refuses to merge or replace into these without --force.
_LOCKED_STATUSES = {"Reviewed", "Posted"}


def _read_status(page: dict) -> str:
    """Pull Status select value out of a Notion page object. Defaults to ''."""
    sel = (page.get("properties", {}).get("Status", {}) or {}).get("select") or {}
    return sel.get("name", "")


@dataclass
class NotionWriteResult:
    action: str           # "created" | "merged" | "replaced"
    url: str
    preserved_blocks: int = 0
    backups: list[Path] = None  # type: ignore[assignment]


def write_to_notion(*, briefs_db_id: str, window: Window, body: str,
                    signals: dict[str, Any], status: str,
                    force: bool) -> NotionWriteResult:
    """Create / merge / force-replace the brief page in Notion.

    Logic:
      • No existing page             → create. Status from arg.
      • Existing page, Status in
        {Draft, Skipped} (or empty)  → merge: preserve all user-native blocks,
                                       backup the existing synthesis code block
                                       to .tmp/, replace only that block.
                                       Status stays as-is unless arg overrides
                                       (we always set Status to arg's value so
                                       --status flag works for promotion).
      • Existing page, Status in
        {Reviewed, Posted}           → refuse unless force=True.
      • force=True                   → full overwrite: deletes ALL children,
                                       appends one fresh code block.
                                       No backup written. Bypasses Status check.

    Returns NotionWriteResult with action + url + preservation stats.
    """
    title = _brief_title(window)
    extra_props = {
        "Commit Count": {"number": int(signals["git"].get("commit_count", 0))},
        "Decision Count": {"number": int(signals["decisions"].get("count", 0))},
    }
    week_iso = window.week_of.isoformat()

    existing = notion_session.find_brief_for_week(briefs_db_id, week_iso)
    if not existing:
        page = notion_session.create_brief_page(
            briefs_db_id=briefs_db_id,
            week_of_iso=week_iso,
            title=title,
            body_md=body,
            status=status,
            extra_props=extra_props,
        )
        return NotionWriteResult(
            action="created", url=page.get("url", ""),
            preserved_blocks=0, backups=[],
        )

    existing_status = _read_status(existing)
    if existing_status in _LOCKED_STATUSES and not force:
        raise RuntimeError(
            f"Brief for {week_iso} is already Status={existing_status} at "
            f"{existing.get('url', '<unknown>')}. Re-run with --force to "
            "overwrite a reviewed/posted page (your edits will be lost)."
        )

    # Merge (force=False) or full replace (force=True)
    result = notion_session.replace_synthesis_block(
        existing["id"], body,
        backup_dir=_BACKUP_DIR if not force else None,
        force=force,
    )
    notion_session.update_brief_props(existing["id"], {
        "Status": {"select": {"name": status}},
        **extra_props,
    })
    return NotionWriteResult(
        action=result["action"],
        url=existing.get("url", ""),
        preserved_blocks=result["preserved_block_count"],
        backups=result["backups"],
    )


# ---------------------------------------------------------------------------
# Bootstrap helper
# ---------------------------------------------------------------------------

def bootstrap_db(parent_page_id: str) -> str:
    db_id = notion_session.create_briefs_db(parent_page_id)
    print(f"Created LinkedIn Content Briefs DB: {db_id}")
    print(f"Add to .env: NOTION_BRIEFS_DB_ID={db_id}")
    return db_id


def create_skeleton(briefs_db_id: str, week_of: date, status: str = "Draft") -> str:
    """Create the pre-Friday skeleton page for `week_of` (a Friday).

    Refuses if a brief already exists for that week.
    Returns the new page URL.
    """
    week_iso = week_of.isoformat()
    existing = notion_session.find_brief_for_week(briefs_db_id, week_iso)
    if existing:
        raise RuntimeError(
            f"Brief for {week_iso} already exists at "
            f"{existing.get('url', '<unknown>')}. Open it directly."
        )

    window = _build_window(week_of)
    title = _brief_title(window)

    page = notion_session.create_skeleton_page(
        briefs_db_id=briefs_db_id,
        week_of_iso=week_iso,
        title=title,
        week_label=window.label,
        status=status,
    )
    return page.get("url", "")


def ensure_auto_title_formula(briefs_db_id: str) -> None:
    """One-time DB schema augmentation: adds the Auto-Title formula property.
    Idempotent — Notion treats schema PATCH as upsert."""
    notion_session.add_auto_title_formula(briefs_db_id)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week-of", type=_parse_date, default=None,
                        help="Friday anchor date (YYYY-MM-DD). Default: most recent Friday.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print brief to stdout, don't write to Notion or send Telegram.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing brief for the same week.")
    parser.add_argument("--fixture", type=Path, default=None,
                        help="Load signals from this JSON file instead of collecting live.")
    parser.add_argument("--bootstrap-db", action="store_true",
                        help="Create the LinkedIn Content Briefs DB and exit.")
    parser.add_argument("--parent-page-id", type=str, default=None,
                        help="Parent page ID for --bootstrap-db.")
    parser.add_argument("--create-page", action="store_true",
                        help="Pre-create a skeleton brief page for the upcoming "
                             "Friday (or --week-of). Body has 'Wochen-Notizen' "
                             "heading; no synthesis. Friday-script merges into it.")
    parser.add_argument("--add-auto-title", action="store_true",
                        help="One-time: add the Auto-Title formula property to "
                             "the Briefs DB. Computes canonical title from Week Of.")
    parser.add_argument("--briefs-db-id", type=str, default=None,
                        help="Override NOTION_BRIEFS_DB_ID for this run (sandbox testing).")
    parser.add_argument("--post-variants-db-id", type=str, default=None,
                        help="Override NOTION_POST_VARIANTS_DB_ID — Marketing dept "
                             "target DB for post variant rows. Required for the "
                             "MARKETING_DISPATCHER_WEBHOOK_URL fire after the brief is written.")
    parser.add_argument("--person", type=str, default=None,
                        choices=["Joaquin", "Nico", "Tej", "Patrik"],
                        help="Which person this brief is for. Drives per-person "
                             "voice variant selection (Phase 11) + post-variants "
                             "Notion DB routing. Defaults to BRIEF_PERSON env or 'Joaquin'.")
    parser.add_argument("--status", type=str, default="Draft",
                        choices=["Draft", "Reviewed", "Posted", "Skipped"],
                        help="Initial Status property value.")
    parser.add_argument("--no-telegram", action="store_true",
                        help="Skip the Telegram checkpoint ping.")
    parser.add_argument("--no-dotenv", action="store_true",
                        help="Skip loading .env (testing: simulates missing env vars).")
    args = parser.parse_args(argv)

    if not args.no_dotenv:
        _load_dotenv()

    # ---- Bootstrap path
    if args.bootstrap_db:
        if not args.parent_page_id:
            print("--bootstrap-db requires --parent-page-id <pid>", file=sys.stderr)
            return 2
        try:
            bootstrap_db(args.parent_page_id)
            return 0
        except Exception as e:
            print(f"Bootstrap failed: {e}", file=sys.stderr)
            return 1

    # ---- One-time DB schema augmentation
    if args.add_auto_title:
        briefs_db_id = args.briefs_db_id or os.environ.get("NOTION_BRIEFS_DB_ID")
        if not briefs_db_id:
            print("NOTION_BRIEFS_DB_ID not set.", file=sys.stderr)
            return 2
        try:
            ensure_auto_title_formula(briefs_db_id)
            print(f"Auto-Title formula property added to DB {briefs_db_id}")
            return 0
        except Exception as e:
            print(f"add-auto-title failed: {e}", file=sys.stderr)
            return 1

    # ---- Pre-Friday skeleton page creation (idempotent — safe for cron)
    if args.create_page:
        briefs_db_id = args.briefs_db_id or os.environ.get("NOTION_BRIEFS_DB_ID")
        if not briefs_db_id:
            print("NOTION_BRIEFS_DB_ID not set.", file=sys.stderr)
            return 2
        week_of = args.week_of or _upcoming_friday(date.today())
        week_iso = week_of.isoformat()
        label = _iso_week_label(week_of)

        # Idempotent: if page already exists for this Friday, log + exit 0.
        existing = notion_session.find_brief_for_week(briefs_db_id, week_iso)
        if existing:
            url = existing.get("url", "")
            print(f"[brief] skeleton already exists for {label} · {week_iso} → {url}")
            return 0

        try:
            url = create_skeleton(briefs_db_id, week_of, status=args.status)
        except Exception as e:
            print(f"create-page failed: {e}", file=sys.stderr)
            if not args.no_telegram:
                _telegram(
                    "halt",
                    f"[linkedin-brief] Monday-create failed for {label} · {week_iso}: {e}",
                )
            return 1
        print(f"[brief] created skeleton: {label} · {week_iso} → {url}")
        if not args.no_telegram:
            _telegram(
                "checkpoint",
                f"[linkedin-brief] {label} · {week_iso} skeleton bereit. "
                f"Schreib deine Notizen rein: {url}",
            )
        return 0

    # ---- Resolve window
    week_of = args.week_of or _previous_friday(date.today())
    window = _build_window(week_of)
    print(f"[brief] window: {window.label}")

    # ---- Signal collection or fixture load
    if args.fixture:
        if not args.fixture.exists():
            print(f"Fixture not found: {args.fixture}", file=sys.stderr)
            return 2
        try:
            signals = json.loads(args.fixture.read_text(encoding="utf-8"))
            # Allow fixture to omit week_of
            signals.setdefault("week_label", window.label)
            signals.setdefault("week_of", window.week_of.isoformat())
            print(f"[brief] loaded fixture: {args.fixture}")
        except Exception as e:
            print(f"Fixture parse failed: {e}", file=sys.stderr)
            return 1
    else:
        try:
            signals = collect_signals(window)
        except Exception as e:
            print(f"Signal collection failed: {e}", file=sys.stderr)
            return 1

    print(f"[brief] git={signals['git'].get('commit_count', 0)} commits, "
          f"decisions={signals['decisions'].get('count', 0)}, "
          f"notion={signals['notion'].get('total_pages_edited', 0) if signals['notion'].get('available') else 'n/a'}, "
          f"n8n={signals['n8n'].get('total', 0) if signals['n8n'].get('available') else 'n/a'}")

    # ---- Pre-flight: live write needs the briefs DB. Refuse before burning a
    # Claude call on synthesis if we'd just refuse the write anyway.
    briefs_db_id = args.briefs_db_id or os.environ.get("NOTION_BRIEFS_DB_ID")
    if not args.dry_run and not briefs_db_id:
        print(
            "NOTION_BRIEFS_DB_ID not set. To bootstrap:\n"
            "  python tools/linkedin_brief.py --bootstrap-db "
            "--parent-page-id <notion-page-id>",
            file=sys.stderr,
        )
        return 2

    # ---- Build brief
    result = build_brief(signals, window)
    print(f"[brief] result: empty={result.is_empty} stub={result.is_stub} "
          f"words={result.word_count}")

    # ---- Word-count cap (truncate Roh-Material if needed)
    if result.word_count > 1000 and not result.is_empty and not result.is_stub:
        truncated = _truncate_roh_material(result.body_md)
        new_word_count = len(truncated.split())
        print(f"[brief] truncated Roh-Material: {result.word_count} → {new_word_count} words")
        result = BriefResult(
            body_md=truncated, is_empty=False, is_stub=False,
            word_count=new_word_count, error=result.error,
        )

    # ---- Prose-leak guard: warn if forbidden tool names slipped into prose
    leaks = _detect_tool_name_leaks(result.body_md)
    if leaks and not result.is_stub:
        print(f"[brief] WARN: forbidden tool names detected in prose: {leaks}")

    # ---- Output / Notion write
    if args.dry_run:
        print("\n" + "=" * 70)
        print("BRIEF (dry-run, not written to Notion):")
        print("=" * 70)
        print(result.body_md)
        if result.error:
            print(f"\n[brief] synthesis error (used stub): {result.error}",
                  file=sys.stderr)
            return 1
        return 0

    # briefs_db_id was already validated above for non-dry-run mode.
    status = args.status
    if result.is_empty and status == "Draft":
        status = "Skipped"

    try:
        wr = write_to_notion(
            briefs_db_id=briefs_db_id, window=window, body=result.body_md,
            signals=signals, status=status, force=args.force,
        )
    except Exception as e:
        print(f"[brief] Notion write failed: {e}", file=sys.stderr)
        if not args.no_telegram:
            _telegram("halt",
                      f"[linkedin-brief] {window.label}: write failed — {e}")
        return 1

    # Human-readable summary of what happened on the page
    if wr.action == "merged":
        backup_info = (f" Backup: {wr.backups[0]}" if wr.backups else
                       " (no prior synthesis to back up)")
        print(f"[brief] merged: preserved {wr.preserved_blocks} user block(s), "
              f"refreshed synthesis. {wr.url}{backup_info}")
    elif wr.action == "replaced":
        print(f"[brief] replaced (--force): all prior blocks dropped. {wr.url}")
    else:
        print(f"[brief] created: {wr.url}")

    if not args.no_telegram:
        if result.is_stub:
            _telegram(
                "halt",
                f"[linkedin-brief] {window.label} — synthesis FAILED, stub written. "
                f"Manual rewrite needed: {wr.url}",
            )
        elif result.is_empty:
            _telegram(
                "checkpoint",
                f"[linkedin-brief] {window.label} — stille Woche, Status=Skipped. "
                f"{wr.url}",
            )
        else:
            note = ""
            if wr.action == "merged" and wr.preserved_blocks > 0:
                note = f", {wr.preserved_blocks} Notizen-Block(e) erhalten"
            elif wr.action == "replaced":
                note = " (force replace)"
            _telegram(
                "checkpoint",
                f"[linkedin-brief] {window.label} {wr.action} "
                f"({result.word_count} Wörter, Status={status}{note}). {wr.url}",
            )

    # Phase 10: fire Marketing PR Dispatcher webhook so the marketing dept
    # produces post variants from the just-written brief. Gated by env var
    # — no-op until n8n's Marketing PR Dispatcher workflow is active.
    if not result.is_stub and not result.is_empty:
        post_variants_db_id = (
            args.post_variants_db_id
            or os.environ.get("NOTION_POST_VARIANTS_DB_ID", "")
        )
        person = args.person or os.environ.get("BRIEF_PERSON", "Joaquin")
        if post_variants_db_id:
            _fire_marketing_dispatcher(
                brief_url=wr.url,
                brief_db_id=briefs_db_id,
                post_variants_db_id=post_variants_db_id,
                person=person,
                iso_week=f"{window.week_of.year}-W{window.week_of.isocalendar().week:02d}",
            )

    return 1 if result.is_stub else 0


if __name__ == "__main__":
    sys.exit(main())
