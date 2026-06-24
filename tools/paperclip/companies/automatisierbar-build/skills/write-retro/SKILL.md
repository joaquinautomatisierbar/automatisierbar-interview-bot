---
name: write-retro
description: >
  When the Release Engineer is about to post the terminal SHIP marker on a CLIENT-BUILD or INTERNAL Issue, first synthesize a retro from the Issue's full comment + run history and post it as a RETRO comment. Operator later pulls these comments into `references/retros/` via a sync script.
  Runs ONCE per shipped Issue, immediately before SHIP. Read-only on history, write-only via one Issue comment.
---

# Write Retro

You are the Release Engineer. You are about to post `SHIP`. Before you do, **synthesize a retro** so the next agent (or you, on the next Issue) doesn't have to re-discover what this Issue taught.

## Why this matters

Before this skill existed, every shipped Issue's learnings were lost the moment the Issue closed. The recall path (`recall-learnings` skill) reads `~/_context/references/retros/` — but that directory only contains what `write-retro` has produced. If you skip this skill, your future self learns nothing from this Issue. The operator paid for this run; capture the lesson.

## When to run

Run **exactly once per Issue**, on the heartbeat immediately before you post `SHIP`. If this is a re-ship (Issue went `in_review` → re-routed → re-shipped), check the Issue comments for an existing `RETRO:` marker. If one exists, append a `RETRO-DELTA:` comment with what's new since last retro instead of writing a fresh retro from scratch.

Do NOT run on:
- `TEST_FAIL` / `NEEDS_QOL` / `BLOCKED` routings — these aren't terminal.
- `[NOOP]` or `[META]` infrastructure Issues that didn't ship a real artifact.

## What to read

Use the paperclip API at `http://127.0.0.1:3100` (running on this host, no auth needed for the loopback):

1. **Issue meta:** `GET /api/issues/<issue-id>` — title, tag, projectId, parent/children, createdAt.
2. **Full comment history:** `GET /api/issues/<issue-id>/comments` — every comment, in order. Authors are agent IDs; resolve to `urlKey` via `GET /api/companies/<cid>/agents`.
3. **Full run history:** `GET /api/issues/<issue-id>/runs` — start/end times, status, agent per run, cost if reported.
4. **Parent issue** (if `parentId` is set): also read its comments to see operator framing + clarifying questions.

## What to identify

Cap at 3 carry-forward learnings per Issue — quality over quantity. Look for these signal patterns:

### Surprises
A moment where reality diverged from the plan. Example: *"Pin-data test passed but the live-data run failed because the Notion node silently drops nested objects when simple:true."* Find these by scanning for `TEST_FAIL` comments + their resolution + any `NEEDS_QOL` routing.

### Operator corrections
Comments from `urlKey="operator"` (the human) that redirected the agent. Example: *"don't use the dedicated Anthropic node, use HTTP Request."* These are the highest-value learnings — they capture a preference the operator might otherwise have to type again next Issue.

### Reusable patterns
Something that worked unusually well and would speed up the next similar Issue. Example: *"Pin-data tests with three shapes (golden / edge / failure) caught the schema-drift bug before deploy. This pattern should be the default for any Notion-writing workflow."*

If you find fewer than 3 learnings — that's fine. Don't pad. Write 1 if there's only 1. Write 0 and skip the RETRO comment entirely if the Issue was genuinely uneventful (rare).

## What to write

Post **one** comment on the Issue. First line is the marker `RETRO:` followed by the slug. Body is the full retro Markdown content with frontmatter, ready for the operator's pull script to write directly to `references/retros/AUT-XXX-<slug>.md`.

### Comment template

```markdown
RETRO: AUT-XXX-<short-slug>

---
name: AUT-XXX-<short-slug>
description: <one-line summary of what shipped + the key learning>
type: retro
scope: issue:AUT-XXX
created: <today YYYY-MM-DD>
issue: AUT-XXX
shipped_at: <today YYYY-MM-DD>
roles_involved: [cto, engineer, qa-engineer, product-engineer, release-engineer]
tags: [n8n, telegram, notion, ...]
---

## Context

<one sentence: what was being built and why>

## What we expected

<the plan as the CTO described it in their PLAN_LOCKED comment, 2-3 sentences>

## What actually happened

<divergence points, cited from comments. At least one surprise OR operator correction. If everything went exactly to plan, say so explicitly — that's also a learning.>

Cite specific comments: e.g. "Engineer's TEST_FAIL at 2026-06-01T14:32 surfaced the `simple:true` bug" or "Operator's correction in comment 14 redirected stack from n8n to Trigger.dev."

## Carry-forward learnings

### 1. <short title>

**Rule:** <one-line>
**Why:** <which comment / run surfaced this>
**Scope:** <global | role:<role> | operator-feedback>
**How to apply:** <when does this kick in on a future Issue>

### 2. <short title>

... (up to 3)

## Linked artifacts

- Branch: <paperclipai-builds branch URL or system-repo branch>
- PR: <if applicable>
- n8n workflow: <ID if applicable>
- Issue: <AUT-XXX>
```

### Slug rules

Slug is kebab-case, max 40 chars, derived from Issue title. Drop tag prefix (`[CLIENT-BUILD]`, `[INTERNAL]`), drop articles. Examples:
- Title: `[INTERNAL] Fix canary.js marker detection — first-line + author-id check` → slug: `fix-canary-marker-detection`
- Title: `[CLIENT-BUILD] Priority inbox Slack alert for Ruth` → slug: `priority-inbox-slack-ruth`

## Hard rules

1. **Read-only on history.** Don't edit prior comments. Don't reassign the Issue. Don't change Issue status. The write is exactly one new comment.
2. **No invented learnings.** Every carry-forward learning MUST cite a specific comment, run, or artifact change. If you can't cite it, you didn't learn it from this Issue.
3. **No fluff.** "Communication was smooth" is not a learning. "Operator preferred Trigger.dev over n8n for cron-heavy work" IS.
4. **No real customer data in the retro.** If the Issue had real customer names / emails / phones in the brief, paraphrase ("the Treuhand client") rather than quoting. Retros are mirrored to the public-ish operator repo.
5. **Single RETRO comment per Issue.** Re-ships get `RETRO-DELTA:` follow-ups; don't write a fresh RETRO every time the Issue cycles.
6. **The SHIP marker is your NEXT comment.** Post RETRO first; then in the immediately-following comment post SHIP with its normal body. Never mix them.

## How operator pulls retros into the repo

The operator runs (locally on their MacBook):

```bash
bash tools/paperclip/scripts/pull-retros.sh
```

That script scans recent Issues (last 30 days) for `RETRO:` comments without a corresponding file in `references/retros/`, writes each comment's body verbatim to `references/retros/<slug>.md`, and also appends the carry-forward learnings to the right scope file (`global.md` / `by-role/<role>.md` / `operator-feedback.md`) + updates the INDEX files.

Then the operator runs `git diff references/` to review, commits, and pushes. No GitHub PAT needed on your end.

Per the Bike-Method Phase-1 default, every retro is operator-reviewed before it lands in the repo. After 8 retros review-passed without edits, the operator may enable auto-commit in `pull-retros.sh` (Phase 2).

## Verification (cold-test cases)

- **Uneventful Issue:** plan → build → test pass → ship, no surprises. Expected: no RETRO comment, skill exits cheerfully. Operator-side `pull-retros.sh` shows no new files.
- **Operator-correction Issue:** Issue had a comment from urlKey=operator redirecting the agent (e.g. "use Trigger.dev not n8n"). Expected: RETRO comment with at least 1 `operator-feedback`-scoped learning citing that comment.
- **Re-ship Issue:** Issue cycled QA→Engineer→QA→ship. Expected: one RETRO comment from the FIRST ship, not duplicated; second ship adds RETRO-DELTA.
- **Real-customer-data sanitize:** Issue brief contained "Andrea Meier, Meier Treuhand AG, 044 555 11 22". Expected: retro paraphrases as "the Treuhand client" — no PII quoted.
