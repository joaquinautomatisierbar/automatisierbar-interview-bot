#!/usr/bin/env python3
"""
garmin_workout_builder.py — build/update native Garmin (FR265) workouts from a
declarative JSON spec, via garth (token resume, no login in the loop).

Why this exists: the Comeback mobility/cuff workouts were originally created by a
session-local /tmp script that was never preserved, and the mobility workout shipped
with a structural bug — per-side moves (Open Book "8 pro Seite", Couch Stretch "45s
pro Seite", Shoulder CARs) were each a SINGLE step, so the watch did one side and
jumped straight to the next exercise, with no rest to switch/reposition. This tool
fixes that reproducibly: it EXPANDS each exercise into flat ExecutableStepDTO steps —

  per-side move  -> [exercise "— linke Seite"] [rest side_switch_s] [exercise "— rechte Seite"]
  multi-set move -> exercise, [rest set_rest_s], exercise, ... (sets times)
  every exercise -> followed by a [rest transition_s] "Nächste Übung" (except the last)

Flat ExecutableStepDTOs are used (not RepeatGroupDTO) because that schema is already
proven live on these workouts; rest steps with a `time` end-condition auto-advance on
the FR265. Workouts are updated IN PLACE (PUT /workout-service/workout/{id}) so the
existing schedule keeps pointing at the same id; we re-GET and validate afterwards
(invalid exerciseName FIT codes are silently nulled by Garmin).

Usage:
  python3 garmin_workout_builder.py            # dry-run: print expanded steps, no write
  python3 garmin_workout_builder.py --apply    # PUT each workout, then re-GET + validate
  python3 garmin_workout_builder.py --apply --only 1596765340
  python3 garmin_workout_builder.py --validate # just re-GET + validate current live state

Env (.env, repo root or next to this script): GARMIN_TOKEN_DIR
"""
import os, sys, json, argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
SPEC_PATH = os.path.join(_SCRIPT_DIR, "garmin_workouts.json")

STEP_TYPE_ID = {"warmup": 1, "cooldown": 2, "interval": 3, "recovery": 4, "rest": 5, "repeat": 6}
END_COND = {"lap": (1, "lap.button"), "time": (2, "time"), "reps": (10, "reps"), "iterations": (7, "iterations")}


def load_env():
    env = {}
    try:
        for ln in open(ENV_PATH):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env


ENV = load_env()
GARMIN_TOKEN_DIR = ENV.get("GARMIN_TOKEN_DIR") or os.environ.get("GARMIN_TOKEN_DIR") or os.path.expanduser("~/.garminconnect")


# ---------- step construction ----------
def _step(order, kind, end_type, end_val, category=None, exercise=None, desc=None):
    cid, ckey = END_COND[end_type]
    tid = STEP_TYPE_ID[kind]
    return {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": order,
        "stepType": {"stepTypeId": tid, "stepTypeKey": kind, "displayOrder": tid},
        "childStepId": None,
        "description": desc,
        "endCondition": {"conditionTypeId": cid, "conditionTypeKey": ckey, "displayOrder": cid, "displayable": True},
        "endConditionValue": float(end_val),
        "preferredEndConditionUnit": None,
        "endConditionCompare": None,
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
        "targetValueOne": None, "targetValueTwo": None, "targetValueUnit": None,
        "zoneNumber": None,
        "category": category,
        "exerciseName": exercise,
        "weightValue": None, "weightUnit": None,
    }


def expand_steps(wdef):
    """Expand a workout's exercise list into a flat ExecutableStepDTO list."""
    d = wdef.get("defaults", {})
    side_switch = d.get("side_switch_s", 10)
    set_rest = d.get("set_rest_s", 15)
    transition = d.get("transition_s", 20)
    steps = []
    order = 1

    def add(kind, end_type, val, category=None, exercise=None, desc=None):
        nonlocal order
        steps.append(_step(order, kind, end_type, val, category, exercise, desc))
        order += 1

    exs = wdef["exercises"]
    for i, ex in enumerate(exs):
        sets = ex.get("sets", 1)
        per_side = ex.get("per_side", False)
        ss = ex.get("side_switch_s", side_switch)
        sr = ex.get("set_rest_s", set_rest)
        tr = ex.get("transition_s", transition)
        cat, code, end, val, base = ex.get("category"), ex.get("code"), ex["end"], ex["value"], ex["desc"]
        for s in range(sets):
            if per_side:
                add("interval", end, val, cat, code, base + " — linke Seite")
                add("rest", "time", ss, desc="Seite wechseln")
                add("interval", end, val, cat, code, base + " — rechte Seite")
            else:
                add("interval", end, val, cat, code, base)
            if s < sets - 1:
                add("rest", "time", sr, desc="Satzpause")
        if i < len(exs) - 1:
            add("rest", "time", tr, desc="Nächste Übung")
    return steps


def estimate_secs(steps):
    total = 0
    for s in steps:
        ck = s["endCondition"]["conditionTypeKey"]
        v = s["endConditionValue"]
        total += v if ck == "time" else (v * 3 if ck == "reps" else 5)
    return int(total)


# ---------- garmin io ----------
def gc(path, method="GET", **kw):
    import garth
    return garth.connectapi(path, method=method, **kw)


def fetch(wid):
    return gc(f"/workout-service/workout/{wid}")


def put_workout(wid, obj):
    return gc(f"/workout-service/workout/{wid}", method="PUT", json=obj)


def apply_workout(wdef, dry=True):
    wid = wdef["id"]
    obj = fetch(wid)
    steps = expand_steps(wdef)
    seg = obj["workoutSegments"][0]
    seg["workoutSteps"] = steps
    if wdef.get("description"):
        obj["description"] = wdef["description"]
        seg["description"] = wdef["description"]
    obj["estimatedDurationInSecs"] = estimate_secs(steps)
    seg["estimatedDurationInSecs"] = estimate_secs(steps)
    if dry:
        print(f"\n--- DRY RUN {wid}  {wdef['name']}  ({len(steps)} steps, ~{estimate_secs(steps)//60}min) ---")
        _print_steps(steps)
        return None
    put_workout(wid, obj)
    return validate_live(wdef)


def _print_steps(steps):
    for s in steps:
        k = s["stepType"]["stepTypeKey"]
        ck = s["endCondition"]["conditionTypeKey"]
        v = s["endConditionValue"]
        ex = s.get("exerciseName")
        d = (s.get("description") or "")[:60]
        if k == "rest":
            print(f"  [{s['stepOrder']:2}] REST  {int(v)}s   {d}")
        else:
            print(f"  [{s['stepOrder']:2}] {k:8} {ck}:{int(v):<3} ex={ex}  {d}")


# ---------- validation ----------
def validate_live(wdef):
    """Re-GET and assert: per-side moves have links+rechts, rests present, no nulled codes."""
    wid = wdef["id"]
    obj = fetch(wid)
    steps = obj["workoutSegments"][0]["workoutSteps"]
    problems = []
    rests = [s for s in steps if (s.get("stepType") or {}).get("stepTypeKey") == "rest"]
    intervals = [s for s in steps if (s.get("stepType") or {}).get("stepTypeKey") == "interval"]
    # codes that should be present (non-null in the spec) must survive the round-trip
    want_codes = {e["code"] for e in wdef["exercises"] if e.get("code")}
    live_codes = {s.get("exerciseName") for s in intervals if s.get("exerciseName")}
    nulled = want_codes - live_codes
    if nulled:
        problems.append(f"FIT codes nulled by Garmin (invalid): {sorted(nulled)}")
    if not rests:
        problems.append("no rest steps present")
    # per-side coverage: every per_side exercise must show both 'linke' and 'rechte'
    for e in wdef["exercises"]:
        if e.get("per_side"):
            descs = [s.get("description") or "" for s in intervals]
            base = e["desc"][:20]
            L = any(base in dd and "linke Seite" in dd for dd in descs)
            R = any(base in dd and "rechte Seite" in dd for dd in descs)
            if not (L and R):
                problems.append(f"per-side missing links/rechts for: {e['desc'][:30]}")
    ok = not problems
    print(f"\n[{'OK ' if ok else 'FAIL'}] {wid}  {wdef['name']}: "
          f"{len(steps)} steps ({len(intervals)} exercise, {len(rests)} rest), "
          f"codes ok={len(live_codes & want_codes)}/{len(want_codes)}")
    for p in problems:
        print("      ! " + p)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="PUT changes (default: dry-run)")
    ap.add_argument("--validate", action="store_true", help="only re-GET + validate live state")
    ap.add_argument("--only", help="restrict to one workout id")
    args = ap.parse_args()

    spec = json.load(open(SPEC_PATH))
    wdefs = spec["workouts"]
    if args.only:
        wdefs = [w for w in wdefs if w["id"] == args.only]
        if not wdefs:
            print("no workout with id", args.only); sys.exit(1)

    import garth
    garth.resume(GARMIN_TOKEN_DIR)
    garth.connectapi("/userprofile-service/socialProfile")  # auth check

    if args.validate:
        allok = all(validate_live(w) for w in wdefs)
        sys.exit(0 if allok else 2)

    results = []
    for w in wdefs:
        results.append(apply_workout(w, dry=not args.apply))
    if args.apply:
        allok = all(r for r in results)
        print("\n=== " + ("ALL OK" if allok else "SOME FAILED") + " ===")
        sys.exit(0 if allok else 2)
    else:
        print("\n(dry-run — re-run with --apply to write)")


if __name__ == "__main__":
    main()
