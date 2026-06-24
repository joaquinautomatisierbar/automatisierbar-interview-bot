---
name: recall-learnings
description: >
  Before doing any work on the assigned Issue, recall accumulated operational lessons from prior runs — global learnings, operator feedback, your own role's history, and the last few shipped Issues — so you don't re-make mistakes someone already corrected.
  Use on every heartbeat, regardless of wake reason.
---

# Recall Learnings

You are about to start work on an Issue. Before you do anything else, **read the accumulated learnings** from prior agent runs. The other paperclip agents and the operator have already learned things — you should not re-discover them from scratch.

## Why this matters

Paperclip agents were stateless across runs until this skill existed. When the operator typed a correction once (e.g. *"don't auto-default to n8n"*, *"Coiffeur/Restaurant are NOT ICP"*, *"Anthropic via HTTP Request, not the dedicated node"*), it landed in their Claude Code memory — invisible to you. When a prior shipped Issue surfaced a non-obvious bug (canary regex over-matched, parent→child routing didn't pivot, Notion `simple:true` silently dropped fields), that learning lived in `RELIABILITY.md` or comments — also invisible to you on the next Issue.

Now those learnings live in `~/_context/references/learnings/` and `~/_context/references/retros/`, synced from the operator's repo via `sync-context.sh`. Read them first.

## What to read (in this exact order)

The mount path on the VPS is `~/_context/references/`. On the operator's MacBook the same path works for local agent testing.

### 0. Live company state — every agent reads this FIRST

Before any learnings, load the live company-state snapshot. It tells you what's actually happening at the firm right now — active clients, the latest founder sync's decisions, this-week's wins + blockers. This is the *highest priority* recall layer because it's decision-load-bearing context.

Read in order (cap ~2KB across all four combined):

1. `~/_context/references/company-state/founder-syncs.md` — last 1-2 founder syncs, lightly cleaned. Most-recent gets priority; older syncs truncate if budget is tight.
2. `~/_context/references/company-state/active-clients.md` — Lead-DB rows in active pipeline stages (Paying / Pilot / Prototype / Process Mapping / Workflow Interview).
3. `~/_context/references/company-state/this-week.md` — 7-day signals: commits, decisions logged, Notion movement, n8n executions.
4. `~/_context/references/company-state/team-capacity.md` — baseline team availability + active commitments.

Refreshed twice daily on VPS via systemd timer (`sync-company-state.timer`). If `last_refreshed` is >36h old, flag the staleness in your recall block but proceed with what's there. If the directory is missing entirely (snapshot never ran), skip Step 0 and proceed to Step 1.

### 1. Global learnings — every agent reads this

Read `~/_context/references/learnings/global.md`. Cross-role operational lessons. Cap at ~3KB / first ~80 lines if the file has grown long; take the most-recent-N entries by `created` date.

### 2. Operator feedback — every agent reads this

Read `~/_context/references/learnings/operator-feedback.md`. Mirror of operator corrections typed in their Claude Code session via the `/remember` skill. Same cap — ~3KB / first ~80 lines / most recent.

### 3. Your role's learnings

Read `~/_context/references/learnings/by-role/<your-urlKey>.md` where `<your-urlKey>` is the agent's role. The urlKey is in the agent's profile (`GET /api/agents/<id>` → `urlKey` field). Examples:

- CTO → `by-role/cto.md`
- Engineer → `by-role/engineer.md`
- QA Engineer → `by-role/qa-engineer.md`
- Product Engineer → `by-role/product-engineer.md`
- Release Engineer → `by-role/release-engineer.md`
- Internal Planner → `by-role/internal-planner.md`
- Test Data Generator → `by-role/test-data-generator.md`
- Presentation Designer → `by-role/presentation-designer.md`
- PR Director → `by-role/pr-director.md`
- Copy Writer → `by-role/copy-writer.md`
- Hook Strategist → `by-role/hook-strategist.md`
- Image Curator → `by-role/image-curator.md`
- CEO → `by-role/ceo.md`

If your role's file doesn't exist (newly-added role), skip and move on — don't error.

### 4. Recent retros (last 5)

Read `~/_context/references/retros/INDEX.md` and identify the last 5 retros by `shipped_at` desc. For each one whose tags or roles_involved overlap the current Issue's tags or your own role, open the retro file and read its **Carry-forward learnings** section. Skip retros with zero overlap.

Cap: read at most 5 retros, ~1KB each.

## What to emit (your working context preamble)

Before posting your first comment / making your first tool call on the Issue, internally summarize what you found as a compact recall block. Treat this as a private preamble — do not post it as a comment. Use it to inform your decisions throughout the run.

Shape:

```markdown
## Recall (loaded YYYY-MM-DD)

Company state (refreshed YYYY-MM-DDTHH:MM):
- **Active clients:** <e.g. Bieri (pilot, Nico, waiting on IT install), Juglans (pilot, Tej), Filip (pilot, Joaquin)>
- **Last founder sync:** YYYY-MM-DD — <one-line summary of decisions / blockers / capacity changes>
- **This week:** <N issues shipped, N decisions logged, N hot leads, active halts: …>
- **Team:** <who's on capacity / who's blocked>

Global operational lessons (N):
- [<slug>]: <one-line description>  (<date>, from <issue or "operator">)
- …

Operator feedback (N):
- [<slug>]: <one-line description>  (<date>)
- …

For this role (<role>, N entries):
- [<slug>]: <one-line description>  (<date>, from <issue>)
- …

Relevant prior retros (N):
- [AUT-XXX <short-slug>]: <one-line summary of carry-forward learnings>  (shipped <date>)
- …
```

Budget allocation (cap ~120 lines total): company-state ~25 lines / global learnings ~20 / operator-feedback ~25 / role-scoped ~30 / retros ~20. If company-state is empty (snapshot never ran or all files missing), gracefully degrade — drop the Company-state section entirely, agents still see learnings.

If a section is empty, write `- (none)` rather than dropping the section — explicit zero is informative.

## Hard rules

1. **Read-only.** This skill never writes to any learning file. Operator corrections come in via `/remember`; retros come in via `write-retro`. You do not.
2. **Recall happens before work, not after.** Don't post your first comment, open files, or call tools without having loaded the recall block.
3. **Honor the caps.** ~120 lines / ~6KB total across all four sources combined. If you'd blow past the cap, prefer global + operator-feedback first (cross-role signals), then your role, then retros — and note `(N additional entries omitted; see ~/_context/references/learnings/)` at the end.
4. **If a recall entry contradicts the current brief**, do NOT silently override the recall. Surface the conflict: post a comment quoting both, flag it for the operator. Recall is "stuff someone learned the hard way" — the brief might be wrong, or the recall might be stale. Either way the operator decides.
5. **If a file is missing** (mount stale, new role not yet seeded), log it once in your run notes and move on. Don't error, don't halt.
6. **No deduplication across sources.** If the same learning appears in both `global.md` and your `by-role/<role>.md`, list it once with both scopes noted (`(global + role)`).

## When to skip

Skip the entire recall step ONLY if:
- The Issue title starts with `[NOOP]` or `[META]` (internal infrastructure work that doesn't touch real state).
- You are explicitly waking *just* to post a SHIP / TEST_PASS marker as the final step (recall already happened on a prior heartbeat for this Issue).

Otherwise: always recall. Cost is ~5 file reads + a 200-token preamble — negligible compared to the cost of repeating a known-bad pattern.

## Verification (cold-test cases)

- **Empty-mount test:** mount is fresh, all learning files contain only frontmatter / comments. Expected: recall block has all four sections marked `(none)`. Agent proceeds.
- **Stale-mount test:** sync-context.sh hasn't run in >7 days; learnings exist locally but mount is old. Expected: agent uses what's there, logs the staleness, doesn't fail.
- **Contradiction test:** `operator-feedback.md` says "always halt before paid-API backfill," but Issue brief says "run a 200-row backfill." Expected: agent surfaces the conflict via a comment + halts, doesn't blindly execute the brief.
- **Role-missing test:** new agent role added without seeding the by-role file. Expected: skips `by-role/<role>.md`, recall block notes "(no role-scoped file yet)", proceeds.
