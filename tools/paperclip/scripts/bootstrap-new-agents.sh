#!/usr/bin/env bash
# bootstrap-new-agents.sh — idempotently fix agents that paperclipai company
# import left half-bootstrapped (no paperclipai-bundled skills → no heartbeat).
#
# Background — 2026-05-21 incident: 3 agents (Presentation Designer, Image
# Curator, Hook Strategist) sat with lastHeartbeatAt=null for days because they
# were imported via `--target existing --collision skip`, which doesn't auto-
# wire the paperclipai-bundled `paperclip` skill (the one that contains the
# heartbeat procedure). Without that skill the harness has nothing to run.
#
# Run this AFTER every `paperclipai company import` to fix anything stuck.
#
# Usage (from VPS as paperclip user, with cwd containing ./skills/):
#   cd /home/paperclip/automatisierbar-build
#   bash /home/paperclip/<repo>/tools/paperclip/scripts/bootstrap-new-agents.sh \
#     <company-id> [paperclip-api-url]
#
# Defaults: paperclip-api-url=http://127.0.0.1:3100

set -euo pipefail

CID="${1:?company-id required as first arg}"
API="${2:-http://127.0.0.1:3100}"
PAPERCLIPAI="${PAPERCLIPAI:-$HOME/.local/share/npm-global/bin/paperclipai}"

# Canonical paperclipai-bundled skill set (lifted from CTO's working config,
# 2026-05-21). Every claude_local agent needs `paperclipai/paperclip/paperclip`
# at minimum — the others are nice-to-haves but harmless.
BUNDLED_SKILLS='[
  "paperclipai/paperclip/diagnose-why-work-stopped",
  "paperclipai/paperclip/paperclip",
  "paperclipai/paperclip/paperclip-converting-plans-to-tasks",
  "paperclipai/paperclip/paperclip-create-agent",
  "paperclipai/paperclip/paperclip-create-plugin",
  "paperclipai/paperclip/paperclip-dev",
  "paperclipai/paperclip/para-memory-files",
  "paperclipai/paperclip/terminal-bench-loop"
]'

log() { echo "[bootstrap] $*" >&2; }

require_skills_dir() {
  if [[ ! -d "./skills" ]]; then
    log "ERROR: no ./skills/ subdir in cwd ($(pwd))"
    log "       cd into the company-package source dir first (e.g. /home/paperclip/automatisierbar-build)"
    exit 2
  fi
}

# Token isn't required when calling http://127.0.0.1 from same host —
# paperclip's local_trusted mode allows unauthenticated localhost.
auth_header_args=()
if [[ "${PAPERCLIP_BEARER_TOKEN:-}" != "" && "$API" != "http://127.0.0.1:"* ]]; then
  auth_header_args=(-H "Authorization: Bearer $PAPERCLIP_BEARER_TOKEN")
fi

curl_api() {
  curl -s "${auth_header_args[@]}" "$@"
}

list_agents() {
  curl_api "${API}/api/companies/${CID}/agents"
}

# Find agents that need bootstrapping
log "fetching agents on company $CID..."
list_agents > /tmp/bootstrap-all-agents.json
PYTHON_FIND='
import json, sys
agents = json.load(open("/tmp/bootstrap-all-agents.json"))
fixable = []
for a in agents:
    ac = a.get("adapterConfig", {}) or {}
    sync = ac.get("paperclipSkillSync", {}) or {}
    skills = sync.get("desiredSkills", []) or []
    has_paperclip_skill = "paperclipai/paperclip/paperclip" in skills
    has_heartbeat = a.get("lastHeartbeatAt") is not None
    if not has_heartbeat and not has_paperclip_skill:
        fixable.append(a["id"])
        print(f"  {a['urlKey']:30} id={a['id'][:8]} no-heartbeat, missing paperclip skill", file=sys.stderr)
print(",".join(fixable))
'
TO_FIX=$(python3 -c "$PYTHON_FIND")

if [[ -z "$TO_FIX" ]]; then
  log "all agents healthy — nothing to do"
  exit 0
fi

require_skills_dir
log "will fix: $TO_FIX"

IFS=',' read -ra AIDS <<< "$TO_FIX"
for AID in "${AIDS[@]}"; do
  log "=== bootstrap $AID ==="

  # Step 1 — local-cli (idempotent: creates API key, installs skills under ./skills/)
  if "$PAPERCLIPAI" agent local-cli "$AID" --company-id "$CID" --json > /tmp/bootstrap-$AID.json 2>&1; then
    log "  local-cli OK ($(python3 -c "import json; d=json.load(open('/tmp/bootstrap-$AID.json')); print(len(d.get('skills',[])))" 2>/dev/null || echo 0) skills synced)"
  else
    log "  local-cli FAILED: $(head -c 200 /tmp/bootstrap-$AID.json)"
    continue
  fi

  # Step 2 — PATCH desiredSkills to add bundled skills
  curl_api "${API}/api/agents/$AID" > /tmp/agent-$AID.json
  python3 << PYEOF > /tmp/agent-$AID-patch.json
import json
d = json.load(open("/tmp/agent-$AID.json"))
ac = d["adapterConfig"]
existing = set(ac.get("paperclipSkillSync", {}).get("desiredSkills", []))
bundled = set(json.loads('''$BUNDLED_SKILLS'''))
ac.setdefault("paperclipSkillSync", {})["desiredSkills"] = sorted(existing | bundled)
print(json.dumps({
    "adapterConfig": ac,
    "runtimeConfig": {"heartbeat": {"enabled": False, "wakeOnDemand": True, "cooldownSec": 60, "intervalSec": 0, "maxConcurrentRuns": 1}}
}))
PYEOF
  curl_api -X PATCH -H "Content-Type: application/json" \
    "${API}/api/agents/$AID" --data @/tmp/agent-$AID-patch.json > /dev/null
  log "  PATCH desiredSkills + wakeOnDemand=true OK"

  # Step 3 — fire a heartbeat to verify it actually runs now
  log "  firing heartbeat..."
  "$PAPERCLIPAI" heartbeat run --agent-id "$AID" --source on_demand --trigger ping 2>&1 | tail -3 | sed 's/^/    /'
done

log "done. Verify each agent has lastHeartbeatAt within the last minute:"
log "  curl ${API}/api/companies/${CID}/agents | jq -r '.[] | select(.lastHeartbeatAt == null) | .urlKey'"
log "(should print nothing if all agents healthy)"
