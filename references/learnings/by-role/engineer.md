# Learnings — engineer

Role-scoped operational lessons for the **engineer** agent. Read at activation by the `recall-learnings` skill. Append-only.

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

## n8n-notion-node-simple-false-return-all-true

---
name: n8n-notion-node-simple-false-return-all-true
description: Every n8n Notion node — getDatabaseItem, getMany, query — MUST be set simple:false AND returnAll:true. No exceptions.
type: learning
scope: role:engineer
created: 2026-05-31
issue: AUT-123
tags: [n8n, notion, data-shape, silent-bug]
---

Every n8n Notion node — `getDatabaseItem`, `getMany`, `query` — gets `simple: false` and `returnAll: true`. No exceptions. Validate it's set before posting `READY_FOR_TEST`.

**Why:** AUT-123 — Engineer used `simple: true`; pin-data happened to pass (test fixture had flat fields), real production shape would have silently dropped `due_date.start` and produced a null reminder body. The `decisions/log.md` 2026-04-26 entry documents this rule — but the Engineer wasn't reading the right context. With `recall-learnings` now wired (this file), the lesson reaches every Engineer run.

**How to apply:** Anytime touching an n8n Notion node. Treat `simple:true` and the default `returnAll:false` as bugs. If a workflow is reading existing nodes and they're set wrong, fix them in the same PR.

Carried forward from [retro AUT-123](../../retros/AUT-123-rechnungs-erinnerung-client-build.md).
