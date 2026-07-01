#!/usr/bin/env python3
"""Regression tests for the week-as-a-whole adherence logic in fitness_sync.py.

Locks the invariants that broke once (a moved session not credited to its planned slot,
and the risk of double-counting it). Run after ANY edit to week_bag / annotate_week_coverage /
build_week_view:

    ~/.comeback-sync/venv/bin/python3 tools/fitness/test_fitness_sync.py   # exit 0 = all pass

Pure/offline — builds synthetic day-rows, never touches Garmin/Hevy/Notion.
"""
import os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitness_sync as fs

MON = date(2026, 6, 22)          # a Monday inside the program (W1)
SUN = MON + timedelta(days=6)

def make_week(done_by_dow):
    """done_by_dow: {weekday_index: set(types)} -> list of day-rows for the ISO week."""
    rows = []
    for i in range(7):
        d = MON + timedelta(days=i)
        rows.append({"date": d.isoformat(), "dow": fs.DOW[d.weekday()],
                     "phase": 1, "week": 1,
                     "planned": sorted(fs.planned_for(d)),
                     "done": sorted(done_by_dow.get(i, set())),
                     "metrics": {}, "strength_volume": None, "hevy_rows": [], "activities": []})
    fs.annotate_week_coverage(rows)
    return rows

def credited(rows):
    _p, _d, done, planned = fs.week_bag(rows)
    return done, planned

def day(rows, dow):  # row by weekday index
    return rows[dow]

PASS, FAIL = [], []
def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("  ok  " if cond else "FAIL  ") + name)

# planned cardio days in W1 are Wed(2) + Sat(5); strength Tue(1)/Thu(3)/Fri(4); mobility daily; cuff Mon/Wed/Fri.

# 1) THE BUG: swim for Wed done Monday (surplus), Saturday NOT done.
#    -> Wed cardio covered (from Mon); Sat stays missed; cardio credited 1/2 (not inflated to 2).
r = make_week({0:{"mobility","cuff","cardio"},        # Mon: floor + the moved swim (cardio not planned Mon)
               1:{"mobility","strength"}, 2:{"mobility","cuff"},
               3:{"mobility"}, 4:{"mobility","cuff","strength"},
               5:set(), 6:{"mobility"}})
done, planned = credited(r)
check("moved swim credits Wednesday", "cardio" in day(r,2)["covered"])
check("Wednesday moved-from points at Monday", day(r,2)["moved"] and day(r,2)["moved"][0]["doneOn"]==[MON.isoformat()])
check("Saturday stays uncovered", "cardio" not in day(r,5)["covered"])
# the surplus swim must be credited exactly once (cap 1 of 2), never doubled by the cover flag
pb, db = fs.week_bag(r)[:2]
check("cardio credited 1 of 2 (surplus not double-counted)", min(db["cardio"], pb["cardio"]) == 1)
check("week planned total = 15", planned == 15)   # mobility7 + cuff3 + cardio2 + strength3 (Tue/Thu/Fri)

# 2) build_week_view summary must match the bag (coverage is display-only, never re-counts)
wv = fs.build_week_view(MON, {x["date"]: x for x in r}, SUN)
check("build_week_view agrees with bag", wv["summary"]["done"] == done and wv["summary"]["planned"] == planned)

# 3) NEGATIVE: cardio never done at all -> no coverage, credited 0/2.
r2 = make_week({0:{"mobility","cuff"},1:{"mobility","strength"},2:{"mobility","cuff"},
                3:{"mobility"},4:{"mobility","cuff","strength"},5:{"mobility"},6:{"mobility"}})
check("genuinely-missed cardio is NOT covered (Wed)", "cardio" not in day(r2,2)["covered"])
check("genuinely-missed cardio is NOT covered (Sat)", "cardio" not in day(r2,5)["covered"])

# 4) SURPLUS >= MISSED: two swims on non-planned days cover both planned slots.
r3 = make_week({0:{"mobility","cuff","cardio"},1:{"mobility","strength","cardio"},2:{"mobility","cuff"},
                3:{"mobility"},4:{"mobility","cuff","strength"},5:set(),6:{"mobility"}})
check("two surplus swims cover Wed and Sat", "cardio" in day(r3,2)["covered"] and "cardio" in day(r3,5)["covered"])
pb3, db3 = fs.week_bag(r3)[:2]
check("two surplus swims credit cardio 2 of 2", min(db3["cardio"], pb3["cardio"]) == 2)

# 5) NO DOUBLE COUNT: done on the planned day AND an extra -> capped at plan.
r4 = make_week({0:{"mobility","cuff","cardio"},1:{"mobility","strength"},2:{"mobility","cuff","cardio"},
                3:{"mobility"},4:{"mobility","cuff","strength"},5:{"mobility","cardio"},6:{"mobility"}})
d4,p4 = credited(r4)
check("cardio with extra still capped at 2", (lambda pb,db: min(db['cardio'],pb['cardio'])==2)(*fs.week_bag(r4)[:2]))

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
