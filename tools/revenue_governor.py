#!/usr/bin/env python3
"""Revenue Lab budget governor — the deterministic $300 kill-switch + ledger.

Replaces the toy data/cockpit_budget.json with a real, enforced ledger. This is CODE,
not an agent: agents consult it before spending (`preflight_can_spend` / `can-spend`) and
feed it after money moves (`record_spend` / `record_revenue`). It is the single guardrail
that protects the operator's $300 and prevents the documented burn incidents.

Two independent kill-switch trips (see killswitch_verdict):
  1. spent_usd >= cap_usd           → "tripped_spend"
  2. >=21 days AND revenue_usd == 0 → "tripped_time"  (the PRIMARY trip — Claude compute is
     on the Max plan, ~$0, so a fleet producing nothing won't trip on spend; time/value does)

On any trip, ALL Revenue Lab agents are paused (tools/paperclip/lib/pause_company.js) and the
operator is paged on Telegram. Compute is NOT dollar-tracked here (Max plan); the cap governs
external/business spend only (paid non-Claude APIs, ads, domains, tools, Stripe fees).

Inner caps (Cortana train loop): the SAME code guards a separate ledger via GOVERNOR_LEDGER. With
`set-caps`, a per-cycle cap (one night) and a trailing-30d month cap apply on top of the $300 master,
so the worst case before a breaker is the per-night cap. Off by default → Revenue Lab is unaffected.

CLI:
  python3 tools/revenue_governor.py status
  python3 tools/revenue_governor.py can-spend <usd>
  python3 tools/revenue_governor.py record-spend <id> <category> <usd> [note] [issue_id]
  python3 tools/revenue_governor.py record-revenue <id> <usd> <stripe_charge_id> [note]
  python3 tools/revenue_governor.py issue-spend <issue_id>
  python3 tools/revenue_governor.py trip-test     # really pauses live agents, then `reset`
  python3 tools/revenue_governor.py reset         # status -> active (does not wipe ledger)
  # train-loop inner caps (use GOVERNOR_LEDGER=data/train_ledger.json to keep separate from Revenue Lab):
  python3 tools/revenue_governor.py set-caps <cycle_cap|none> <month_cap|none>
  python3 tools/revenue_governor.py start-cycle <id> [cap_usd]
  python3 tools/revenue_governor.py end-cycle

Pure functions are unit-tested in tools/tests/test_revenue_governor.py (no network/no live).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

CAP_USD = 300.0
ZERO_REV_TRIP_DAYS = 21
# Inner caps for the Cortana self-improvement train loop. None = off (Revenue Lab leaves them off);
# the train loop runs against its own ledger (GOVERNOR_LEDGER=data/train_ledger.json) with these set,
# so a single night can't blow more than the cycle cap and a month can't exceed the month cap — the
# worst-case-before-breaker is the per-night cap, not the $300 master.
CYCLE_CAP_USD = None      # max external spend per nightly cycle (train loop: e.g. 15.0)
MONTH_CAP_USD = None      # max external spend per trailing 30 days (train loop: e.g. 50.0)
MONTH_WINDOW_DAYS = 30
UTC = timezone.utc

_HERE = os.path.dirname(os.path.abspath(__file__))
# GOVERNOR_LEDGER lets the train loop point the SAME code at a separate ledger from Revenue Lab's.
DEFAULT_LEDGER = os.environ.get("GOVERNOR_LEDGER") or os.path.join(_HERE, "..", "data", "revenue_ledger.json")
_PAUSE_HELPER = os.path.join(_HERE, "paperclip", "lib", "pause_company.js")
_NOTIFY_HOOK = os.path.join(_HERE, "..", ".claude", "hooks", "notify-telegram.sh")


# ── time helpers ──────────────────────────────────────────────────────────────
def _now(now=None):
    return now or datetime.now(UTC)


def _parse_dt(s):
    """Parse an ISO timestamp; tolerate a trailing 'Z' (Python 3.9 fromisoformat can't)."""
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def _days_since(started_at, now):
    return (now - _parse_dt(started_at)).total_seconds() / 86400.0


# ── state ────────────────────────────────────────────────────────────────────
def default_state(cap_usd=CAP_USD, now=None, company_id=None,
                  cycle_cap_usd=CYCLE_CAP_USD, month_cap_usd=MONTH_CAP_USD):
    return {
        "cap_usd": float(cap_usd),
        "started_at": _now(now).isoformat(),
        "status": "active",          # active | tripped_spend | tripped_time | paused
        "company_id": company_id,    # filled post-import; resolves the pause target
        "spend": [],                 # [{id, ts, category, usd, note, issue_id, cycle_id}]
        "revenue": [],               # [{id, ts, usd, stripe_charge_id, note}]
        "spent_usd": 0.0,
        "revenue_usd": 0.0,
        "counted": [],               # dedup ids across spend+revenue (idempotency)
        # ── inner caps for the train loop (None = off; checked only when set) ──
        "cycle_cap_usd": cycle_cap_usd,   # max external spend per nightly cycle
        "month_cap_usd": month_cap_usd,   # max external spend per trailing 30 days
        "active_cycle": None,             # {id, started_at, cap_usd} while a cycle is open
    }


def read_state(path=DEFAULT_LEDGER):
    if not os.path.exists(path):
        st = default_state()
        write_state(st, path)
        return st
    with open(path) as f:
        return json.load(f)


def write_state(state, path=DEFAULT_LEDGER):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def _recompute(state):
    state["spent_usd"] = round(sum(float(e.get("usd", 0)) for e in state.get("spend", [])), 2)
    state["revenue_usd"] = round(sum(float(e.get("usd", 0)) for e in state.get("revenue", [])), 2)
    return state


def remaining_usd(state):
    return round(float(state["cap_usd"]) - float(state.get("spent_usd", 0.0)), 2)


# ── kill-switch (pure) ───────────────────────────────────────────────────────
def killswitch_verdict(state, now=None):
    """Return 'active' | 'tripped_spend' | 'tripped_time' | 'paused'. Pure: reads the
    already-recomputed spent_usd/revenue_usd totals; never does I/O."""
    if state.get("status") == "paused":
        return "paused"
    if float(state.get("spent_usd", 0.0)) >= float(state["cap_usd"]):
        return "tripped_spend"
    if (_days_since(state["started_at"], _now(now)) >= ZERO_REV_TRIP_DAYS
            and float(state.get("revenue_usd", 0.0)) == 0):
        return "tripped_time"
    return "active"


def issue_spend(state, issue_id):
    return round(sum(float(e.get("usd", 0)) for e in state.get("spend", [])
                     if e.get("issue_id") == issue_id), 2)


# ── inner caps for the train loop (pure where possible) ───────────────────────
def month_spend(state, now=None):
    """External spend within the trailing MONTH_WINDOW_DAYS days (for the inner month cap)."""
    cutoff = _now(now) - timedelta(days=MONTH_WINDOW_DAYS)
    return round(sum(float(e.get("usd", 0)) for e in state.get("spend", [])
                     if e.get("ts") and _parse_dt(e["ts"]) >= cutoff), 2)


def cycle_spend(state, cycle_id=None):
    """Spend tagged to a cycle (defaults to the active cycle). 0 if no cycle."""
    cid = cycle_id if cycle_id is not None else (state.get("active_cycle") or {}).get("id")
    if cid is None:
        return 0.0
    return round(sum(float(e.get("usd", 0)) for e in state.get("spend", [])
                     if e.get("cycle_id") == cid), 2)


def start_cycle(cycle_id, cap_usd=None, path=DEFAULT_LEDGER, now=None):
    """Open a train cycle so the per-cycle cap applies. cap_usd overrides the ledger's cycle_cap_usd."""
    state = read_state(path)
    eff = float(cap_usd) if cap_usd is not None else state.get("cycle_cap_usd")
    state["active_cycle"] = {"id": cycle_id, "started_at": _now(now).isoformat(), "cap_usd": eff}
    write_state(state, path)
    return state["active_cycle"]


def end_cycle(path=DEFAULT_LEDGER):
    state = read_state(path)
    state["active_cycle"] = None
    write_state(state, path)
    return state


# ── enforcement (I/O) ────────────────────────────────────────────────────────
def preflight_can_spend(estimated_usd, path=DEFAULT_LEDGER, now=None):
    """(allowed: bool, reason: str). Agents MUST call this before any external spend. Enforces, in
    order: governor status, the $300 master cap, the trailing-30d month cap, and the active cycle cap.
    The inner caps are skipped when unset (None) so Revenue Lab is unaffected."""
    state = _recompute(read_state(path))
    effective = state["status"] if state["status"] != "active" else killswitch_verdict(state, now)
    if effective != "active":
        return False, f"governor status is '{effective}' — spending blocked"
    headroom = remaining_usd(state)
    est = float(estimated_usd)
    if est > headroom:
        return False, f"est ${est:.2f} exceeds remaining ${headroom:.2f} of ${state['cap_usd']:.0f} cap"
    mcap = state.get("month_cap_usd")
    if mcap is not None:
        mspent = month_spend(state, now)
        if mspent + est > float(mcap):
            return False, f"est ${est:.2f} would exceed month cap ${float(mcap):.0f} (spent ${mspent:.2f}/30d)"
    ac = state.get("active_cycle")
    if ac:
        ccap = ac.get("cap_usd")
        if ccap is None:
            ccap = state.get("cycle_cap_usd")
        if ccap is not None:
            cspent = cycle_spend(state, ac["id"])
            if cspent + est > float(ccap):
                return False, (f"est ${est:.2f} would exceed cycle cap ${float(ccap):.2f} "
                               f"(cycle '{ac['id']}' spent ${cspent:.2f})")
    return True, f"ok: ${headroom:.2f} master headroom"


def check_killswitch(path=DEFAULT_LEDGER, now=None, pause_fn=None):
    """Evaluate the kill-switch; on a trip, persist the status and pause all agents.
    pause_fn is injectable for tests; defaults to the real pause_all_agents."""
    pause_fn = pause_fn or pause_all_agents
    state = _recompute(read_state(path))
    if state["status"] == "paused":
        return "paused"
    verdict = killswitch_verdict(state, now)
    state["status"] = verdict
    write_state(state, path)
    if verdict != "active":
        try:
            pause_fn(company_id=state.get("company_id"), reason=verdict, state=state)
        except Exception as e:  # a pause failure must never crash the caller
            sys.stderr.write(f"[governor] pause_all_agents failed: {e}\n")
    return verdict


def record_spend(entry_id, category, usd, note="", issue_id=None, cycle_id=None,
                 path=DEFAULT_LEDGER, now=None, pause_fn=None):
    now = _now(now)
    state = read_state(path)
    if entry_id not in state["counted"]:
        cid = cycle_id if cycle_id is not None else (state.get("active_cycle") or {}).get("id")
        state["spend"].append({
            "id": entry_id, "ts": now.isoformat(), "category": category,
            "usd": float(usd), "note": note, "issue_id": issue_id, "cycle_id": cid,
        })
        state["counted"].append(entry_id)
    _recompute(state)
    write_state(state, path)
    check_killswitch(path=path, now=now, pause_fn=pause_fn)
    return read_state(path)


def record_revenue(entry_id, usd, stripe_charge_id, note="", path=DEFAULT_LEDGER, now=None):
    now = _now(now)
    state = read_state(path)
    if entry_id not in state["counted"]:
        state["revenue"].append({
            "id": entry_id, "ts": now.isoformat(), "usd": float(usd),
            "stripe_charge_id": stripe_charge_id, "note": note,
        })
        state["counted"].append(entry_id)
    _recompute(state)
    write_state(state, path)
    return read_state(path)


# ── pause (the hard kill-switch) ─────────────────────────────────────────────
def pause_all_agents(company_id=None, reason="", state=None, **_):
    """PATCH every Revenue Lab agent to enabled:false + wakeOnDemand:false via the Node
    helper that reuses lib/transport.js, then page the operator. Dry-run (no-op) when no
    company_id is configured yet (pre-import) so this is safe to call offline."""
    if not company_id:
        msg = f"[governor] kill-switch '{reason}' — DRY-RUN (no company_id configured yet)"
        sys.stderr.write(msg + "\n")
        return {"dry_run": True, "reason": reason, "paused": []}
    result = {"dry_run": False, "reason": reason}
    try:
        out = subprocess.run(
            ["node", _PAUSE_HELPER, company_id, reason],
            capture_output=True, text=True, timeout=60,
        )
        result["pause_helper_rc"] = out.returncode
        result["pause_helper_out"] = (out.stdout or out.stderr or "").strip()[:500]
    except Exception as e:
        result["pause_helper_error"] = str(e)
    # best-effort operator page (self-contained — no dependency on the hook being mounted)
    spent = state.get("spent_usd") if state else "?"
    rev = state.get("revenue_usd") if state else "?"
    result["notify"] = notify_operator(
        f"[revenue-lab] KILL-SWITCH TRIPPED ({reason}). All agents paused. "
        f"spent=${spent} revenue=${rev}. Reset via revenue_governor.py reset after review.")
    return result


def notify_operator(msg):
    """Best-effort operator page. Sends via the Telegram Bot API directly — Revenue Lab bot
    preferred (REVENUE_TELEGRAM_*), operator bot as fallback (OPERATOR_TELEGRAM_*); if neither
    is in env, falls back to the notify-telegram.sh hook. Never raises."""
    tok = os.environ.get("REVENUE_TELEGRAM_BOT_TOKEN") or os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("REVENUE_TELEGRAM_CHAT_ID") or os.environ.get("OPERATOR_TELEGRAM_CHAT_ID")
    if tok and chat:
        try:  # curl, not urllib — robust cert handling across macOS + Linux
            out = subprocess.run(
                ["curl", "-s", "-m", "15", "-X", "POST",
                 f"https://api.telegram.org/bot{tok}/sendMessage",
                 "--data-urlencode", f"chat_id={chat}", "--data-urlencode", f"text={msg}"],
                capture_output=True, text=True, timeout=20)
            return {"sent": '"ok":true' in (out.stdout or ""), "via": "telegram_api"}
        except Exception as e:
            return {"sent": False, "error": str(e)}
    try:
        subprocess.run(["bash", _NOTIFY_HOOK, "halt", msg], capture_output=True, text=True, timeout=30)
        return {"sent": True, "via": "hook"}
    except Exception as e:
        return {"sent": False, "error": str(e)}


def _resolve_company_id(state):
    return state.get("company_id") or os.environ.get("REVENUE_LAB_COMPANY_ID")


# ── CLI ──────────────────────────────────────────────────────────────────────
def _cli(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]

    if cmd == "status":
        st = _recompute(read_state())
        days = round(_days_since(st["started_at"], _now()), 1)
        out = {
            "status": st["status"], "cap_usd": st["cap_usd"],
            "spent_usd": st["spent_usd"], "revenue_usd": st["revenue_usd"],
            "remaining_usd": remaining_usd(st), "days_elapsed": days,
            "live_verdict": killswitch_verdict(st), "company_id": st.get("company_id"),
        }
        if st.get("month_cap_usd") is not None:
            out["month_cap_usd"] = st["month_cap_usd"]
            out["month_spent_usd"] = month_spend(st)
        if st.get("cycle_cap_usd") is not None or st.get("active_cycle"):
            out["cycle_cap_usd"] = st.get("cycle_cap_usd")
            out["active_cycle"] = st.get("active_cycle")
            if st.get("active_cycle"):
                out["cycle_spent_usd"] = cycle_spend(st)
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "set-caps":   # set-caps <cycle_cap|none> <month_cap|none>
        st = read_state()
        st["cycle_cap_usd"] = None if args[0].lower() in ("none", "off", "-") else float(args[0])
        st["month_cap_usd"] = None if args[1].lower() in ("none", "off", "-") else float(args[1])
        write_state(st, DEFAULT_LEDGER)
        print(f"caps set: cycle={st['cycle_cap_usd']} month={st['month_cap_usd']} (ledger {DEFAULT_LEDGER})")
        return 0

    if cmd == "start-cycle":   # start-cycle <id> [cap_usd]
        cap = float(args[1]) if len(args) > 1 else None
        ac = start_cycle(args[0], cap_usd=cap)
        print(f"cycle '{ac['id']}' open, cap=${ac['cap_usd']}")
        return 0

    if cmd == "end-cycle":
        end_cycle()
        print("cycle closed")
        return 0

    if cmd == "can-spend":
        ok, why = preflight_can_spend(float(args[0]))
        print(("OK " if ok else "BLOCKED ") + why)
        return 0 if ok else 1

    if cmd == "record-spend":
        eid, cat, usd = args[0], args[1], float(args[2])
        note = args[3] if len(args) > 3 else ""
        issue = args[4] if len(args) > 4 else None
        st = record_spend(eid, cat, usd, note=note, issue_id=issue)
        print(f"recorded spend ${usd:.2f} ({cat}); status={st['status']} remaining=${remaining_usd(st):.2f}")
        return 0

    if cmd == "record-revenue":
        eid, usd, charge = args[0], float(args[1]), args[2]
        note = args[3] if len(args) > 3 else ""
        st = record_revenue(eid, usd, charge, note=note)
        print(f"recorded revenue ${usd:.2f} ({charge}); revenue_usd=${st['revenue_usd']:.2f}")
        return 0

    if cmd == "issue-spend":
        st = read_state()
        print(f"${issue_spend(st, args[0]):.2f}")
        return 0

    if cmd == "trip-test":
        st = read_state()
        cid = _resolve_company_id(st)
        print(f"trip-test: pausing agents for company_id={cid or '(none → dry-run)'}")
        print(json.dumps(pause_all_agents(company_id=cid, reason="trip-test", state=_recompute(st)), indent=2))
        print("NOTE: agents are now paused. Run `reset` and re-enable wakeOnDemand per the plan.")
        return 0

    if cmd == "set-company":
        st = read_state()
        st["company_id"] = args[0]
        write_state(st, DEFAULT_LEDGER)
        print(f"company_id set to {args[0]} (kill-switch will pause this company's agents)")
        return 0

    if cmd == "reset":
        st = read_state()
        st["status"] = "active"
        write_state(st, DEFAULT_LEDGER)
        print("status reset to active (ledger entries preserved)")
        return 0

    print(f"unknown command: {cmd}\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
