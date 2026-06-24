---
name: AUT-119-client-canary-rechnungs-erinnerung
description: First CLIENT canary running through the full client-build pipeline (with Presentation Designer step) — 60 min end-to-end, surfaced multiple Gate-B routing bugs
type: retro
scope: issue:AUT-119
created: 2026-05-31
issue: AUT-119
shipped_at: 2026-05-31
roles_involved: [cto, engineer, qa-engineer, product-engineer, presentation-designer, release-engineer]
tags: [canary, client-build, n8n, parent-child-routing, agents-md-routing, gate-b]
---

## Context

First CLIENT canary running the full client-build pipeline (CTO → Engineer → QA → Product → Presentation Designer → Release). Brief: a simple n8n Rechnungs-Erinnerung workflow (invoice reminder) targeting the Treuhand persona. Goal: validate the CLIENT path with Presentation Designer in the loop, after AUT-115 proved the INTERNAL path.

## What we expected

15-25 min if the wakeOnDemand fix held + Presentation Designer ran cleanly. Real artifacts (workflow code + PRESENTATION.md + TESTING.md + process-diagram.svg + roi-page.html) pushed to `paperclipai-builds/build/AUT-119`.

## What actually happened

60 min — much slower than INTERNAL canary. Surfaced 3 distinct routing bugs that all needed orchestrator-side fixes (not agent-prompt fixes):

1. **Parent→child pivot missing in orchestrator** — same root cause as AUT-115 carry-forward. CTO spawned child AUT-122 / AUT-123 for the implementation work, but the orchestrator's auto-flow logic kept routing based on AUT-119's state.

2. **AGENTS.md routing rules drifted from `[CLIENT]` to `[CLIENT-BUILD]`** — the child Issue's title was tagged `[CLIENT-BUILD]` (correct: it's an implementation child of a CLIENT parent), but Engineer / QA / Product agents' routing checks only matched `[CLIENT]` literal. Each role's AGENTS.md needed an explicit note: "treat `[CLIENT-BUILD]` as `[CLIENT]` for every rule." Fix: added that note in 5 AGENTS.md files.

3. **Presentation Designer skipped on first run** — Product Engineer posted SHIP and routed straight to Release Engineer because the route-decision logic checked the parent's tag instead of the child's tag (parent was `[CLIENT]`, child was `[CLIENT-BUILD]`, the routing table only matched against exact `[CLIENT]`). Re-routed manually.

## Carry-forward learnings

### 1. CLIENT-BUILD is a tag, not a typo

**Rule:** `[CLIENT-BUILD]` is the correct tag for implementation children of `[CLIENT]` / `[CLIENT-DEMO]` parents. Every agent's AGENTS.md routing logic must treat `[CLIENT-BUILD]` identically to `[CLIENT]`. Same applies to `[CLIENT-PROD]` for prod-rollout children.
**Why:** AUT-119/122/123 — three roles' routing logic broke because they only matched `[CLIENT]` literal. Manual re-routing burned ~15 min.
**Scope:** global
**How to apply:** Anytime adding routing logic to a paperclip agent's AGENTS.md (Engineer, QA, Product, Presentation Designer, Release): include the explicit equivalence note. Reuse the existing wording: *"Note on child-issue tags: `[CLIENT-BUILD]` (in the issue title) is the tag for implementation children spawned from `[CLIENT]` / `[CLIENT-DEMO]` parents. Treat `[CLIENT-BUILD]` as `[CLIENT]` for every rule below."*

### 2. CLIENT canary takes ~3x INTERNAL because Presentation Designer adds 15-25 min

**Rule:** When budgeting wall-clock for a CLIENT/CLIENT-BUILD pipeline run, account for Presentation Designer being on the critical path. Realistic min/max: 30-50 min on a simple workflow; 50-90 min on anything with custom SVG diagrams or honest-ROI math beyond defaults.
**Why:** AUT-119 took 60 min vs AUT-115's 8 min; Presentation Designer added ~25 of those (one full heartbeat to draft the process-diagram.svg + the roi-page.html + the live-demo-script.md).
**Scope:** global
**How to apply:** Any time scoping a CLIENT-build run or quoting an ETA. Don't promise "ships in 15 min" — that's the INTERNAL ETA, not the CLIENT one.

## Linked artifacts

- Issue: AUT-119 (parent CLIENT canary)
- Child build: AUT-118 / AUT-122 / AUT-123 (Rechnungs-Erinnerung n8n workflow)
- Branch: `paperclipai-builds/build/AUT-119`
- Backfilled into the learning system on 2026-06-01 as seed data.
