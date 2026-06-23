#!/usr/bin/env python3
"""overseer.py — the async watcher with CANCEL authority over a running train build.

The highest-leverage safety add: a cheap watcher tails a build's trace and kills a pathological run
BEFORE it burns the night's budget or spins forever. Deterministic guards decide first (free, decisive);
only if none trip does it optionally ask Haiku "is this trace pathological?" (graceful degrade → no
cancel when the LLM is offline, so the deterministic floor always holds).

Deterministic guards (first trip wins):
  1. spend     — spend_usd >= max_spend_usd            (mirrors the governor's per-cycle cap)
  2. time      — elapsed_s >= max_seconds              (SICA-style per-task wall-clock cap)
  3. iteration — iterations >= max_iterations          (Build<->Test cycle cap, default 8)
  4. loop      — same action repeated >= loop_repeat   (repeated-diff / thrash detector)
  5. progress  — no_progress_iters >= max_no_progress  (spinning without producing an artifact)

Usage:
  python3 overseer.py --demo
  python3 overseer.py --check trace.json          # prints {cancel, reason, via}, exit 0=continue 1=cancel
"""
import argparse
import json
import os
import sys
import urllib.request
from collections import Counter

DEFAULT_LIMITS = {
    "max_spend_usd": 15.0,
    "max_seconds": 300.0,
    "max_iterations": 8,
    "loop_repeat": 3,
    "max_no_progress": 4,
}
OVERSEER_MODEL = os.environ.get("OVERSEER_MODEL", "claude-haiku")
LITELLM_URL = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000/v1/chat/completions")
LITELLM_KEY = os.environ.get("LITELLM_MASTER_KEY", "sk-cortana-local")


def _deterministic(trace, lim):
    spend = float(trace.get("spend_usd", 0))
    if spend >= lim["max_spend_usd"]:
        return f"spend cap: ${spend:.2f} >= ${lim['max_spend_usd']:.2f}"
    elapsed = float(trace.get("elapsed_s", 0))
    if elapsed >= lim["max_seconds"]:
        return f"time cap: {elapsed:.0f}s >= {lim['max_seconds']:.0f}s"
    iters = int(trace.get("iterations", 0))
    if iters >= lim["max_iterations"]:
        return f"iteration cap: {iters} >= {lim['max_iterations']}"
    actions = trace.get("recent_actions", []) or []
    if actions:
        action, count = Counter(actions).most_common(1)[0]
        if count >= lim["loop_repeat"]:
            return f"loop detected: action repeated {count}x ('{str(action)[:60]}')"
    nps = int(trace.get("no_progress_iters", 0))
    if nps >= lim["max_no_progress"]:
        return f"no progress for {nps} iterations (>= {lim['max_no_progress']})"
    return None


def _haiku(trace):
    """Ask Haiku whether the trace looks pathological. (None, ok=False) on any failure → no cancel."""
    summary = json.dumps({k: trace.get(k) for k in
                          ("iterations", "elapsed_s", "no_progress_iters", "spend_usd", "recent_actions", "last_output")},
                         ensure_ascii=False)[:3000]
    prompt = ("Hier ist der Trace eines laufenden autonomen Build-Versuchs:\n" + summary +
              "\n\nWirkt das pathologisch (Endlosschleife, völlig vom Ziel abgekommen, brennt ohne Fortschritt)? "
              "Antworte NUR JSON: {\"cancel\": true|false, \"reason\": \"<kurz>\"}. Im Zweifel cancel:false.")
    body = json.dumps({"model": OVERSEER_MODEL, "temperature": 0,
                       "messages": [{"role": "system", "content": "Du bist ein nüchterner Aufseher. Antworte nur JSON."},
                                    {"role": "user", "content": prompt}], "max_tokens": 150}).encode()
    req = urllib.request.Request(LITELLM_URL, data=body,
                                 headers={"Authorization": "Bearer " + LITELLM_KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = json.loads(r.read())["choices"][0]["message"]["content"]
        import re
        m = re.search(r"\{[\s\S]*\}", txt)
        d = json.loads(m.group(0)) if m else None
        if d and d.get("cancel"):
            return d.get("reason", "Haiku-Overseer: pathologisch"), True
        return None, True
    except Exception:
        return None, False


def should_cancel(trace, limits=None, use_haiku=True):
    lim = dict(DEFAULT_LIMITS, **(limits or {}))
    det = _deterministic(trace, lim)
    if det:
        return {"cancel": True, "reason": det, "via": "deterministic"}
    if use_haiku:
        reason, ok = _haiku(trace)
        if reason:
            return {"cancel": True, "reason": reason, "via": "haiku"}
        return {"cancel": False, "reason": "ok", "via": "haiku" if ok else "deterministic(haiku offline)"}
    return {"cancel": False, "reason": "ok", "via": "deterministic"}


def _demo():
    fails = []

    def chk(label, cond, extra=""):
        print(("PASS " if cond else "FAIL ") + label + (("  " + extra) if extra else ""))
        if not cond:
            fails.append(label)

    # healthy → no cancel (haiku off so the test is deterministic + offline-safe)
    healthy = {"iterations": 2, "elapsed_s": 40, "recent_actions": ["edit-a", "test-b"], "spend_usd": 1.2, "no_progress_iters": 1}
    r = should_cancel(healthy, use_haiku=False)
    chk("healthy → continue", r["cancel"] is False, r["reason"])

    chk("spend cap trips", should_cancel({"spend_usd": 16}, use_haiku=False)["cancel"] is True)
    chk("time cap trips", should_cancel({"elapsed_s": 301}, use_haiku=False)["cancel"] is True)
    chk("iteration cap trips", should_cancel({"iterations": 8}, use_haiku=False)["cancel"] is True)
    loop = should_cancel({"recent_actions": ["same-diff", "same-diff", "same-diff"]}, use_haiku=False)
    chk("loop detected trips", loop["cancel"] is True, loop["reason"])
    chk("no-progress trips", should_cancel({"no_progress_iters": 4}, use_haiku=False)["cancel"] is True)
    # ordering: spend beats the rest when several would trip
    multi = should_cancel({"spend_usd": 99, "elapsed_s": 9999, "iterations": 99}, use_haiku=False)
    chk("spend guard checked first", "spend cap" in multi["reason"], multi["reason"])

    print()
    if fails:
        print("❌ %d FAILED: %s" % (len(fails), fails)); return 1
    print("✅ overseer guards OK"); return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--check", help="path to a trace.json")
    ap.add_argument("--no-haiku", action="store_true")
    a = ap.parse_args()
    if a.demo:
        sys.exit(_demo())
    if a.check:
        with open(a.check, encoding="utf-8") as f:
            trace = json.load(f)
        r = should_cancel(trace, use_haiku=not a.no_haiku)
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(1 if r["cancel"] else 0)
    ap.print_help(); sys.exit(2)


if __name__ == "__main__":
    main()
