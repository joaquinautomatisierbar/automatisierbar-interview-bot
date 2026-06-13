#!/usr/bin/env python3
"""Tests for the pure decision helpers in tools/revenue_trigger.py.

The trigger fires exactly ONE downstream heartbeat (no loop), but only when the governor is
active, and it backs off (does NOT retry) on a rate-limit. Those two decisions are the logic
worth pinning; the subprocess shell around them is thin orchestration. Run:

    python3 tools/tests/test_revenue_trigger.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
import revenue_trigger as rt

fails = []
def chk(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + label + (f"  {extra}" if extra else ""))
    if not cond:
        fails.append(label)

# ── should_fire: only when governor status is active ─────────────────────────
ok, _ = rt.should_fire("active")
chk("should_fire: active → yes", ok is True)
for bad in ("tripped_spend", "tripped_time", "paused"):
    ok, why = rt.should_fire(bad)
    chk(f"should_fire: {bad} → no", ok is False, why)

# ── is_rate_limited: detect 429 / overloaded so we back off instead of looping ─
chk("rate-limit: 429 detected", rt.is_rate_limited("Error: HTTP 429 Too Many Requests") is True)
chk("rate-limit: 'rate limit' phrase", rt.is_rate_limited("you hit the rate limit, retry later") is True)
chk("rate-limit: overloaded", rt.is_rate_limited("rate_limit_error: overloaded_error") is True)
chk("rate-limit: clean output → false", rt.is_rate_limited("heartbeat run complete, 1 comment posted") is False)
chk("rate-limit: empty → false", rt.is_rate_limited("") is False)

print()
if fails:
    print(f"❌ {len(fails)} FAILED: {fails}")
    sys.exit(1)
print("✅ all revenue_trigger helper tests passed")
