#!/usr/bin/env python3
"""Bootstrap + lock down every agent of a Revenue Lab company.

For each agent: (1) run `paperclipai agent local-cli` to mint an API key + install the
paperclipai-bundled skills under ./skills/ (without the `paperclip` skill an agent has no
heartbeat procedure and never runs), then (2) set the heartbeat config —
enabled:false, wakeOnDemand:TRUE, cooldownSec:60, maxConcurrentRuns:1.

IMPORTANT (learned 2026-06-13): wakeOnDemand MUST be true or the agent is completely inert —
paperclip SKIPS every run, including explicit `heartbeat run`, when both enabled and
wakeOnDemand are false ("Heartbeat invocation was skipped"). The loop-safety does NOT come
from wakeOnDemand:false; it comes from the self-comment-exit guard in each AGENTS.md
("if the last comment is yours, exit") + cooldownSec:60 + maxConcurrentRuns:1 + the budget
governor kill-switch. This matches the working Automatisierbar config.

Why not the shared bootstrap-new-agents.sh: that script has a shell-quoting bug (single
quotes inside its embedded Python terminate the bash string → `urlKey` NameError). Uses
urllib (no shell-quoting).

Run ON THE VPS from the company package dir (must contain ./skills/):
  cd /home/paperclip/revenue-lab
  python3 /home/paperclip/wire_revenue_agents.py <company-id> [api-base]

Idempotent: re-running only re-asserts skills + heartbeat config.
"""
import json
import subprocess
import sys
import urllib.request

CID = sys.argv[1]
API = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:3100"
PAPERCLIPAI = "/home/paperclip/.local/share/npm-global/bin/paperclipai"

BUNDLED = [
    "paperclipai/paperclip/diagnose-why-work-stopped",
    "paperclipai/paperclip/paperclip",
    "paperclipai/paperclip/paperclip-converting-plans-to-tasks",
    "paperclipai/paperclip/paperclip-create-agent",
    "paperclipai/paperclip/paperclip-create-plugin",
    "paperclipai/paperclip/paperclip-dev",
    "paperclipai/paperclip/para-memory-files",
    "paperclipai/paperclip/terminal-bench-loop",
]
# Triggerable + loop-safe heartbeat config. wakeOnDemand MUST be true (else inert);
# loop-safety = self-comment-exit guard + cooldown + maxConcurrentRuns + budget governor.
HEARTBEAT = {"enabled": False, "wakeOnDemand": True, "cooldownSec": 60,
             "intervalSec": 0, "maxConcurrentRuns": 1}


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or "{}")


def main():
    agents = api("GET", f"/api/companies/{CID}/agents")
    if isinstance(agents, dict):
        agents = agents.get("agents", [])
    print(f"wiring {len(agents)} agents on company {CID}")
    for a in agents:
        aid, urlkey = a["id"], a.get("urlKey")
        print(f"--- {urlkey} ({aid[:8]}) ---")
        r = subprocess.run(
            [PAPERCLIPAI, "agent", "local-cli", aid, "--company-id", CID, "--json"],
            capture_output=True, text=True)
        print(f"  local-cli rc={r.returncode}"
              + ("" if r.returncode == 0 else f"  ERR: {(r.stderr or r.stdout)[:200]}"))
        cur = api("GET", f"/api/agents/{aid}")
        ac = cur.get("adapterConfig", {}) or {}
        existing = set((ac.get("paperclipSkillSync", {}) or {}).get("desiredSkills", []))
        ac.setdefault("paperclipSkillSync", {})["desiredSkills"] = sorted(existing | set(BUNDLED))
        api("PATCH", f"/api/agents/{aid}",
            {"adapterConfig": ac, "runtimeConfig": {"heartbeat": HEARTBEAT}})
        v = api("GET", f"/api/agents/{aid}")
        hb = (v.get("runtimeConfig", {}) or {}).get("heartbeat", {})
        skills = (v.get("adapterConfig", {}).get("paperclipSkillSync", {}) or {}).get("desiredSkills", [])
        print(f"  -> wakeOnDemand={hb.get('wakeOnDemand')} enabled={hb.get('enabled')} "
              f"maxRuns={hb.get('maxConcurrentRuns')} cooldown={hb.get('cooldownSec')} "
              f"paperclip_skill={'paperclipai/paperclip/paperclip' in skills}")
    print("done")


if __name__ == "__main__":
    main()
