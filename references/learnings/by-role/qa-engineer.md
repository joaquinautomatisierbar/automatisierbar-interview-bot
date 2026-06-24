# Learnings — qa-engineer

Role-scoped operational lessons for the **qa-engineer** agent. Read at activation by the `recall-learnings` skill. Append-only.

Frontmatter convention: see [../INDEX.md](../INDEX.md).

---

<!--
Entries below. Sorted reverse-chronological (newest first).
The `write-retro` skill appends a new entry here when a shipped Issue
surfaces a role-specific learning. The operator can also append via
`/remember --paperclip-only` if a correction is role-specific.

Empty at creation. First entries arrive after the first `write-retro` run
or backfill of AUT-115 / AUT-119 / AUT-123.
-->

## skip-approve-wait-on-pin-data-tests

---
name: skip-approve-wait-on-pin-data-tests
description: Pin-data tests on n8n workflows do NOT require an "approve" interaction — terminal-bench-loop's wait-for-approve branch is for live-state mutations only
type: learning
scope: role:qa-engineer
created: 2026-05-31
issue: AUT-123
tags: [terminal-bench-loop, pin-data, stuck-loop, time-wasted]
---

When running pin-data tests on an n8n workflow (no real external state mutation), QA does NOT wait for an "approve" interaction comment. Just run the test, post `TEST_PASS` or `TEST_FAIL`, reassign. The approve-wait branch is for tests that mutate live state.

**Why:** AUT-123 — QA sat for 10 min waiting on an approval that wasn't designed-in. Wasted heartbeat budget + delayed the ship. The `terminal-bench-loop` skill's wait-for-approve fires conservatively (good default) but should be bypassable when no real state changes.

**How to apply:** Check the test type before invoking the wait-for-approve branch. Pin-data + sandbox-only Notion test = no approve, just run + report. Live-deploy or paid-API call = halt-before-acting per CLAUDE.md (which is a different surface — operator Telegram, not in-Issue approve).

Carried forward from [retro AUT-123](../../retros/AUT-123-rechnungs-erinnerung-client-build.md).
