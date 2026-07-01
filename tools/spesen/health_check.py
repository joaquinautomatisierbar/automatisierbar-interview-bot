"""health_check.py — external uptime probe for KnowSpesen (VPS cron, ~every 10 min).

Hits the LIVE health URL (not localhost, so it exercises Caddy + gunicorn + the DB
end-to-end) and Telegram-alerts the operator on state CHANGES, not every tick:
  - OK  -> DOWN : alert once (service just went down / degraded)
  - DOWN -> OK  : alert once (recovered)
  - still DOWN  : re-remind every RE_REMINDER_HOURS so it isn't forgotten
The last state + last alert time live in app_meta (best-effort; if the DB itself is
the outage, we alert anyway rather than swallow it).

Usage:  python3 tools/spesen/health_check.py            (probe + alert)
        python3 tools/spesen/health_check.py --dry-run  (probe + print, no send)

Env:
  SPESEN_HEALTH_URL   what to probe (default https://knowspesen.automatisierbar.ch/api/spesen/health)
  OPERATOR_TELEGRAM_BOT_TOKEN / OPERATOR_TELEGRAM_CHAT_ID   alert channel
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

try:
    from . import db
except ImportError:  # pragma: no cover - direct-script run
    import db

DEFAULT_URL = "https://knowspesen.automatisierbar.ch/api/spesen/health"
HTTP_TIMEOUT = 15
RE_REMINDER_HOURS = 6
STATE_KEY = "last_health_state"          # "ok" | "down"
ALERT_KEY = "last_health_alert_at"       # iso utc


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def health_url() -> str:
    return os.environ.get("SPESEN_HEALTH_URL", DEFAULT_URL)


def probe(url: str) -> dict:
    """Return {up, code, status, detail}. up=True only on HTTP 200 + status 'ok'."""
    req = urllib.request.Request(url, headers={"User-Agent": "KnowSpesen-Healthcheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            code = resp.getcode()
            body = json.loads(resp.read().decode("utf-8"))
        status = body.get("status")
        return {"up": code == 200 and status == "ok", "code": code,
                "status": status, "detail": body.get("checks")}
    except urllib.error.HTTPError as e:
        # a 503 from the health route itself: read the degraded payload
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        return {"up": False, "code": e.code, "status": body.get("status") or "http_error",
                "detail": body.get("checks")}
    except Exception as e:
        return {"up": False, "code": None, "status": f"unreachable ({type(e).__name__})",
                "detail": None}


def _parse_utc(ts: str):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", ""))
    except ValueError:
        return None


def decide(result: dict, last_state: str | None, last_alert_iso: str | None, now: datetime) -> dict:
    """Pure: should we alert, and what's the new state?"""
    new_state = "ok" if result["up"] else "down"
    changed = (last_state or "ok") != new_state if last_state is not None else (not result["up"])
    alert = False
    reason = "keine Änderung"
    if changed:
        alert = True
        reason = "erholt" if new_state == "ok" else "AUSFALL"
    elif new_state == "down":
        last = _parse_utc(last_alert_iso or "")
        if not last or (now - last).total_seconds() / 3600.0 >= RE_REMINDER_HOURS:
            alert = True
            reason = "weiterhin AUSFALL"
    return {"alert": alert, "reason": reason, "new_state": new_state}


def build_message(result: dict, decision: dict) -> str:
    if decision["new_state"] == "ok":
        return "🟢 KnowSpesen ist wieder erreichbar."
    detail = ""
    if result.get("detail"):
        bad = [k for k, v in (result["detail"] or {}).items()
               if isinstance(v, str) and v not in ("ok",) and "error" in v]
        if bad:
            detail = " (" + ", ".join(bad) + ")"
    code = result.get("code")
    return (f"🔴 KnowSpesen {decision['reason']}: {result.get('status')}"
            f"{(' HTTP ' + str(code)) if code else ''}{detail}.")


def _post_telegram(text: str) -> bool:
    token = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID") or os.environ.get("COCKPIT_TEAM_CHAT_ID", "")
    if not token or not chat:
        print("[health] no Telegram creds, skipping alert")
        return False
    try:
        import requests
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": text}, timeout=15)
        return r.ok
    except Exception as e:
        print(f"[health] Telegram error: {e!r}")
        return False


def run(send: bool = True) -> dict:
    now = _now_utc()
    result = probe(health_url())
    try:
        last_state = db.meta_get(STATE_KEY)
        last_alert = db.meta_get(ALERT_KEY)
    except Exception:
        last_state, last_alert = None, None
    decision = decide(result, last_state, last_alert, now)
    print(f"[health] up={result['up']} code={result.get('code')} status={result.get('status')} "
          f"-> {decision['new_state']} alert={decision['alert']} ({decision['reason']})")

    if decision["alert"] and send:
        msg = build_message(result, decision)
        if _post_telegram(msg):
            try:
                db.meta_set(ALERT_KEY, now.isoformat(timespec="seconds"))
            except Exception:
                pass
            print("[health] Telegram gesendet: " + msg)
    elif decision["alert"]:
        print("[health] (kein Versand) " + build_message(result, decision))

    try:
        db.meta_set(STATE_KEY, decision["new_state"])
    except Exception:
        pass
    return {"result": result, "decision": decision}


if __name__ == "__main__":
    out = run(send=("--dry-run" not in sys.argv))
    sys.exit(0 if out["result"]["up"] else 1)
