---
name: recall-learnings
description: >
  Before doing any work, recall accumulated operator feedback + prior lessons so you don't
  re-make a correction someone already typed. Read-only. Use on every heartbeat.
---

# Recall Learnings (Revenue Lab)

Paperclip agents are stateless across runs. Operator corrections and prior lessons live in
files — read them before acting so you don't re-discover them the expensive way.

## What to read (in order, ~4KB total cap)

Revenue Lab keeps its OWN learnings (separate from Automatisierbar's). Company root on the VPS:
`~/_context/tools/paperclip/companies/revenue-lab/`.

1. **`learnings/global.md`** (this company's) — what prior Revenue Lab runs got wrong + the
   binding rules that came out of it. Highest priority. Read all of it.
2. **`learnings/by-role/<your-urlKey>.md`** (`ceo` / `builder` / `qa-reviewer` / `finance-ops`)
   — your role's history, if the file exists. Skip silently if it doesn't.

Do NOT read Automatisierbar's `~/_context/references/learnings/` — that is a different company's
feedback and would re-introduce Automatisierbar context/brand. Revenue Lab learnings only.

## Emit a private recall preamble (do not post it)

Before your first tool call, internally summarize what you found:

```markdown
## Recall (loaded YYYY-MM-DD)
Operator feedback (N): - [<slug>]: <one-line>  (<date>)
Global lessons (N):    - [<slug>]: <one-line>  (<date>)
For this role (N):     - [<slug>]: <one-line>  (<date>)
```

If a section is empty, write `- (none)` — explicit zero is informative.

## Hard rules

1. **Read-only.** This skill never writes to a learning file.
2. **Recall before work**, not after.
3. **If a recall entry contradicts the current task, surface the conflict** (quote both, flag
   for the operator) — don't silently override. Especially relevant for Revenue Lab's money
   rules: if a task asks you to spend/send in a way operator-feedback warns against, halt.
4. **If a file is missing**, note it once and move on — don't error or halt.
