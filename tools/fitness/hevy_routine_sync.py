#!/usr/bin/env python3
"""
hevy_routine_sync.py — version-controlled Hevy routine maintenance for the Comeback.

The Comeback routines were originally created via one-off curl and never preserved, so
rest times drifted wrong (compound near-max lifts resting only 60s; calves/tibialis far
too long). This tool makes the fixes reproducible from hevy_routines.json:

  --fix-rest   GET each routine -> patch only rest_seconds per the override map -> PUT.
               Rebuilds the PUT body from the live routine, so all logged sets / reps /
               weights are preserved; idempotent (re-running is a no-op).
  --create     POST the new "Increase Repetitions" rep-ladder routine (each ladder rung
               = one set), into folder 3019499; writes the new id back into the JSON.
  --verify     GET routines and print live rest_seconds vs the expected overrides.

Default is a dry-run; pass --apply to actually write. Auth: HEVY_API_KEY (.env).
"""
import os, sys, json, argparse, requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
CFG_PATH = os.path.join(_SCRIPT_DIR, "hevy_routines.json")
BASE = "https://api.hevyapp.com/v1"


def env(k, d=None):
    try:
        for ln in open(ENV_PATH):
            if ln.strip().startswith(k + "="):
                return ln.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    return os.environ.get(k, d)


KEY = env("HEVY_API_KEY", "")
H = {"api-key": KEY, "Content-Type": "application/json"}


def get_routine(rid):
    # the list endpoint is the reliable read; find the routine across pages
    for page in (1, 2, 3):
        r = requests.get(f"{BASE}/routines", headers=H, params={"page": page, "pageSize": 10}, timeout=30)
        r.raise_for_status()
        for x in r.json().get("routines", []):
            if x["id"] == rid:
                return x
    return None


def _set_body(s):
    return {"type": s.get("type", "normal"), "weight_kg": s.get("weight_kg"),
            "reps": s.get("reps"), "distance_meters": s.get("distance_meters"),
            "duration_seconds": s.get("duration_seconds"), "custom_metric": s.get("custom_metric")}


def put_body_from_live(routine, rest_map):
    """Rebuild the PUT body from a live routine, overriding rest_seconds by exercise title."""
    exs = []
    changed = []
    for ex in routine["exercises"]:
        rest = ex.get("rest_seconds")
        if ex["title"] in rest_map:
            new = rest_map[ex["title"]]
            if new != rest:
                changed.append(f"{ex['title']}: {rest}->{new}")
            rest = new
        e = {
            "exercise_template_id": ex["exercise_template_id"],
            "superset_id": ex.get("superset_id"),
            "rest_seconds": rest,
            "sets": [_set_body(s) for s in ex.get("sets", [])],
        }
        if ex.get("notes"):   # Hevy rejects empty notes; only send when present
            e["notes"] = ex["notes"]
        exs.append(e)
    # NOTE: PUT does not accept routine.folder_id (the routine stays in its folder);
    # folder_id is only valid on POST/create.
    rt = {"title": routine["title"], "exercises": exs}
    if routine.get("notes"):
        rt["notes"] = routine["notes"]
    return {"routine": rt}, changed


def fix_rest(cfg, apply, only=None):
    ok = True
    for rid, rmap in cfg["rest_overrides"].items():
        if only and rid != only:
            continue
        name = rmap.get("_name", rid)
        rest_map = {k: v for k, v in rmap.items() if not k.startswith("_")}
        live = get_routine(rid)
        if not live:
            print(f"[MISS] {name} ({rid}) not found"); ok = False; continue
        body, changed = put_body_from_live(live, rest_map)
        if not changed:
            print(f"[noop] {name}: rest already correct"); continue
        if not apply:
            print(f"[dry ] {name}: would change {changed}"); continue
        r = requests.put(f"{BASE}/routines/{rid}", headers=H, json=body, timeout=30)
        if r.status_code not in (200, 201):
            print(f"[FAIL] {name}: PUT {r.status_code} {r.text[:200]}"); ok = False; continue
        print(f"[OK  ] {name}: {changed}")
    return ok


def create_new(cfg, apply, key=None):
    ok = True
    for spec in cfg.get("new_routines", []):
        if key and spec["key"] != key:
            continue
        if spec.get("id"):
            print(f"[skip] {spec['title']} already created (id={spec['id']})"); continue
        exs = []
        for e in spec["exercises"]:
            sets = [{"type": "normal", "reps": r, "weight_kg": None,
                     "distance_meters": None, "duration_seconds": None, "custom_metric": None}
                    for r in e["ladder"]]
            exo = {"exercise_template_id": e["template_id"], "superset_id": None,
                   "rest_seconds": e.get("rest", 45), "sets": sets}
            if e.get("notes"):
                exo["notes"] = e["notes"]
            exs.append(exo)
        rt = {"title": spec["title"], "folder_id": cfg["folder_id"], "exercises": exs}
        if spec.get("notes"):
            rt["notes"] = spec["notes"]
        body = {"routine": rt}
        if not apply:
            total = sum(sum(e["ladder"]) for e in spec["exercises"])
            print(f"[dry ] would POST {spec['title']}: {len(exs)} moves, "
                  f"{sum(len(e['ladder']) for e in spec['exercises'])} sets, {total} total reps")
            for e in spec["exercises"]:
                print(f"        {e['title']:22} ladder {e['ladder']}  (Σ{sum(e['ladder'])})  rest {e.get('rest',45)}s")
            continue
        r = requests.post(f"{BASE}/routines", headers=H, json=body, timeout=30)
        if r.status_code not in (200, 201):
            print(f"[FAIL] POST {spec['title']}: {r.status_code} {r.text[:300]}"); ok = False; continue
        data = r.json()
        rt = data.get("routine", data) if isinstance(data, dict) else data
        if isinstance(rt, list):   # Hevy wraps the created routine in a list
            rt = rt[0]
        new_id = rt.get("id") if isinstance(rt, dict) else None
        print(f"[OK  ] created {spec['title']}  id={new_id}")
        # write id back into the JSON config
        for s in cfg["new_routines"]:
            if s["key"] == spec["key"]:
                s["id"] = new_id
        json.dump(cfg, open(CFG_PATH, "w"), indent=2, ensure_ascii=False)
        open(CFG_PATH, "a").write("\n")
    return ok


def verify(cfg):
    for rid, rmap in cfg["rest_overrides"].items():
        name = rmap.get("_name", rid)
        live = get_routine(rid)
        print(f"\n{name}")
        for ex in live["exercises"]:
            exp = rmap.get(ex["title"])
            mark = "" if exp is None else (" ✓" if ex["rest_seconds"] == exp else f" ✗ expected {exp}")
            print(f"  {ex['title'][:42]:42} rest={ex['rest_seconds']}s{mark}")
    for spec in cfg.get("new_routines", []):
        if spec.get("id"):
            live = get_routine(spec["id"])
            if live:
                print(f"\n{spec['title']}  (id={spec['id']})")
                for ex in live["exercises"]:
                    reps = [s.get("reps") for s in ex["sets"]]
                    print(f"  {ex['title'][:30]:30} rest={ex['rest_seconds']}s  ladder={reps}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix-rest", action="store_true")
    ap.add_argument("--create", nargs="?", const="*", help="create new routine(s); optional key")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="restrict --fix-rest to one routine id")
    a = ap.parse_args()
    if not KEY:
        print("HEVY_API_KEY missing"); sys.exit(1)
    cfg = json.load(open(CFG_PATH))
    rc = True
    if a.verify:
        verify(cfg); return
    if a.fix_rest:
        rc &= fix_rest(cfg, a.apply, a.only)
    if a.create:
        rc &= create_new(cfg, a.apply, None if a.create == "*" else a.create)
    if not (a.fix_rest or a.create):
        print("nothing to do — pass --fix-rest and/or --create (and --apply to write)")
    if a.apply and not rc:
        sys.exit(2)


if __name__ == "__main__":
    main()
