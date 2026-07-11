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
check("build_message nennt den Erledigen-Weg (#8)", "Erledigen" in msg and "Erledigt" in msg)

# ── issue #8: reflect Notion/Hub triage into SQLite before alerting ──
from spesen import notion_feedback as nf

# fetch_resolved_app_ids without Notion env -> None (best-effort skip; alert keeps old behaviour)
_saved = (os.environ.pop("NOTION_API_KEY", None), os.environ.pop("SPESEN_FEEDBACK_DB_ID", None))
check("fetch_resolved_app_ids ohne Notion-Env -> None", nf.fetch_resolved_app_ids() is None)

# sync_resolved_from_notion closes exactly the feedbacks Notion reports resolved
_resolved_calls = []
_orig = (nf.fetch_resolved_app_ids, fa.db.open_feedback, fa.db.resolve_feedback)
nf.fetch_resolved_app_ids = lambda: {2, 3}
fa.db.open_feedback = lambda: [{"id": i, "name": "n", "text": "t",
                                "created_at": item(1)["created_at"]} for i in (1, 2, 3)]
fa.db.resolve_feedback = lambda fid: (_resolved_calls.append(fid) or True)
_n = fa.sync_resolved_from_notion()
check("sync schliesst die in Notion erledigten (2,3)", _n == 2 and set(_resolved_calls) == {2, 3})

# sync is a no-op when Notion is off (fetch returns None)
_resolved_calls.clear()
nf.fetch_resolved_app_ids = lambda: None
check("sync No-op wenn Notion aus", fa.sync_resolved_from_notion() == 0 and _resolved_calls == [])

nf.fetch_resolved_app_ids, fa.db.open_feedback, fa.db.resolve_feedback = _orig
if _saved[0] is not None:
    os.environ["NOTION_API_KEY"] = _saved[0]
if _saved[1] is not None:
    os.environ["SPESEN_FEEDBACK_DB_ID"] = _saved[1]

if FAILS:
    print(f"\n{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("\nALL PASS (feedback_alert)")
sys.exit(0)
