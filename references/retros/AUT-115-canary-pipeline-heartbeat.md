---
name: AUT-115-canary-pipeline-heartbeat
description: First INTERNAL canary validating the wakeOnDemand build-pipeline fix — shipped clean in 8 minutes, but surfaced two parent→child routing gaps
type: retro
scope: issue:AUT-115
created: 2026-05-30
issue: AUT-115
shipped_at: 2026-05-30
roles_involved: [cto, engineer, qa-engineer, product-engineer, release-engineer]
tags: [canary, pipeline-reliability, wakeOnDemand, parent-child-routing, internal]
---

## Context

INTERNAL canary Issue to validate the `wakeOnDemand=true` fix that landed on the build-pipeline agents 2026-05-29. Brief: add a simple "build-pipeline heartbeat marker" file (`tools/paperclip/.pipeline-events.log` writer) and ship via the full pipeline as a smoke test.

## What we expected

8-15 min end-to-end through CTO → Engineer → QA → Product → Release. Wake-on-comment to work without manual `paperclipai heartbeat run` pokes. Marker comments (`READY_FOR_TEST`, `TEST_PASS`, `SHIP`) to flow on their own.

## What actually happened

Shipped in 8 minutes — the fastest pipeline run to date. Confirmed wakeOnDemand was real-world working. BUT surfaced two latent problems that didn't cause failure on this canary but would on a bigger Issue:

1. **CTO's `PLAN_LOCKED` comment lists every downstream marker** (READY_FOR_TEST, TEST_PASS, SHIP, etc.) as part of describing the planned handoff sequence. The orchestrator's `canary.js` marker-regex scanned the flat join of all comment bodies and matched those tokens *anywhere* — so every stage looked PASS at 201s when only CTO had actually run. Pure regex false-positive. Didn't matter for AUT-115 because everything genuinely did ship — but on a failed Issue this would mask the real failure.

2. **Parent→child pivot was missing.** CTO spawned a child Issue (AUT-118) for the actual build work. The canary script kept polling AUT-115 (the parent) for downstream markers, never noticing the work had pivoted to a child. Manually traced the pivot, but the canary's auto-scorecard reported only `cto` as having run.

## Carry-forward learnings

### 1. Marker detection must be first-line + author-id check, not flat-blob regex

**Rule:** `canary.js`'s marker-detection should iterate comments, and for each comment check that (a) its first non-blank line starts with the marker token AND (b) the comment's `authorAgentId` resolves to the agent with the expected role's `urlKey`. Plain regex over the flat-joined comment text produces false positives whenever a planning comment mentions downstream markers.
**Why:** AUT-115's CTO plan listed every marker → canary reported all 5 stages PASS at 201s when only CTO had actually run. Caught by manual inspection; would silently mislead the operator on a real failure.
**Scope:** global
**How to apply:** Any time `tools/paperclip/canary.js` or other orchestrator-side comment-parsing logic is touched. Mirror the convention codified in `tools/paperclip/companies/automatisierbar-build/skills/handoff-protocol/SKILL.md` — markers ARE first-line, that's the protocol.

### 2. Canary must follow parent→child pivots

**Rule:** When CTO posts `PLAN_LOCKED` and spawns a child Issue, the canary monitor must shift its polling target from the parent to the child. Read `parentId` / children from the Issue meta and follow the work.
**Why:** AUT-115 the work moved to AUT-118; canary kept watching AUT-115 and reported every downstream stage as missing.
**Scope:** global
**How to apply:** Any orchestrator-side script that watches an Issue's progress (canary.js, orchestrator.js, watchers in `.tmp/`). On detecting a child Issue creation by the current agent, retarget polling.

## Linked artifacts

- Issue: AUT-115
- Child build: AUT-118
- Branch: `paperclipai-builds/build/AUT-118` (staged inactive, Joaquin owns merge)
- Backfilled into the learning system on 2026-06-01 as seed data for the `recall-learnings` skill.
