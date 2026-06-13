---
name: recall-learnings
description: >
  Before doing any work, recall accumulated operator feedback + prior lessons so you don't
  re-make a correction someone already typed. Read-only. Use on every heartbeat.
---

# Recall Learnings (Revenue Lab)

Paperclip agents are stateless across runs. Operator corrections and prior lessons live in
files — read them before acting so you don't re-discover them the expensive way.

## What to read (in order, ~6KB total cap)

Mount path on the VPS: `~/_context/references/`. The same paths work on the operator's MacBook
for local testing.

1. **`~/_context/references/learnings/operator-feedback.md`** — mirror of operator corrections
   typed via `/remember`. Highest priority. Cap ~3KB / most-recent entries.
2. **`~/_context/references/learnings/global.md`** — cross-role operational lessons. Cap ~3KB.
3. **`~/_context/references/learnings/by-role/<your-urlKey>.md`** — your role's history
   (`ceo` / `builder` / `finance-ops`). If the file doesn't exist yet, skip — don't error.

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
