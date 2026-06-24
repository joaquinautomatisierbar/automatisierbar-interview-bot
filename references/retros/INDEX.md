# Retros — Index

Per-Issue postmortems. One file per shipped Issue (CLIENT-BUILD or INTERNAL). Written by the `write-retro` paperclip skill at the moment of `SHIP`, sourced from the Issue's full comment + run history.

**File naming:** `AUT-<id>-<short-slug>.md`. Slug is kebab-case, derived from Issue title (truncated to ~40 chars).

**Frontmatter convention:**

```yaml
---
name: AUT-XXX-short-slug
description: one-line summary of what shipped + key learning
type: retro
scope: issue:AUT-XXX
created: YYYY-MM-DD
issue: AUT-XXX
shipped_at: YYYY-MM-DD
roles_involved: [cto, engineer, qa-engineer, product-engineer, release-engineer]
tags: [n8n, telegram, …]
---
```

**Body sections** (used by `write-retro` template):

1. **Context** — 1 sentence, what was being built and why.
2. **What we expected** — the plan as described in the brief.
3. **What actually happened** — divergence points; ≥1 surprise; operator corrections (cite specific comments).
4. **Carry-forward learnings** — 1-3 entries. Each entry mirrors a fresh entry appended to the right scope file (`global.md`, `operator-feedback.md`, or `by-role/<role>.md`).
5. **Linked artifacts** — branch URLs (paperclipai-builds, system repo), GitHub PR URLs, n8n workflow IDs.

---

## Recent retros (sorted by `shipped_at` desc)

- [AUT-123 rechnungs-erinnerung-client-build](AUT-123-rechnungs-erinnerung-client-build.md) — shipped 2026-05-31 — Notion `simple:true` bug + QA stuck-on-approve, both backfilled into role-scoped learnings
- [AUT-119 client-canary-rechnungs-erinnerung](AUT-119-client-canary-rechnungs-erinnerung.md) — shipped 2026-05-31 — first full CLIENT canary; surfaced `[CLIENT-BUILD]` routing equivalence + 3x wall-clock budget vs INTERNAL
- [AUT-115 canary-pipeline-heartbeat](AUT-115-canary-pipeline-heartbeat.md) — shipped 2026-05-30 — INTERNAL canary validated wakeOnDemand fix; surfaced flat-blob regex false-positives + missing parent→child pivot
