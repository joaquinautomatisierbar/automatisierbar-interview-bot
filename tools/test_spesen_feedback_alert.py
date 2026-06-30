#!/usr/bin/env python3
"""Offline tests for spesen.feedback_alert — the batched-alert decision logic.

Run: python3 tools/test_spesen_feedback_alert.py  (exit 0 = pass). Pure, no DB/network.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SPESEN_DB_PATH", "/tmp/ks_fa_unused.db")  # importing db won't connect

from spesen import feedback_alert as fa

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


NOW = datetime(2026, 6, 30, 12, 0, 0)


def item(hours_old):
    return {"created_at": (NOW - timedelta(hours=hours_old)).strftime("%Y-%m-%d %H:%M:%S")}


# under both thresholds -> no alert
check("2 frische Feedbacks -> kein Alert", fa.evaluate([item(1), item(2)], "", NOW)["alert"] is False)
# more than 5 open -> alert
check(">5 offen -> Alert", fa.evaluate([item(1)] * 6, "", NOW)["alert"] is True)
# exactly 5 -> no alert (threshold is GREATER than 5)
check("genau 5 offen -> kein Alert", fa.evaluate([item(1)] * 5, "", NOW)["alert"] is False)
# oldest older than 48h -> alert
check(">48h alt -> Alert", fa.evaluate([item(50)], "", NOW)["alert"] is True)
check("47h alt -> kein Alert", fa.evaluate([item(47)], "", NOW)["alert"] is False)

# dedup: a recent alert suppresses
recent = (NOW - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
check("kürzlich alarmiert -> kein Alert", fa.evaluate([item(50)], recent, NOW)["alert"] is False)
# dedup expired (>24h) -> alert again
old = (NOW - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%S")
check("alter Alert (>24h) -> wieder Alert", fa.evaluate([item(50)], old, NOW)["alert"] is True)

# oldest_age_hours
check("oldest_age_hours ~50", abs(fa.oldest_age_hours([item(50), item(1)], NOW) - 50) < 0.1)
check("oldest_age_hours leer -> 0", fa.oldest_age_hours([], NOW) == 0.0)

# build_message doesn't crash + includes snippet
msg = fa.build_message([{"name": "Markus", "text": "geht nicht", "created_at": item(50)["created_at"]}],
                       {"reason": "test", "count": 1, "oldest_h": 50})
check("build_message enthält Snippet", "Markus" in msg and "geht nicht" in msg)

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (feedback_alert)")
sys.exit(0)
