#!/usr/bin/env python3
"""Revenue Lab one-shot agent trigger (Phase 0-1). Fires EXACTLY ONE downstream heartbeat —
no loop, no auto-flow — and only when the governor is active. Backs off (does NOT retry) on a
rate-limit so it never hammers the Claude Max quota. Records a run-count (compute is on the Max
plan, so we track runs + rate-limit headroom, not dollars).

Usage:
  python3 tools/revenue_trigger.py <agent_id> [--reason "<why>"]

Exit codes: 0 fired OK · 1 governor blocked (tripped/paused) · 2 rate-limited (backed off) ·
3 heartbeat failed.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import revenue_governor as rg  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_LOG = os.path.join(_HERE, "..", "data", "revenue_runs.json")
_NOTIFY_HOOK = os.path.join(_HERE, "..", ".claude", "hooks", "notify-telegram.sh")
PAPERCLIPAI = os.environ.get("PAPERCLIPAI", "npx paperclipai")

_RATE_LIMIT_TOKENS = ("429", "rate limit", "rate_limit", "overloaded", "too many requests")


# ── pure decisions (unit-tested) ─────────────────────────────────────────────
def should_fire(governor_status):
    """Only fire when the governor is active. A tripped/paused governor must block all wakes."""
    if governor_status == "active":
        return True, "governor active"
    return False, f"governor status is '{governor_status}' — wake blocked"


def is_rate_limited(text):
    low = (text or "").lower()
    return any(tok in low for tok in _RATE_LIMIT_TOKENS)


# ── thin orchestration ───────────────────────────────────────────────────────
def fire_once(agent_id, reason=""):
    """Fire a single heartbeat. Returns (returncode, combined_output)."""
    cmd = PAPERCLIPAI.split() + [
        "heartbeat", "run", "--agent-id", agent_id, "--source", "on_demand", "--trigger", "callback",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 99, f"trigger subprocess error: {e}"


def _record_run(agent_id, reason, rc, rate_limited):
    log = []
    if os.path.exists(RUNS_LOG):
        try:
            log = json.load(open(RUNS_LOG))
        except Exception:
            log = []
    log.append({
        "ts": datetime.now(timezone.utc).isoformat(), "agent_id": agent_id,
        "reason": reason, "rc": rc, "rate_limited": rate_limited,
    })
    os.makedirs(os.path.dirname(os.path.abspath(RUNS_LOG)), exist_ok=True)
    json.dump(log, open(RUNS_LOG, "w"), indent=2)
    return len(log)


def _halt(msg):
    try:
        subprocess.run(["bash", _NOTIFY_HOOK, "halt", msg], capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    agent_id = argv[0]
    reason = ""
    if "--reason" in argv:
        i = argv.index("--reason")
        reason = argv[i + 1] if i + 1 < len(argv) else ""

    status = rg.read_state().get("status", "active")
    ok, why = should_fire(status)
    if not ok:
        print(f"BLOCKED: {why}")
        return 1

    rc, out = fire_once(agent_id, reason)
    rate_limited = is_rate_limited(out)
    runs = _record_run(agent_id, reason, rc, rate_limited)

    if rate_limited:
        _halt(f"[revenue-lab] heartbeat for {agent_id} hit a rate limit — backed off (no retry). "
              f"Max-plan quota window likely exhausted; try again later.")
        print(f"RATE-LIMITED: backed off, no retry (run #{runs}). Tail:\n{out[-300:]}")
        return 2

    if rc != 0:
        print(f"HEARTBEAT FAILED rc={rc} (run #{runs}). Tail:\n{out[-300:]}")
        return 3

    print(f"fired heartbeat for {agent_id} (run #{runs}, reason='{reason}')")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
