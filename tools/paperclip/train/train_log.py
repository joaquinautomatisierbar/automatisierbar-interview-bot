#!/usr/bin/env python3
"""train_log.py — append/read the self-improvement run-log (JSONL).

One line per run record; the Cortana hub's /api/improve/runs serves these newest-first and the
SELF-IMPROVE view renders them ("was sie gemacht hat"). SHARED FILE: set CORTANA_TRAIN_RUNS on BOTH
the hub service and the train cron to the same absolute path (e.g. the hub's data/train_runs.jsonl).

Record fields (all optional except ts/status): ts, cycle, mode(dry|live), task, kind, surface,
status(planned|promoted|failed|cancelled|halted), eval{composite,validator,critic,judge,passed},
browser_test(pass|fail|na), cost_usd, duration_s, artifact, error, note.

Usage:
  python3 train_log.py append '{"cycle":"night-..","status":"planned","note":"3 tasks"}'
  echo '{...}' | python3 train_log.py append -
  python3 train_log.py recent [n]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.environ.get("CORTANA_TRAIN_RUNS",
                         os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "train_runs.jsonl")))


def append(record, path=DEFAULT):
    record = dict(record)
    record.setdefault("ts", datetime.now(timezone.utc).isoformat())
    record.setdefault("status", "planned")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def recent(n=50, path=DEFAULT):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return list(reversed(out))[:n]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("append"); a.add_argument("json", help="JSON record, or '-' for stdin")
    a.add_argument("--path", default=DEFAULT)
    r = sub.add_parser("recent"); r.add_argument("n", nargs="?", type=int, default=50); r.add_argument("--path", default=DEFAULT)
    ns = ap.parse_args()
    if ns.cmd == "append":
        raw = sys.stdin.read() if ns.json == "-" else ns.json
        rec = append(json.loads(raw), path=ns.path)
        print(json.dumps(rec, ensure_ascii=False))
    elif ns.cmd == "recent":
        print(json.dumps(recent(ns.n, path=ns.path), ensure_ascii=False, indent=2))
    else:
        ap.print_help(); sys.exit(2)


if __name__ == "__main__":
    main()
