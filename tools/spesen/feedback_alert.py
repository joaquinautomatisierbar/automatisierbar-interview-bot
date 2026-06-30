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
    return "\n".join(lines)


def _post_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram message. Isolated so tests monkeypatch it."""
    import requests
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text}, timeout=15)
    return r.ok


def run(send: bool = True) -> dict:
    now = _now_utc()
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
