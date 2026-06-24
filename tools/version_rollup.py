#!/usr/bin/env python3
"""Per-Script-Version rollup of the Voice Sessions DB — the A/B comparison.

Groups every batch by Script Version and shows the gate metrics (connected-weighted)
side by side, so "ist v20 besser als v17?" is a table, not a feeling. Read-only.

Usage: python3 tools/version_rollup.py
"""
import json, os, subprocess, sys
from collections import defaultdict

DB = "377bebb0-c2f9-8109-ad8b-c6aab96640dd"


def _key():
    for line in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
        s = line.strip()
        if s.startswith("NOTION_API_KEY") and "=" in s:
            return s.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _query_all(key):
    h = ["-H", f"Authorization: Bearer {key}", "-H", "Notion-Version: 2022-06-28",
         "-H", "Content-Type: application/json"]
    rows, cursor = [], None
    while True:
        body = {"page_size": 100, "sorts": [{"property": "Date", "direction": "ascending"}]}
        if cursor:
            body["start_cursor"] = cursor
        r = subprocess.run(["curl", "-s", "-X", "POST",
                            f"https://api.notion.com/v1/databases/{DB}/query"] + h
                           + ["-d", json.dumps(body)], capture_output=True, text=True)
        d = json.loads(r.stdout)
        rows += d.get("results", [])
        if not d.get("has_more"):
            break
        cursor = d.get("next_cursor")
    return rows


def _num(p, name):
    v = (p.get(name) or {}).get("number")
    return v


def main():
    key = _key()
    if not key:
        print("no NOTION_API_KEY"); sys.exit(2)
    rows = _query_all(key)
    by_ver = defaultdict(list)
    for r in rows:
        p = r["properties"]
        ver = ((p.get("Script Version") or {}).get("select") or {}).get("name") or "?"
        by_ver[ver].append(p)

    def wavg(props, metric, weight="Connected"):
        num = den = 0.0
        for p in props:
            v = _num(p, metric); w = _num(p, weight) or 0
            if v is not None and w:
                num += v * w; den += w
        return round(num / den, 2) if den else None

    cols = [("Health", "Median Health"), ("p95 s", "p95 Latenz s"),
            ("Open-Surv", "Opener-Survival Rate"), ("AgtFault-HU", "Agent-Fault Hangup Rate"),
            ("STT-err", "STT-Fehlerrate"), ("Hot-Rate", "Hot Rate"), ("Booking", "Booking Rate")]
    print(f"{'Version':9} {'Batches':>7} {'Fired':>6} {'Conn':>5} " +
          " ".join(f"{label:>11}" for label, _ in cols))
    print("-" * 110)
    for ver in sorted(by_ver):
        props = by_ver[ver]
        fired = int(sum(_num(p, "Fired") or 0 for p in props))
        conn = int(sum(_num(p, "Connected") or 0 for p in props))
        cells = []
        for _, metric in cols:
            v = wavg(props, metric)
            cells.append("—" if v is None else (f"{v*100:.0f}%" if "Rate" in metric or "Fehler" in metric else f"{v}"))
        print(f"{ver:9} {len(props):>7} {fired:>6} {conn:>5} " + " ".join(f"{c:>11}" for c in cells))
    print("\n(connected-gewichtet pro Version. Gates: Beta Health>=75 / p95<=1.5s / Opener>=55% / AgtFault<=15% / CBR>=3%)")


if __name__ == "__main__":
    main()
