#!/usr/bin/env python3
"""Backfill cold-call audio transcripts via the C2 webhook worker.

Workflow C (Drive-trigger) only fires on NEW Drive files, so any recording that
errored (e.g. the broken Gemini cred) or was uploaded while the pipeline was down
stays permanently untranscribed. This tool re-drives them deterministically:

  C-LIST (webhook)  -> full source-folder audio list + which already have transcripts
  C2     (webhook)  -> per-file: Drive download -> Gemini transcribe -> Drive upload

We fire C2 once per *pending* file with a small gap (n8n cloud queues the rest),
then the caller polls executions for success/error. Idempotent: re-running only
fires files still missing a transcript (C-LIST dedup), so it's safe to repeat.

Usage:
  python3 tools/backfill_transcripts.py            # pending Tej files only
  python3 tools/backfill_transcripts.py --all      # every pending audio file
  python3 tools/backfill_transcripts.py --gap 3    # seconds between fires (default 4)
"""
import argparse, json, subprocess, sys, time, os

LIST_HOOK = "https://oojoaquin.app.n8n.cloud/webhook/c2-list-9f3a2c"
C2_HOOK = "https://oojoaquin.app.n8n.cloud/webhook/c2-audio-transcribe-9f3a2c"
C2_WF = "N4jMK9Ff7THIsLwg"
N8N_API = "https://oojoaquin.app.n8n.cloud/api/v1"
LOG = os.path.join(os.path.dirname(__file__), "..", ".tmp", "backfill.log")


def _nkey():
    for l in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
        if l.startswith("N8N_API_KEY"):
            return l.split("=", 1)[1].strip()
    return ""


_H = ["-H", f"X-N8N-API-KEY: {_nkey()}"]


def _post(url, body):
    r = subprocess.run(["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json",
                        "-d", json.dumps(body)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"_raw": r.stdout[:200]}


def _get(url, tries=4):
    for _ in range(tries):
        out = subprocess.run(["curl", "-s", url] + _H, capture_output=True, text=True).stdout
        if out and out.strip()[:1] in "[{":
            try:
                return json.loads(out)
            except Exception:
                pass
        time.sleep(3)
    return {}


def _max_exec_id():
    d = _get(f"{N8N_API}/executions?workflowId={C2_WF}&limit=1")
    rows = d.get("data") or []
    return int(rows[0]["id"]) if rows else 0


def _wait_terminal(after_id, timeout=300):
    """Poll until a C2 execution with id > after_id reaches a terminal status."""
    waited = 0
    while waited < timeout:
        time.sleep(8); waited += 8
        d = _get(f"{N8N_API}/executions?workflowId={C2_WF}&limit=3")
        for r in d.get("data") or []:
            if int(r.get("id", 0)) > after_id and r.get("status") in ("success", "error", "crashed"):
                return r.get("status"), r.get("id")
    return "timeout", None


def _log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="process every pending file, not just Tej")
    ap.add_argument("--gap", type=float, default=4.0, help="gap between fires in parallel mode")
    ap.add_argument("--sequential", action="store_true",
                    help="fire one file, wait for its execution to finish, then the next (gentle on n8n cloud)")
    args = ap.parse_args()

    d = _post(LIST_HOOK, {})
    if isinstance(d, list):
        d = d[0] if d else {}
    files = d.get("files") or []
    if not files:
        _log(f"C-LIST returned no files: {str(d)[:200]}")
        sys.exit(1)
    pending = [f for f in files if not f.get("done")]
    if not args.all:
        pending = [f for f in pending if "_tej" in (f.get("name") or "").lower()]
    _log(f"C-LIST: {d.get('count')} total / {d.get('done')} done / {d.get('pending')} pending "
         f"-> firing {len(pending)} ({'all' if args.all else 'Tej-only'}), gap {args.gap}s")

    fired = ok_n = err_n = 0
    for f in pending:
        fired += 1
        if args.sequential:
            before = _max_exec_id()
            res = _post(C2_HOOK, {"file_id": f["id"], "file_name": f["name"]})
            if "started" not in str(res).lower():
                _log(f"[{fired}/{len(pending)}] WEBHOOK-REJECT {f['name'][:36]} -> backing off 15s")
                time.sleep(15)
                continue
            status, eid = _wait_terminal(before)
            ok_n += status == "success"; err_n += status != "success"
            _log(f"[{fired}/{len(pending)}] {status:8} exec {eid} {f['name'][:36]}")
        else:
            res = _post(C2_HOOK, {"file_id": f["id"], "file_name": f["name"]})
            ok = "started" in str(res).lower()
            _log(f"[{fired}/{len(pending)}] {'OK ' if ok else 'ERR'} {f['name'][:40]}")
            time.sleep(args.gap)
    if args.sequential:
        _log(f"DONE: fired {fired} | success {ok_n} | non-success {err_n}. Re-run to retry any failures (idempotent).")
    else:
        _log(f"DONE firing {fired} files. n8n is draining the queue; poll executions for outcomes.")


if __name__ == "__main__":
    main()
