# Learnings — Index

Append-only operational lessons. Read by every paperclip agent at activation via the `recall-learnings` skill, and by the operator's Claude Code session as part of the `~/_context/` mount.

**Where it comes from:**
- `write-retro` paperclip skill — appends 1-3 entries per shipped Issue, sourced from the Issue's comment + run history.
- `/remember` Claude Code skill (operator side) — operator types a correction once, it lands here (paperclip-visible) AND in operator MEMORY.md (session-visible).
- Manual backfill — high-value lessons from past Issues (AUT-115, AUT-119, AUT-123).

**Where it does NOT belong:**
- Architectural decisions → [decisions/log.md](../../decisions/log.md) (forward-looking choices, not reflective lessons).
- Operational SOPs → [tools/paperclip/RELIABILITY.md](../../tools/paperclip/RELIABILITY.md) (forward-facing health contract, not lessons).
- Static business facts → [references/business-context.md](../business-context.md).
- Distilled book frameworks → [references/library/INDEX.md](../library/INDEX.md).

**Frontmatter convention** (every entry uses this):

```yaml
---
name: short-kebab-case-slug
description: one-line summary (the recall skill uses this as the relevance signal)
type: learning
scope: global | role:<role-slug> | issue:<AUT-XXX>
created: YYYY-MM-DD
issue: AUT-XXX        # optional — where the learning was first surfaced
tags: [tag1, tag2, …]
---
```

---

## Scopes

### Global (cross-role)
- [global.md](global.md) — operational lessons every agent should know

### Operator feedback (mirror of Claude Code MEMORY.md feedback entries)
- [operator-feedback.md](operator-feedback.md) — corrections + preferences typed once by operator, propagated to paperclip via the `/remember` skill

### Role-scoped (read only by the agent in that role)
- [by-role/ceo.md](by-role/ceo.md)
- [by-role/cto.md](by-role/cto.md)
- [by-role/engineer.md](by-role/engineer.md)
- [by-role/qa-engineer.md](by-role/qa-engineer.md)
- [by-role/product-engineer.md](by-role/product-engineer.md)
- [by-role/release-engineer.md](by-role/release-engineer.md)
- [by-role/internal-planner.md](by-role/internal-planner.md)
- [by-role/test-data-generator.md](by-role/test-data-generator.md)
- [by-role/presentation-designer.md](by-role/presentation-designer.md)
- [by-role/pr-director.md](by-role/pr-director.md)
- [by-role/copy-writer.md](by-role/copy-writer.md)
- [by-role/hook-strategist.md](by-role/hook-strategist.md)
- [by-role/image-curator.md](by-role/image-curator.md)

### Retros (per-Issue postmortems)
- [../retros/INDEX.md](../retros/INDEX.md)

---

## Health snapshot (updated by `/audit`)

The `/audit` skill reports learning density and retro coverage as part of its Context + Cadence scoring. Re-run weekly. If learning density stays at zero for >2 weeks while Issues are shipping, the `write-retro` skill is broken — open an [INTERNAL] Issue via Internal Planner.
