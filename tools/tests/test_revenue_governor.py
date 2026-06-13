#!/usr/bin/env python3
"""Tests for tools/revenue_governor.py — the Revenue Lab $300 kill-switch + ledger.

Safety-critical: this proves the kill-switch trips (spend AND time/value) and pauses
agents BEFORE any real money or live company exists. Run:

    python3 tools/tests/test_revenue_governor.py     # exit 0 = all pass, 1 = failure

No pytest dependency — plain asserts in the project's existing test style.
"""
import os, sys, json, tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
import revenue_governor as rg

UTC = timezone.utc
T0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

fails = []
def chk(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + label + (f"  {extra}" if extra else ""))
    if not cond:
        fails.append(label)

def _tmp_ledger(state):
    fd, path = tempfile.mkstemp(suffix=".json", prefix="ledger_")
    os.close(fd)
    rg.write_state(state, path)
    return path

# ── default_state ────────────────────────────────────────────────────────────
st = rg.default_state(now=T0)
chk("default: cap_usd == 300", st["cap_usd"] == 300.0, str(st.get("cap_usd")))
chk("default: status active", st["status"] == "active")
chk("default: empty spend/revenue", st["spend"] == [] and st["revenue"] == [])
chk("default: zero totals", st["spent_usd"] == 0 and st["revenue_usd"] == 0)
chk("default: started_at set", st["started_at"] == T0.isoformat())

# ── _recompute + remaining_usd ───────────────────────────────────────────────
st2 = rg.default_state(now=T0)
st2["spend"] = [{"id": "a", "usd": 30.0}, {"id": "b", "usd": 20.0}]
st2["revenue"] = [{"id": "r1", "usd": 49.0}]
rg._recompute(st2)
chk("recompute: spent_usd == 50", st2["spent_usd"] == 50.0, str(st2["spent_usd"]))
chk("recompute: revenue_usd == 49", st2["revenue_usd"] == 49.0, str(st2["revenue_usd"]))
chk("remaining_usd == 250", rg.remaining_usd(st2) == 250.0, str(rg.remaining_usd(st2)))

# ── killswitch_verdict (pure) ────────────────────────────────────────────────
def mk(spent=0.0, revenue=0.0, days=0):
    s = rg.default_state(now=T0)
    if spent:   s["spend"] = [{"id": "s", "usd": spent}]
    if revenue: s["revenue"] = [{"id": "r", "usd": revenue}]
    rg._recompute(s)
    return s, T0 + timedelta(days=days)

s, now = mk(spent=100, revenue=0, days=5)
chk("verdict: under cap + recent → active", rg.killswitch_verdict(s, now) == "active")
s, now = mk(spent=300, revenue=0, days=1)
chk("verdict: spent>=cap → tripped_spend", rg.killswitch_verdict(s, now) == "tripped_spend")
s, now = mk(spent=300, revenue=0, days=30)
chk("verdict: spend trip beats time trip", rg.killswitch_verdict(s, now) == "tripped_spend")
s, now = mk(spent=0, revenue=0, days=21)
chk("verdict: 21d + zero revenue → tripped_time", rg.killswitch_verdict(s, now) == "tripped_time")
s, now = mk(spent=0, revenue=0, days=20)
chk("verdict: 20d + zero revenue → active (under 21d)", rg.killswitch_verdict(s, now) == "active")
s, now = mk(spent=0, revenue=10, days=30)
chk("verdict: revenue>0 → active even at 30d", rg.killswitch_verdict(s, now) == "active")

# ── preflight_can_spend ──────────────────────────────────────────────────────
p = _tmp_ledger(mk(spent=50, days=1)[0])
ok, _ = rg.preflight_can_spend(50, path=p, now=T0 + timedelta(days=1))
chk("preflight: est 50 within 250 headroom → ok", ok is True)
ok, why = rg.preflight_can_spend(300, path=p, now=T0 + timedelta(days=1))
chk("preflight: est 300 > headroom → blocked", ok is False, why)
ok, _ = rg.preflight_can_spend(250, path=p, now=T0 + timedelta(days=1))
chk("preflight: est == headroom → ok", ok is True)
tripped = mk(spent=300, days=1)[0]
tripped["status"] = "tripped_spend"
p2 = _tmp_ledger(tripped)
ok, why = rg.preflight_can_spend(1, path=p2, now=T0 + timedelta(days=1))
chk("preflight: tripped status → blocked", ok is False, why)

# ── check_killswitch invokes pause_fn ────────────────────────────────────────
calls = []
recorder = lambda **kw: calls.append(kw)

p = _tmp_ledger(mk(spent=300, days=1)[0])
v = rg.check_killswitch(path=p, now=T0 + timedelta(days=1), pause_fn=recorder)
persisted = rg.read_state(p)["status"]
chk("check_killswitch: spend trip returns tripped_spend", v == "tripped_spend", v)
chk("check_killswitch: status persisted", persisted == "tripped_spend", persisted)
chk("check_killswitch: pause_fn invoked once", len(calls) == 1, str(calls))

calls.clear()
p = _tmp_ledger(mk(spent=0, days=21)[0])
v = rg.check_killswitch(path=p, now=T0 + timedelta(days=21), pause_fn=recorder)
chk("check_killswitch: time trip returns tripped_time", v == "tripped_time", v)
chk("check_killswitch: time trip pauses", len(calls) == 1, str(calls))

calls.clear()
p = _tmp_ledger(mk(spent=50, days=2)[0])
v = rg.check_killswitch(path=p, now=T0 + timedelta(days=2), pause_fn=recorder)
chk("check_killswitch: active → no trip", v == "active", v)
chk("check_killswitch: active → no pause", len(calls) == 0, str(calls))

# ── record_spend: dedup + sum + auto-trip ────────────────────────────────────
p = _tmp_ledger(rg.default_state(now=T0))
rg.record_spend("x1", "tools", 10.0, note="api", path=p, now=T0)
rg.record_spend("x1", "tools", 10.0, note="dupe", path=p, now=T0)  # same id → ignored
s = rg.read_state(p)
chk("record_spend: dedup by id", s["spent_usd"] == 10.0, str(s["spent_usd"]))
chk("record_spend: id in counted", "x1" in s["counted"])
rg.record_spend("x2", "ads", 15.0, path=p, now=T0)
chk("record_spend: sums distinct ids", rg.read_state(p)["spent_usd"] == 25.0)

calls.clear()
p = _tmp_ledger(rg.default_state(now=T0))
rg.record_spend("big", "ads", 305.0, path=p, now=T0, pause_fn=recorder)
s = rg.read_state(p)
chk("record_spend: crossing cap auto-trips", s["status"] == "tripped_spend", s["status"])
chk("record_spend: crossing cap pauses", len(calls) == 1, str(calls))

# ── record_revenue: dedup + sum ──────────────────────────────────────────────
p = _tmp_ledger(rg.default_state(now=T0))
rg.record_revenue("ch_1", 49.0, "ch_stripe_1", note="first sale", path=p, now=T0)
rg.record_revenue("ch_1", 49.0, "ch_stripe_1", note="dupe", path=p, now=T0)
chk("record_revenue: dedup by id", rg.read_state(p)["revenue_usd"] == 49.0, str(rg.read_state(p)["revenue_usd"]))

# ── issue_spend ──────────────────────────────────────────────────────────────
p = _tmp_ledger(rg.default_state(now=T0))
rg.record_spend("i1", "tools", 3.0, issue_id="ISS-A", path=p, now=T0)
rg.record_spend("i2", "tools", 4.0, issue_id="ISS-A", path=p, now=T0)
rg.record_spend("i3", "tools", 9.0, issue_id="ISS-B", path=p, now=T0)
s = rg.read_state(p)
chk("issue_spend: sums per issue (A=7)", rg.issue_spend(s, "ISS-A") == 7.0, str(rg.issue_spend(s, "ISS-A")))
chk("issue_spend: isolates issues (B=9)", rg.issue_spend(s, "ISS-B") == 9.0)

# ── summary ──────────────────────────────────────────────────────────────────
print()
if fails:
    print(f"❌ {len(fails)} FAILED: {fails}")
    sys.exit(1)
print("✅ all governor tests passed")
