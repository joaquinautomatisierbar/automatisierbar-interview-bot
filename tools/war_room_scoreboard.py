#!/usr/bin/env python3
"""War Room Daily-100 Scoreboard — Pace, Schulden & Telegram-Reveal.

The "Kein-Ausreden"-Zwangsfunktion for the 10-week outreach blitz. Reads the
"Daily 100 — War Room" Notion DB, computes the cumulative pace vs. the SOLL line
(IST − SOLL = SALDO; a missed day silently grows SOLL by DAILY_PACE → negative
SALDO = "hintendrein"), writes the result to the 1-row "War Room — Pace State"
DB, and posts a grayscale-safe public reveal to the team Telegram group.

Mental model (operator): over the 8-week remote offensive the team must rack up
TARGET_TOTAL reach-outs. That defines a daily pace (TARGET_TOTAL / WORKING_DAYS).
Skip a day and you're DAILY_PACE behind — and everyone sees it.

  Per-person daily target ("Rule of 100") = DAILY_PACE_PERSON (the aspiration).
  Team commitment / floor = TARGET_TOTAL over the window (the SALDO line).
  Both are tunable below. Default TARGET_TOTAL=4000 matches the operator's
  "−100 per missed day" model. For Rule-of-100 as the floor, set 16000.

Modes:
  python3 tools/war_room_scoreboard.py --selftest   # pace math, no Notion/Telegram
  python3 tools/war_room_scoreboard.py --dry-run     # read+compute+print only
  python3 tools/war_room_scoreboard.py               # PM reveal: write Notion + post
  python3 tools/war_room_scoreboard.py --mode kickoff # AM kickoff post

Env (all optional — sensible defaults baked in):
  NOTION_API_KEY              required for live read/write
  WAR_ROOM_DAILY_DB_ID        Daily-100 database id
  WAR_ROOM_PACE_DB_ID         Pace-State database id
  WAR_ROOM_TARGET_TOTAL       default 4000
  WAR_ROOM_DAILY_PACE         team pace/day, default 100
  WAR_ROOM_DAILY_PACE_PERSON  per-person ✓ threshold, default 100
  WAR_ROOM_WORKING_DAYS       default 40 (8 weeks × 5)
  WAR_ROOM_WINDOW_START       ISO date, default 2026-06-22 (first Monday)
  WAR_ROOM_BOT_TOKEN          Telegram bot token (must be in the team group);
                              falls back to OPERATOR_TELEGRAM_BOT_TOKEN
  WAR_ROOM_CHAT_ID            Telegram chat id, default -5026363666 (team group)
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
NOTION_VERSION = "2022-06-28"

PEOPLE = ["Nico", "Joaquin", "Tej", "Patrik"]

# --- Tunable constants (env overrides win) -------------------------------------
TARGET_TOTAL = int(os.environ.get("WAR_ROOM_TARGET_TOTAL", "4000"))
DAILY_PACE = int(os.environ.get("WAR_ROOM_DAILY_PACE", "100"))          # team/day
DAILY_PACE_PERSON = int(os.environ.get("WAR_ROOM_DAILY_PACE_PERSON", "100"))
WORKING_DAYS = int(os.environ.get("WAR_ROOM_WORKING_DAYS", "40"))
WINDOW_START = os.environ.get("WAR_ROOM_WINDOW_START", "2026-06-22")

# Database ids (with dashes) — created under the War Room hub page.
DAILY_DB_ID = os.environ.get("WAR_ROOM_DAILY_DB_ID", "779aa76b-a844-4187-9141-aed40ee72de9")
PACE_DB_ID = os.environ.get("WAR_ROOM_PACE_DB_ID", "42962f6c-9481-45ba-a3e8-d73b4ed3e149")

CHAT_ID = os.environ.get("WAR_ROOM_CHAT_ID", "-5026363666")

_WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


# --- .env loader (does not override already-set env) ---------------------------
def _load_dotenv() -> None:
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


def _notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_db_all(db_id: str, max_pages: int = 10) -> list:
    """Paginate a Notion database query. Returns all page objects."""
    results, cursor = [], None
    for _ in range(max_pages):
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=_notion_headers(), json=body, timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return results


# --- Pace math (pure, unit-testable) -------------------------------------------
def working_days_elapsed(start_iso: str, today: date) -> int:
    """Count Mon–Fri from start (inclusive) up to and including `today`.
    0 if the window hasn't started yet."""
    start = date.fromisoformat(start_iso)
    if today < start:
        return 0
    n, d = 0, start
    while d <= today:
        if d.weekday() < 5:  # Mon=0 .. Fri=4
            n += 1
        d += timedelta(days=1)
    return n


def compute_pace(ist: int, today: date):
    """Return (soll, saldo, day_index). SOLL = elapsed working days × DAILY_PACE,
    capped at TARGET_TOTAL. SALDO = IST − SOLL (negative = behind)."""
    elapsed = working_days_elapsed(WINDOW_START, today)
    soll = min(elapsed, WORKING_DAYS) * DAILY_PACE
    return soll, ist - soll, elapsed


# --- Notion read ----------------------------------------------------------------
def _num(props, key) -> int:
    v = props.get(key, {}).get("number")
    return int(v) if v else 0


def fetch_activity(today: date):
    """Read Daily-100 rows. Returns (per_person_today, team_today, ist_window).
    A 'touch' = Reach-outs + Walk-ins. Window = Datum in [WINDOW_START, today]."""
    rows = _query_db_all(DAILY_DB_ID)
    today_iso = today.isoformat()
    per_today = {p: 0 for p in PEOPLE}
    ist_window = 0
    for page in rows:
        props = page.get("properties", {})
        person = (props.get("Person", {}).get("select") or {}).get("name")
        datum = (props.get("Datum", {}).get("date") or {}).get("start")
        if not datum:
            continue
        datum = datum[:10]
        touches = _num(props, "Reach-outs") + _num(props, "Walk-ins")
        if WINDOW_START <= datum <= today_iso:
            ist_window += touches
        if datum == today_iso and person in per_today:
            per_today[person] += touches
    return per_today, sum(per_today.values()), ist_window


# --- Notion write (Pace State) --------------------------------------------------
def update_pace_state(ist: int, soll: int, saldo: int, status_line: str, today: date) -> None:
    """Upsert the single Pace-State row (matched by title 'Pace')."""
    rows = _query_db_all(PACE_DB_ID)
    page_id = None
    for page in rows:
        title = page.get("properties", {}).get("Stand", {}).get("title", [])
        if title and title[0].get("plain_text", "").strip() == "Pace":
            page_id = page["id"]
            break
    props = {
        "IST": {"number": ist},
        "SOLL": {"number": soll},
        "SALDO": {"number": saldo},
        "Status": {"rich_text": [{"text": {"content": status_line[:1999]}}]},
        "Aktualisiert": {"date": {"start": today.isoformat()}},
    }
    if page_id:
        r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}",
                           headers=_notion_headers(), json={"properties": props}, timeout=20)
    else:  # row missing — recreate it
        props["Stand"] = {"title": [{"text": {"content": "Pace"}}]}
        r = requests.post("https://api.notion.com/v1/pages", headers=_notion_headers(),
                          json={"parent": {"database_id": PACE_DB_ID}, "properties": props}, timeout=20)
    r.raise_for_status()


# --- Formatting (grayscale-safe: glyph + text, never color alone) --------------
def fmt(n: int) -> str:
    """Swiss thousands: 1750 -> 1'750."""
    return f"{n:,}".replace(",", "'")


def progress_bar(pct: float, width: int = 10) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def _saldo_line(saldo: int) -> str:
    if saldo > 0:
        return f"▲ {fmt(saldo)} Vorsprung — dranbleiben!"
    if saldo < 0:
        return f"▼ {fmt(-saldo)} hintendrein — aufholen!"
    return "● genau auf Pace"


def build_pm_message(per_today, team_today, ist, soll, saldo, day_index, today: date) -> str:
    dow = _WEEKDAYS_DE[today.weekday()]
    head = f"⚔️ WAR ROOM — Tag {day_index} ({dow} {today.strftime('%d.%m')})"
    if day_index == 0:
        return (f"{head}\n\nBlitz startet am {date.fromisoformat(WINDOW_START).strftime('%d.%m.%Y')}.\n"
                f"Ziel: {fmt(TARGET_TOTAL)} Reach-outs in {WORKING_DAYS} Arbeitstagen. Open to goal.")
    lines = [head, "", "Reach-outs heute (Ziel 100):"]
    for p in PEOPLE:
        n = per_today.get(p, 0)
        mark = "✓" if n >= DAILY_PACE_PERSON else "✗"
        gap = "" if n >= DAILY_PACE_PERSON else f"   ← {DAILY_PACE_PERSON - n} fehlen"
        lines.append(f"{mark} {p:<8}{fmt(n):>5}{gap}")
    pct = (ist / TARGET_TOTAL * 100) if TARGET_TOTAL else 0
    lines += [
        f"\nTeam heute: {fmt(team_today)}",
        f"\nPACE (Ziel {fmt(TARGET_TOTAL)} in {WORKING_DAYS} Tagen)",
        f"IST {fmt(ist)}  /  SOLL {fmt(soll)}",
        _saldo_line(saldo),
        f"Road to {fmt(TARGET_TOTAL)}: {pct:.0f}%  {progress_bar(pct)}",
        "\nOpen to goal. Keine Ausreden. 💪",
    ]
    return "\n".join(lines)


def build_kickoff_message(ist, soll, saldo, day_index, today: date) -> str:
    dow = _WEEKDAYS_DE[today.weekday()]
    if day_index == 0:
        return (f"⚔️ WAR ROOM — Countdown\n\nStart {date.fromisoformat(WINDOW_START).strftime('%d.%m.%Y')}. "
                f"Macht euch bereit: 100 Reach-outs/Tag, jeder.")
    return "\n".join([
        f"⚔️ WAR ROOM — Tag {day_index} ({dow} {today.strftime('%d.%m')})",
        "Ziel: 100 Reach-outs each. Open to goal — wir hören erst bei 100 auf.",
        f"Stand: {_saldo_line(saldo)} (IST {fmt(ist)} / SOLL {fmt(soll)})",
        "Los. 💪",
    ])


# --- Telegram -------------------------------------------------------------------
def send_telegram(text: str) -> bool:
    token = os.environ.get("WAR_ROOM_BOT_TOKEN") or os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN")
    if not token or not CHAT_ID:
        print("[war-room] Telegram token/chat missing — skipping post.", file=sys.stderr)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}, timeout=10,
    )
    if not r.ok:
        print(f"[war-room] Telegram error {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return False
    return True


# --- Selftest (pace math, no I/O) ----------------------------------------------
def selftest() -> int:
    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got}, want {want}")

    start = WINDOW_START  # 2026-06-22 is a Monday
    # 1 working day elapsed on the start Monday
    check("wd_start", working_days_elapsed(start, date(2026, 6, 22)), 1)
    # Mon..Fri of week 1 = 5 working days
    check("wd_fri", working_days_elapsed(start, date(2026, 6, 26)), 5)
    # weekend doesn't add
    check("wd_sun", working_days_elapsed(start, date(2026, 6, 28)), 5)
    # before start = 0
    check("wd_before", working_days_elapsed(start, date(2026, 6, 21)), 0)

    # Pace: on day 5, SOLL = 5×100 = 500. If IST=500 → saldo 0.
    soll, saldo, di = compute_pace(500, date(2026, 6, 26))
    check("soll_d5", soll, 500); check("saldo_even", saldo, 0); check("day5", di, 5)
    # Miss-a-day model: SOLL grows, IST flat → −100. On day 2 with IST still 100.
    soll2, saldo2, _ = compute_pace(100, date(2026, 6, 23))
    check("soll_d2", soll2, 200); check("saldo_minus100", saldo2, -100)
    # Cap: way past the window, SOLL caps at TARGET_TOTAL.
    soll3, _, _ = compute_pace(0, date(2026, 12, 31))
    check("soll_cap", soll3, TARGET_TOTAL)
    # Ahead: IST beats SOLL → positive.
    _, saldo4, _ = compute_pace(900, date(2026, 6, 23))
    check("saldo_ahead", saldo4, 700)

    # Formatting
    check("fmt", fmt(1750), "1'750")
    check("bar", progress_bar(50, 10), "█████░░░░░")

    if fails:
        print("SELFTEST FAILED:")
        for f in fails:
            print("  -", f)
        return 1
    print("SELFTEST PASSED ✓  (working-days, pace, miss-day=-100, cap, formatting)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="War Room Daily-100 scoreboard + reveal")
    ap.add_argument("--dry-run", action="store_true", help="read+compute+print only; no Notion write, no Telegram post")
    ap.add_argument("--selftest", action="store_true", help="run pace-math self-test, no I/O")
    ap.add_argument("--mode", choices=["pm", "kickoff"], default="pm", help="pm reveal (default) or am kickoff")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    _load_dotenv()
    if not os.environ.get("NOTION_API_KEY"):
        print("ERROR: NOTION_API_KEY not set (.env or env).", file=sys.stderr)
        return 1

    today = datetime.now().date()
    per_today, team_today, ist = fetch_activity(today)
    soll, saldo, day_index = compute_pace(ist, today)
    if day_index == 0:
        start_de = date.fromisoformat(WINDOW_START).strftime("%d.%m.%Y")
        status_line = f"Noch nicht gestartet — Start {start_de}. Ziel {fmt(TARGET_TOTAL)} in {WORKING_DAYS} Arbeitstagen."
    else:
        status_line = f"{_saldo_line(saldo)}  ·  IST {fmt(ist)} / SOLL {fmt(soll)}  ·  Tag {day_index}/{WORKING_DAYS}"

    if args.mode == "kickoff":
        msg = build_kickoff_message(ist, soll, saldo, day_index, today)
    else:
        msg = build_pm_message(per_today, team_today, ist, soll, saldo, day_index, today)

    if args.dry_run:
        print("--- DRY RUN (no writes, no post) ---")
        print(f"pace status: {status_line}")
        print("--- message ---")
        print(msg)
        return 0

    # Live: PM reveal persists the pace state; kickoff is post-only.
    if args.mode == "pm":
        try:
            update_pace_state(ist, soll, saldo, status_line, today)
        except Exception as e:
            print(f"[war-room] Pace-State update failed: {e}", file=sys.stderr)
    ok = send_telegram(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
