---
name: AUT-123-rechnungs-erinnerung-client-build
description: Implementation child of AUT-119 CLIENT canary — n8n workflow + TESTING.md shipped. Most relevant retro for the routing-bugs cleanup since it's where they surfaced.
type: retro
scope: issue:AUT-123
created: 2026-05-31
issue: AUT-123
shipped_at: 2026-05-31
roles_involved: [engineer, qa-engineer, product-engineer, presentation-designer, release-engineer]
tags: [client-build, n8n, notion-tag-bug, ctod-routing, stuck-in-qa, treuhand-persona]
---

## Context

Implementation child Issue spawned by CTO from the AUT-119 CLIENT canary parent. Target artifact: an n8n Rechnungs-Erinnerung workflow (invoice reminder) for the Treuhand persona, plus customer-facing PRESENTATION.md + TESTING.md.

## What we expected

Standard child-Issue flow: Engineer implements + validates → QA pin-data tests → Product reviews intent → Presentation Designer makes the customer artifacts → Release Engineer pushes to `paperclipai-builds/build/AUT-123`. ~25 min.

## What actually happened

Worked but slow + sloppy. Two issues stood out:

1. **QA got stuck waiting on an "approve" interaction** that wasn't actually needed. The `terminal-bench-loop` skill expected a confirmation comment that QA never required for a pure pin-data test. Manual unstick. Spent ~10 min on the wrong loop.

2. **Notion node `simple:true` silently dropped nested fields** in the test fixture. Engineer's initial workflow code had `simple: true` on the Notion Get Database Item node — pin-data test passed (because the test fixture happened to use flat fields), but on a realistic shape with nested `due_date.start` the node returned `null`. Found by reviewing the workflow code manually; would have failed in production. This is a known-pattern (already in `decisions/log.md` 2026-04-26 entry) but Engineer didn't apply it.

## Carry-forward learnings

### 1. Notion node ALWAYS: `simple:false` AND `returnAll:true`

**Rule:** Every n8n Notion node — `getDatabaseItem`, `getMany`, `query` — gets `simple: false` and `returnAll: true`. No exceptions. Validate it's set before posting `READY_FOR_TEST`.
**Why:** AUT-123 — Engineer used `simple: true`, pin-data happened to pass, real shape would have silently dropped `due_date.start` and produced a null reminder body. The decisions/log.md 2026-04-26 entry documents this — but the Engineer wasn't reading the right context. With `recall-learnings` now wired, this learning is now in `global.md` and will be in every Engineer's recall block.
**Scope:** role:engineer
**How to apply:** Anytime touching an n8n Notion node. Treat `simple:true` and the default `returnAll:false` as bugs. If a workflow is reading existing nodes and they're set wrong, fix them in the same PR.

### 2. QA's terminal-bench-loop wait-for-approve should be SKIPPED on pure pin-data tests

**Rule:** When running pin-data tests on an n8n workflow (no real external state mutation), QA does NOT wait for an "approve" interaction comment. Just run the test, post `TEST_PASS` or `TEST_FAIL`, reassign. The approve loop is for tests that mutate live state.
**Why:** AUT-123 — QA sat for 10 min waiting on an approval that wasn't designed-in. Wasted heartbeat budget + delayed the ship.
**Scope:** role:qa-engineer
**How to apply:** Check the test type before invoking the wait-for-approve branch. Pin-data + sandbox-only Notion test = no approve. Live-deploy or paid-API call = halt-before-acting per CLAUDE.md.

## Linked artifacts

- Issue: AUT-123 (child of AUT-119 parent)
- Parent: AUT-119 (CLIENT canary)
- Branch: `paperclipai-builds/build/AUT-123`
- Backfilled into the learning system on 2026-06-01 as seed data.
