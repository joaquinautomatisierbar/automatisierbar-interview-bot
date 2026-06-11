#!/usr/bin/env python3
"""Backfill the Voice Calls DB from the Leads DB (one-time, best-effort history seed).

Reads Leads-DB rows that have `Gesprächsdatum` set (i.e. a call happened) and writes one
Voice Calls row each so the Analyse page has history before new batches accumulate.

LOW FIDELITY by design: the Leads DB keeps only the *latest* call per lead (last-call-wins),
holds no no-answer attempts, and `Pipeline Stage` maps back to a bucket only approximately.
Idempotent via a synthetic Call ID `backfill:<lead_id>` (re-runs skip already-seeded leads).

Usage:
  python3 tools/backfill_voice_calls.py            # DRY RUN — prints what it would write
  python3 tools/backfill_voice_calls.py --apply    # actually write
  python3 tools/backfill_voice_calls.py --apply --limit 200
"""
import argparse
import os
import sys
import time
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
NOTION_VERSION = "2022-06-28"
LEADS_DB_ID = os.environ.get("NOTION_LEADS_DB_ID", "31cbebb0-c2f9-8047-9e9f-fc59851f8a34")
VOICE_CALLS_DB_ID = os.environ.get("VOICE_CALLS_DB_ID", "37cbebb0-c2f9-818b-8c77-d635fbfd61cc")

# Leads-DB Pipeline Stage -> Voice Calls bucket (best-effort; unknown -> followup, neutral).
STAGE_TO_BUCKET = {
    "Workflow Interview": "hot", "Process Mapping": "hot", "Prototype Building": "hot",
    "Problem Interview": "followup", "OUT": "cold",
}


def _load_dotenv() -> None:
    env = _REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def _h(key):
    return {"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"}


def _rt(prop):
    arr = (prop or {}).get("rich_text") or (prop or {}).get("title") or []
    return "".join(t.get("plain_text", "") for t in arr).strip()


def _title_of(props):
    for v in props.values():
        if v.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in (v.get("title") or [])).strip()
    return ""


def _branche_of(props):
    p = props.get("Branche") or {}
    t = p.get("type")
    if t == "select":
        return (p.get("select") or {}).get("name")
    if t == "multi_select":
        opts = p.get("multi_select") or []
        return opts[0].get("name") if opts else None
    if t in ("rich_text", "title"):
        return _rt(p) or None
    return None


def _query_all(key, db_id, body):
    out, cursor = [], None
    while True:
        b = dict(body, page_size=100)
        if cursor:
            b["start_cursor"] = cursor
        r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query",
                          headers=_h(key), json=b, timeout=30)
        r.raise_for_status()
        d = r.json()
        out.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not (d.get("has_more") and cursor):
            break
        time.sleep(0.34)        # ~3 req/s Notion limit
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()

    _load_dotenv()
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key:
        print("ERROR: NOTION_API_KEY not set.", file=sys.stderr)
        return 1

    # already-seeded Call IDs (idempotency)
    seen = set()
    for p in _query_all(key, VOICE_CALLS_DB_ID, {}):
        cid = _rt((p.get("properties") or {}).get("Call ID"))
        if cid:
            seen.add(cid)
    print(f"Voice Calls DB already has {len(seen)} backfill/real rows.")

    # leads with a call date
    leads = _query_all(key, LEADS_DB_ID,
                       {"filter": {"property": "Gesprächsdatum", "date": {"is_not_empty": True}}})
    print(f"Leads with Gesprächsdatum set: {len(leads)}")

    to_write, skipped, by_bucket = [], 0, {}
    for lead in leads:
        lid = lead.get("id")
        bk_key = f"backfill:{lid}"
        if bk_key in seen:
            skipped += 1
            continue
        pr = lead.get("properties") or {}
        date = ((pr.get("Gesprächsdatum") or {}).get("date") or {}).get("start")
        if not date:
            continue
        stage = ((pr.get("Pipeline Stage") or {}).get("status") or {}).get("name")
        bucket = STAGE_TO_BUCKET.get(stage, "followup")
        firma = _title_of(pr) or "—"
        props = {
            "Call": {"title": [{"text": {"content": f"{firma} · {str(date)[:10]}"[:200]}}]},
            "Call ID": {"rich_text": [{"text": {"content": bk_key}}]},
            "Date": {"date": {"start": date}},
            "Firma": {"rich_text": [{"text": {"content": firma[:200]}}]},
            "Lead ID": {"rich_text": [{"text": {"content": lid}}]},
            "Connected": {"checkbox": True},
            "Bucket": {"select": {"name": bucket}},
        }
        br = _branche_of(pr)
        if br:
            props["Branche"] = {"select": {"name": str(br)[:100]}}
        tp = _rt(pr.get("Top Problem"))
        if tp:
            props["Top Problem"] = {"rich_text": [{"text": {"content": tp[:1900]}}]}
        sc = (pr.get("Schmnerzscore (1-5)") or {}).get("number")
        if isinstance(sc, (int, float)):
            props["Schmerzscore"] = {"number": sc}
        if (pr.get("Zahlungsindikator") or {}).get("checkbox"):
            props["Payment"] = {"checkbox": True}
        if (pr.get("Interview Abgeschlossen") or {}).get("checkbox"):
            props["Interview Completed"] = {"checkbox": True}
        to_write.append(props)
        by_bucket[bucket] = by_bucket.get(bucket, 0) + 1

    print(f"\nWould write {len(to_write)} new rows (skipped {skipped} already seeded).")
    print(f"  bucket split: {by_bucket}")
    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write.")
        return 0

    n = min(len(to_write), args.limit)
    print(f"\nWriting {n} rows …")
    ok = 0
    for i, props in enumerate(to_write[:n]):
        try:
            r = requests.post("https://api.notion.com/v1/pages", headers=_h(key),
                              json={"parent": {"database_id": VOICE_CALLS_DB_ID}, "properties": props},
                              timeout=20)
            if r.ok:
                ok += 1
            else:
                print(f"  row {i} failed: {r.status_code} {r.text[:160]}")
        except Exception as e:
            print(f"  row {i} error: {e}")
        time.sleep(0.34)        # ~3 req/s
        if (i + 1) % 25 == 0:
            print(f"  … {i + 1}/{n}")
    print(f"\nDone: {ok}/{n} rows written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
