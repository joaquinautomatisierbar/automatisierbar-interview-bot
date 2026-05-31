---
name: dispatch-internal-issue
description: >
  Programmatic dispatch of a polished [INTERNAL] build brief from the Internal Planner agent to the existing build pipeline. Creates a new paperclip Issue in the Internal Builds project assigned to the CTO via the urlKey resolution pattern. Used only by the Internal Planner.
---

# Dispatch Internal Issue

This is the one external action the Internal Planner takes. Everything else is conversation.

## When to use

ONLY when the operator has explicitly confirmed the brief is ready ("ship it", "send to CEO", "dispatch", "looks good, go") AND you have produced a polished brief following `planning-protocol`.

Never dispatch without explicit confirmation. Never re-dispatch the same brief.

## API call

The paperclip server runs at `http://127.0.0.1:3100` on the same host as the agent (local_trusted, no auth required for the agent's own calls).

### Step 1 — resolve the CTO's id by urlKey (drift-proof)

```bash
CTO_ID=$(curl -s "http://127.0.0.1:3100/api/companies/47196d38-2f19-4168-af8f-fe9451dff910/agents" \
  | python3 -c 'import json,sys;a=json.load(sys.stdin);a=a if isinstance(a,list) else a.get("agents",[]);print(next(x["id"] for x in a if x.get("urlKey")=="cto"))')
```

**Why urlKey, not the hardcoded UUID?** UUIDs change on company re-imports (`paperclipai company import`). Hardcoding caused the orchestrator drift bug (`tools/paperclip/orchestrator.js` was pointing at a dead company for weeks before anyone noticed). See `~/_context/tools/paperclip/RELIABILITY.md` for the full story. The urlKey `cto` is stable across re-imports.

### Step 2 — create the issue

```bash
curl -s -X POST "http://127.0.0.1:3100/api/issues" \
  -H "Content-Type: application/json" \
  --data-binary @- <<EOF
{
  "title": "[INTERNAL] <one-line title that names the change>",
  "description": <full polished brief as JSON-escaped string>,
  "assigneeAgentId": "${CTO_ID}",
  "projectId": "230a021a-c22a-437f-8c33-bb9eda5fa357",
  "priority": "medium"
}
EOF
```

- `title` must start with `[INTERNAL]`. The CTO routes by tag — see `~/_context/tools/paperclip/companies/automatisierbar-build/agents/cto/AGENTS.md`.
- `description` is the full brief from the `planning-protocol` template (Context / Architecture / Critical files / Verification / Production safety + rollback).
- `projectId` = `230a021a-c22a-437f-8c33-bb9eda5fa357` (the *Internal Builds* paperclip project — verified 2026-06-01).
- `priority` is operator-driven; default `medium`.

Capture the response — it contains `identifier` (e.g. `AUT-142`) and `id` (UUID).

### Step 3 — confirm back to the operator on the planning Issue

Post one comment on the *planning* Issue (the one in `AI OS - OPERATIONS` the operator opened with you):

```
Dispatched as **AUT-XXX** in *Internal Builds*. CTO will pick it up via wake-on-assignment.

You can follow the build in paperclip; the orchestrator will Telegram you on completion or halt.

Closing this planning thread. ✓
```

Replace `AUT-XXX` with the actual identifier from the API response.

### Step 4 — close the planning Issue

```bash
curl -s -X PATCH "http://127.0.0.1:3100/api/issues/${PLANNING_ISSUE_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'
```

(`PLANNING_ISSUE_ID` is the UUID of the Issue you were working on, not the new dispatched one.)

## Failure modes

- **Non-200 on issue create** → don't retry blindly. Post a comment to the operator with the error body and `BLOCKED: dispatch failed — <error>`. Don't auto-close.
- **Can't resolve CTO by urlKey** → the company has drifted catastrophically. Halt + report.
- **Operator never confirmed but you dispatched anyway** → don't. There's no recovery from spending budget on an unwanted build.

## Hard rules

- One dispatch per planning Issue. After it succeeds, the planning Issue closes and you stop.
- Never dispatch a `[CLIENT]` brief — those enter through the web interview bot, not through the Planner. If the brief drifted client-facing, refuse and explain.
- Never modify production code in the dispatch itself — your output is only the brief; Engineer does the code.
- The brief MUST contain the `## Production safety + rollback` section — refuse to dispatch if it's missing.
