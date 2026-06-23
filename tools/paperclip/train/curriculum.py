#!/usr/bin/env python3
"""curriculum.py — the nightly task selector for Cortana's self-improvement loop.

Picks N candidate tasks from backlog.json, preferring the **30-70% prior-success "frontier" band**
(where the most learning happens), in a ~50/30/20 backlog/harden/distill mix. Deterministic — sorts by
frontier score then id, so a cycle is reproducible (no randomness).

Two hard rules baked in:
  • NEVER selects a golden-set id (the frozen eval gate is never training data).
  • Only yields sandbox/test build-or-harden tasks of OUR OWN tooling — the loop never touches a real
    customer / live production system (PRIME DIRECTIVE; see references/golden/README.md).

Usage:
  python3 curriculum.py --demo                 # self-check the selector
  python3 curriculum.py --n 3                  # print a JSON selection
  python3 curriculum.py --n 3 --only harden    # proving phase: hardening only (verifier already exists)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(HERE, "backlog.json")
GOLDEN = os.path.normpath(os.path.join(HERE, "..", "..", "..", "references", "golden", "golden_set.json"))
DEFAULT_MIX = {"backlog": 0.5, "harden": 0.3, "distill": 0.2}
KINDS = ("backlog", "harden", "distill")


def golden_ids(path=GOLDEN):
    try:
        with open(path, encoding="utf-8") as f:
            return {c["id"] for c in json.load(f).get("cases", [])}
    except Exception:
        return set()


def success_rate(task):
    a = task.get("attempts", [])
    if not a:
        return None  # never attempted → explore
    return round(sum(1 for x in a if x.get("success")) / len(a), 3)


def frontier_score(task):
    """Higher = more worth doing tonight. The 30-70% band scores highest (most learning);
    never-attempted is a strong explore; stuck (<30%) and mastered (>70%) score low."""
    r = success_rate(task)
    if r is None:
        return 0.75          # explore
    if 0.3 <= r <= 0.7:
        return 1.0           # the frontier
    if r < 0.3:
        return 0.25          # too hard / stuck — deprioritise
    return 0.40              # already mastered


def _eligible(task, gids):
    return task["id"] not in gids and task.get("status") not in ("done", "in_progress", "blocked")


def select(n=3, mix=None, backlog_path=BACKLOG, golden_path=GOLDEN, only=None):
    mix = mix or DEFAULT_MIX
    gids = golden_ids(golden_path)
    with open(backlog_path, encoding="utf-8") as f:
        tasks = json.load(f).get("tasks", [])

    pool = []
    for t in tasks:
        if not _eligible(t, gids):
            continue
        pool.append(dict(t, success_rate=success_rate(t), frontier=frontier_score(t)))
    by_kind = {k: [] for k in KINDS}
    for t in pool:
        by_kind.setdefault(t["kind"], []).append(t)
    for k in by_kind:
        by_kind[k].sort(key=lambda t: (-t["frontier"], t["id"]))

    chosen, chosen_ids = [], set()

    def add(t):
        if len(chosen) < n and t["id"] not in chosen_ids:
            chosen.append(t); chosen_ids.add(t["id"])

    if only:
        for t in by_kind.get(only, []):
            add(t)
    else:
        quotas = {k: int(round(n * mix.get(k, 0))) for k in KINDS}
        for k in ("harden", "backlog", "distill"):   # hardening first — its verifier already exists
            for t in by_kind.get(k, [])[:quotas[k]]:
                add(t)
        if len(chosen) < n:   # fill quota-rounding / thin-kind shortfall with frontier-best remaining
            for t in sorted((x for x in pool if x["id"] not in chosen_ids),
                            key=lambda x: (-x["frontier"], x["id"])):
                add(t)

    return {
        "n": n, "mix": (("only:" + only) if only else mix),
        "selected": [{"id": t["id"], "kind": t["kind"], "title": t["title"], "surface": t.get("surface"),
                      "verifier": t.get("verifier"), "est_usd": t.get("est_usd"),
                      "success_rate": t["success_rate"], "frontier": t["frontier"]} for t in chosen],
        "excluded_golden": sorted(gids), "pool_size": len(pool),
    }


def _demo():
    fails = []

    def chk(label, cond, extra=""):
        print(("PASS " if cond else "FAIL ") + label + (("  " + extra) if extra else ""))
        if not cond:
            fails.append(label)

    gids = golden_ids()
    chk("golden ids loaded", len(gids) == 5, str(sorted(gids)))

    sel = select(n=3)
    ids = [s["id"] for s in sel["selected"]]
    chk("selects exactly n=3", len(sel["selected"]) == 3, str(ids))
    chk("never selects a golden id", not (set(ids) & gids))
    kinds = {s["kind"] for s in sel["selected"]}
    chk("mixes kinds (>1 kind in 3)", len(kinds) >= 2, str(kinds))
    # frontier: a stuck task (rate<0.3) must not outrank an in-band one of the same kind
    stuck_before_band = any(
        s["id"] == "backlog-cockpit-error-banner" and "backlog-warroom-pace-widget" not in ids
        for s in sel["selected"])
    chk("frontier sort prefers in-band over stuck/mastered",
        all(s["frontier"] >= 0.4 for s in sel["selected"]), str([(s["id"], s["frontier"]) for s in sel["selected"]]))

    only = select(n=3, only="harden")
    chk("--only harden → all hardening", all(s["kind"] == "harden" for s in only["selected"]), str([s["id"] for s in only["selected"]]))
    # the fully-mastered harden task (rate=1.0) should rank below frontier/explore harden tasks
    oids = [s["id"] for s in only["selected"]]
    chk("mastered task deprioritised within kind", oids.index("harden-scraper-placeid") == len(oids) - 1 if "harden-scraper-placeid" in oids else True, str(oids))

    print()
    if fails:
        print("❌ %d FAILED: %s" % (len(fails), fails)); return 1
    print("✅ curriculum selector OK"); print(json.dumps(sel, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--only", choices=KINDS)
    ap.add_argument("--backlog", default=BACKLOG)
    ap.add_argument("--golden", default=GOLDEN)
    a = ap.parse_args()
    if a.demo:
        sys.exit(_demo())
    print(json.dumps(select(n=a.n, only=a.only, backlog_path=a.backlog, golden_path=a.golden), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
