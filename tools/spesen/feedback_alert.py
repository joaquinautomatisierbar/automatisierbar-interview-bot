"""feedback_alert.py — batched Telegram alert for KnowSpesen developer feedback.

VPS cron (every ~6h). Fires an operator Telegram alert ONLY when the open-feedback
backlog crosses a threshold:
  - more than 5 open items, OR
  - the oldest open item is older than 48h.
Deduped via app_meta.last_feedback_alert_at so it pings at most once per 24h. No
per-message spam. If Telegram creds are absent it just logs (never crashes the cron).

Usage:  python3 tools/spesen/feedback_alert.py            (live)
        python3 tools/spesen/feedback_alert.py --dry-run  (no send, prints decision)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

try:
    from . import db
except ImportError:  # pragma: no cover
    import db

OPEN_COUNT_THRESHOLD = 5      # alert when open count is GREATER than this
AGE_THRESHOLD_HOURS = 48      # alert when oldest open item is older than this
ALERT_DEDUP_HOURS = 24        # at most one alert per this many hours
META_KEY = "last_feedback_alert_at"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_utc(ts: str):
    """Parse a DB timestamp (SQLite 'YYYY-MM-DD HH:MM:SS' UTC, or an ISO tz string)
    to a naive UTC datetime, or None."""
    if not ts:
        return None
    ts = ts.strip().replace("Z", "")
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def oldest_age_hours(open_list: list, now_utc: datetime) -> float:
    ages = []
    for f in open_list:
        dt = _parse_utc(f.get("created_at", ""))
        if dt:
            ages.append((now_utc - dt).total_seconds() / 3600.0)
    return max(ages) if ages else 0.0


def evaluate(open_list: list, last_alert_iso: str, now_utc: datetime) -> dict:
    """Pure decision: should we alert now? Returns {alert, reason, count, oldest_h}."""
    count = len(open_list)
    oldest_h = oldest_age_hours(open_list, now_utc)
    threshold_hit = count > OPEN_COUNT_THRESHOLD or oldest_h > AGE_THRESHOLD_HOURS
    if not threshold_hit:
        return {"alert": False, "reason": "unter Schwelle", "count": count, "oldest_h": oldest_h}
    last = _parse_utc(last_alert_iso) if last_alert_iso else None
    if last and (now_utc - last).total_seconds() / 3600.0 < ALERT_DEDUP_HOURS:
        return {"alert": False, "reason": "kürzlich schon alarmiert", "count": count, "oldest_h": oldest_h}
    reason = []
    if count > OPEN_COUNT_THRESHOLD:
        reason.append(f"{count} offene Feedbacks")
    if oldest_h > AGE_THRESHOLD_HOURS:
        reason.append(f"ältestes {oldest_h:.0f}h alt")
    return {"alert": True, "reason": " + ".join(reason), "count": count, "oldest_h": oldest_h}


def build_message(open_list: list, decision: dict) -> str:
    lines = [f"🟡 KnowSpesen Feedback: {decision['reason']}.",
             f"{decision['count']} offen, ältestes {decision['oldest_h']:.0f}h.", ""]
    for f in open_list[:3]:
        who = f.get("name") or "?"
        txt = (f.get("text") or "").replace("\n", " ")[:160]
        lines.append(f"• {who}: {txt}")
    if len(open_list) > 3:
        lines.append(f"… und {len(open_list) - 3} weitere.")
    lines.append("")
    lines.append("Erledigen: Status im KnowSpesen-Feedback (Notion) auf Erledigt setzen oder im Hub unter /app/builds, dann verstummt der Alert.")
    return "\n".join(lines)


def _post_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram message. Isolated so tests monkeypatch it."""
    import requests
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text}, timeout=15)
    return r.ok


def sync_resolved_from_notion() -> int:
    """Pull resolved statuses from the shared KnowSpesen-Feedback Notion DB into SQLite.

    That Notion DB is the operator's (and the Hub's) triage surface: the Hub mirrors it inbound,
    and a human can set a row's Status to Erledigt there. Marking a build done in the Hub used to
    silence nothing here because triage never reached this SQLite. Now, before the alert counts, any
    feedback whose Notion row is resolved is closed in SQLite too, so a handled backlog stops nagging.
    Best-effort: returns the number resolved (0 when Notion is off/unreachable), never raises.
    """
    try:
        from . import notion_feedback
    except ImportError:  # pragma: no cover
        import notion_feedback
    resolved_ids = notion_feedback.fetch_resolved_app_ids()
    if not resolved_ids:
        return 0
    n = 0
    for f in db.open_feedback():
        fid = f.get("id")
        if fid in resolved_ids and db.resolve_feedback(fid):
            n += 1
    if n:
        print(f"[feedback-alert] {n} Feedback(s) via Notion-Status als erledigt synchronisiert")
    return n


def run(send: bool = True) -> dict:
    now = _now_utc()
    # Reflect triage done on the shared Notion feedback DB (the Hub's / operator's surface) BEFORE
    # counting, so a feedback already handled there no longer drives the alert (issue #8).
    sync_resolved_from_notion()
    open_list = db.open_feedback()
    decision = evaluate(open_list, db.meta_get(META_KEY) or "", now)
    print(f"[feedback-alert] open={decision['count']} oldest={decision['oldest_h']:.0f}h "
          f"alert={decision['alert']} ({decision['reason']})")
    if not decision["alert"]:
        return decision
    token = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID") or os.environ.get("COCKPIT_TEAM_CHAT_ID", "")
    msg = build_message(open_list, decision)
    if send and token and chat:
        try:
            if _post_telegram(token, chat, msg):
                db.meta_set(META_KEY, now.isoformat(timespec="seconds"))
                print("[feedback-alert] Telegram gesendet")
            else:
                print("[feedback-alert] Telegram send failed (non-ok)")
        except Exception as e:
            print(f"[feedback-alert] Telegram error: {e!r}")
    else:
        # mark as alerted even in dry-run? No — only on real send. Log the message.
        print("[feedback-alert] (kein Versand) Nachricht:\n" + msg)
    return decision


if __name__ == "__main__":
    run(send=("--dry-run" not in sys.argv))
