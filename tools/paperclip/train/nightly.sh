#!/usr/bin/env bash
# nightly.sh — Cortana self-improvement loop, nightly cron driver (00:00–06:00 on the VPS).
#
# DRY-RUN by default: exercises the orchestration (preflight → governor cycle → curriculum → digest)
# with NO spend, NO build, NO live touch — safe to run anytime. The real autonomous build lane is GATED
# in code: --live requires BOTH TRAIN_ENABLED=1 AND a metered ANTHROPIC_API_KEY, else it refuses. The Max
# OAuth token must NEVER drive the Agent SDK (ban vector); only the bounded `claude -p` liveness probe
# touches Max. Spend is bounded by the governor's per-cycle + per-month caps on a SEPARATE train ledger.
#
# Usage:
#   bash nightly.sh                 # dry-run (default)
#   TRAIN_ENABLED=1 ANTHROPIC_API_KEY=sk-... bash nightly.sh --live    # gated live lane
set -euo pipefail

MODE="dry"; [[ "${1:-}" == "--live" ]] && MODE="live"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GOV="$REPO_ROOT/tools/revenue_governor.py"
CUR="$SCRIPT_DIR/curriculum.py"
export GOVERNOR_LEDGER="${GOVERNOR_LEDGER:-$REPO_ROOT/data/train_ledger.json}"

CYCLE_CAP="${TRAIN_CYCLE_CAP:-15}"
MONTH_CAP="${TRAIN_MONTH_CAP:-50}"
N_TASKS="${TRAIN_N:-3}"
CYCLE_ID="night-$(date +%Y-%m-%d-%H%M)"

log(){ printf '%s  %s\n' "$(date +%H:%M:%S)" "$*"; }
section(){ printf '\n=== %s ===\n' "$*"; }

section "Cortana train loop — $CYCLE_ID  (mode=$MODE)"
log "ledger: $GOVERNOR_LEDGER"

# ── PREFLIGHT ────────────────────────────────────────────────────────────────
section "PREFLIGHT"
python3 "$GOV" set-caps "$CYCLE_CAP" "$MONTH_CAP" >/dev/null
GOVSTAT=$(python3 "$GOV" status | python3 -c 'import json,sys;print(json.load(sys.stdin)["status"])')
log "governor: $GOVSTAT  (caps cycle=\$$CYCLE_CAP month=\$$MONTH_CAP)"
[[ "$GOVSTAT" != "active" ]] && { log "governor not active → abort, no run"; exit 0; }

# ── live-lane gate (operator go-live) — checked BEFORE any probe/spend ────────
if [[ "$MODE" == "live" ]]; then
  if [[ "${TRAIN_ENABLED:-0}" != "1" || -z "${ANTHROPIC_API_KEY:-}" ]]; then
    log "LIVE refused: needs TRAIN_ENABLED=1 + a metered ANTHROPIC_API_KEY (operator go-live gate)."
    exit 2
  fi
fi

# liveness probe (the bounded $0 Max lane); dry-run only checks the CLI is present
if command -v claude >/dev/null 2>&1; then
  if [[ "$MODE" == "live" ]]; then
    claude -p "reply with: ok" >/dev/null 2>&1 && log "liveness: claude -p ok" || { log "liveness FAILED → abort (re-auth needed)"; exit 1; }
  else
    log "liveness: claude CLI present (probe skipped in dry-run)"
  fi
else
  log "liveness: claude CLI not found ($([[ $MODE == live ]] && echo abort || echo 'ok for dry-run'))"
  [[ "$MODE" == "live" ]] && exit 1
fi

# ── CURRICULUM ───────────────────────────────────────────────────────────────
section "CURRICULUM"
python3 "$GOV" start-cycle "$CYCLE_ID" "$CYCLE_CAP" >/dev/null
SEL=$(python3 "$CUR" --n "$N_TASKS" --only harden)   # proving phase: hardening first (verifier exists)
printf '%s\n' "$SEL" | python3 -c 'import json,sys
for t in json.load(sys.stdin)["selected"]:
    print(" •", t["id"], "("+t["kind"]+", frontier="+str(t["frontier"])+")")
    print("     ", t["title"])'

# ── BUILD + VERIFY + EVAL (plan; executed only in the gated live lane) ───────
section "BUILD + VERIFY + EVAL"
printf '%s\n' "$SEL" | python3 -c 'import json,sys
for t in json.load(sys.stdin)["selected"]:
    print(" →", t["id"])
    print("     build : paperclip Builder<->Test (caps 8/3) · overseer.py watching (cancel authority)")
    print("     verify:", t.get("verifier"))
    print("     eval  : eval_judge.py vs golden surface", t.get("surface"), "(Validator60/Critic30/Judge10, PRIME-DIRECTIVE)")
    print("     promote: only on pass + zero golden regression → versioned skill + PR draft · NO live write, halt to Telegram")'
if [[ "$MODE" == "dry" ]]; then
  log "DRY-RUN: build/verify/eval/promote NOT executed (no spend, no build, no live touch)"
else
  log "LIVE: build loop runs here (joins curriculum→paperclip→overseer→eval_judge; wired in the next brick)"
fi

# ── END + DIGEST ─────────────────────────────────────────────────────────────
section "DIGEST"
python3 "$GOV" end-cycle >/dev/null

# append a cycle record to the run-log the SELF-IMPROVE view renders (live build steps add per-task records)
RUNREC=$(printf '%s\n' "$SEL" | CYCLE_ID="$CYCLE_ID" MODE="$MODE" python3 -c 'import json,sys,os
sel=json.load(sys.stdin)["selected"]
print(json.dumps({"cycle":os.environ["CYCLE_ID"],"mode":os.environ["MODE"],"kind":"cycle",
  "status":"planned" if os.environ["MODE"]=="dry" else "running",
  "note":("geplant (dry-run): " if os.environ["MODE"]=="dry" else "")+", ".join(t["id"] for t in sel)}))')
printf '%s' "$RUNREC" | python3 "$SCRIPT_DIR/train_log.py" append - >/dev/null 2>&1 && log "run-log: cycle record appended" || log "run-log: append skipped"
python3 "$GOV" status | python3 -c 'import json,sys
d=json.load(sys.stdin)
print(" cycle closed · status="+d["status"]
      +" · month_spent=$"+str(d.get("month_spent_usd",0))+"/"+str(d.get("month_cap_usd",0))
      +" · master_remaining=$"+str(d["remaining_usd"]))'
log "done."
