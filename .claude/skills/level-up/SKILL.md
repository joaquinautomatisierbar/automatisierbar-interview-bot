---
name: level-up
description: Use when the operator asks "what should I automate next", "find me leverage this week", "let's level up", or as a Friday ritual. Walks the operator-principles interview — Mindset (find the candidate) → Method (scope one) → Machine (build it via WAT). One run = one shipped artifact. Reads operator-principles.md, decisions/log.md, connections.md, workflows/, and recent activity. Logs the decision + ships a workflow / tool / skill / prompt.
---

## What this skill does

Walks the operator through finding **one** new automation per run, scoping it cleanly, and shipping the artifact — through the lens of `references/operator-principles.md`. Rewires the operator's brain to spot leverage mid-week without prompting.

**One interview = one artifact.** Not a multi-candidate planner. Not a coach. Not a status report.

> Adapted from the Three Ms framing in Nate Herk's AIS-OS. Tied here to our WAT framework, n8n MCP toolchain, halt-poll surface, and `/loop` + `/schedule` patterns.

## What `/level-up` is NOT

- Not `/audit`. `/audit` is structural ("is the AIOS built right?"). `/level-up` is functional ("what business leverage am I missing?"). If `/audit` says structure is messy (Stage 0/1), fix that first.
- Not multi-candidate scoping. One run = one shipped artifact.
- Not a coach. The operator does the thinking. The skill conducts the interview and ships the artifact.

## When to run

- **First fit:** after `/audit` shows ≥40/100 (Stage 1 or higher) AND ≥1 tier-1 domain is reachable. Earlier produces trivial output.
- **Cadence:** weekly Friday afternoon. Review the week, surface one automation, ship it.
- **On-demand:** any time a manual task itches mid-week.

## Inputs the skill reads

- `references/operator-principles.md` — the framework (used to quote principles back when relevant)
- `decisions/log.md` — recent decisions (don't re-scope what's already in flight; check Eliminate outcomes)
- `connections.md` — what's reachable, by what mechanism, RW or R-only
- `workflows/*.md` — current capability surface + autonomy levels
- `tools/*.py` — what deterministic primitives we already have (don't re-build)
- `~/.claude/projects/-Users-sexyjoaquin-*/memory/MEMORY.md` + relevant memory files — recent context
- `audits/audit-*.md` if present — most recent audit report
- `.claude/skills/*/SKILL.md` frontmatter — what skills already exist

## Execution — three phases

### Phase 1 — Mindset interview (find the candidate)

Surface 1–3 candidates ranked by leverage. Ask conversationally:

1. *"Walk me through your week. What did you do 3+ times by hand?"* (frequency)
2. *"Anything that felt manual, boring, copy-paste, or tab-switchy?"* (drudgery)
3. *"Anything where you thought 'a smart intern could handle this'?"* (delegation candidate)
4. *"If 5x more cold-call audio landed tomorrow, what would break first?"* (constraint at scale)
5. *"What would 5x your cold-call hot-lead conversion?"* (growth lever)

Quote relevant Mindset principles when they fit (don't force them):
- *"Sounds like the Default Shift applies — to what extent could AI be leveraged on this slice?"*
- *"This is Function Breakdown — you're not automating the whole role, just this one piece."*
- *"AI is better than it was last quarter. If it couldn't do this six months ago, it might be ready now."*

**Output of Phase 1:** numbered list of 1–3 candidate opportunities, one-line "why this is leverage" per candidate, tied back to a current priority or pain point if visible in memory / `decisions/log.md`. Then ask: *"Pick one to scope."*

### Phase 2 — Method interview (scope one)

Operator picks one candidate. Walk the 5-step Method pipeline:

**Step 1 — Find the constraint.** Which bottleneck does this solve, or which growth lever does it open? Tie back to Phase 1 answers + recent project state (e.g. Cold-Call Phase 2 build, LinkedIn engagement, etc.).

**Step 2 — EAD: Eliminate / Automate / Delegate.**

- **Eliminate first:** *"What happens if we just stop doing this?"* If the answer is "nothing breaks" → skill exits cheerfully. *"Don't automate waste."* This is a win — log to `decisions/log.md` as an Eliminate outcome and stop.
- **Automate second:** apply 60/30/10 framing. ~60% deterministic, ~30% AI-assisted, ~10% manual. State which slice each piece falls into.
- **Delegate third:** if too complex / variable / judgment-heavy → suggest a person. Skill exits with a delegation suggestion logged.

**Step 3 — Map the process.** Five elements (operator must answer all five):

- Trigger (what kicks it off)
- Data sources (where info comes from)
- Data transformations (how data changes shape)
- Decision points (where it branches)
- Destination (where output goes)

If the operator can't articulate any of the five: *"If you can't explain it to a person, you can't explain it to an AI. Sketch it on paper first, then come back."* Skill stops.

**Step 4 — Pick the autonomy level.**

| Level | Name | What happens |
|---|---|---|
| L0 | Manual | No AI |
| L1 | Suggested | AI suggests, human decides every step |
| L2 | Drafted | AI drafts, human reviews + edits before send |
| L3 | Supervised | AI runs, human validates periodically |
| L4 | Autonomous | AI handles end-to-end |

**Default = lowest level that solves the problem.** Push back on L4 unless the operator has explicitly run lower levels first. *"Workflows beat agents. If a decision doesn't have to be made by AI, don't let AI make it."*

The artifact ships at **bike-method-phase: 1** (training wheels) regardless of the autonomy *level* it's designed for. Phase advances by explicit edit after validation, never automatically.

**Step 5 — Tie to a KPI.** Which Bucket does this move?

- More customers
- More value per customer
- Less cost

Plus a specific metric (response time per cold-call, hot-lead count per week, errors per 100 transcripts, time-to-completion on outreach). **If the operator can't name a Bucket and a metric, skill stops.** *"If your automation doesn't move a number, why are you building it?"*

**Output of Phase 2:** scoped automation spec written to `decisions/log.md` as a dated entry with all five answers + autonomy level + bike-method-phase: 1 + KPI. Durable record of what was decided and why.

Use the dated-header format established in `decisions/log.md`. Title: `{YYYY-MM-DD} — {short title of the automation}`.

### Phase 3 — Machine handoff (build it via WAT)

Ask: *"How do you want to ship this?"* Options ordered by Boring-is-Beautiful default:

1. **Prompt-only** — saved prompt template in `prompts/<name>.md` the operator runs by hand. Zero infrastructure. Highest manual involvement.
2. **Deterministic tool** — Python script in `tools/<name>.py` (no AI step). Best for transformations with clear rules.
3. **AI-assisted tool** — `tools/<name>.py` with one Claude HTTP call inside. Drafts, classifies, summarizes.
4. **n8n workflow** — full SOP in `workflows/<name>.md` + the workflow built in n8n via MCP. Best when integration is needed (Drive trigger, Telegram bot, Notion mutation, scheduled aggregation).
5. **Skill** — `.claude/skills/<name>/SKILL.md` for repeatable interactive tasks the operator wants to invoke from any session.
6. **Sub-agent** — `.claude/agents/<name>.md` multi-step agent. Last resort. Only if work genuinely needs reasoning + tool use across multiple turns.

**Default selected = highest non-AI option that solves the problem.** Operator has to explicitly upgrade to an AI step.

For n8n workflow path, follow CLAUDE.md § "n8n Documentation Access" — use the n8n MCP tools (`get_node_types`, `validate_workflow`, `test_workflow`) before scaffolding.

**Every artifact ships with this header in its YAML frontmatter** (or top-of-file for `.py`):

```yaml
---
autonomy-level: L<n>
bike-method-phase: 1
kpi-bucket: <one of: more-customers | more-value-per-customer | less-cost>
kpi-metric: <specific metric>
shipped-via-level-up: <YYYY-MM-DD>
---
```

For `tools/*.py`, put the same as a top-of-file comment block since Python doesn't parse YAML frontmatter.

This locks every new artifact into Phase 1 of the Bike Method (training wheels — manual validation first). Advancing phase requires an explicit edit to the file, which forces a moment of "have I actually validated this at the lower phase?"

**Surface the Machine principles as you scaffold:**

- **Lego Principle** — smallest steps, zero-AI first if possible.
- **Validation Chain** — for n8n workflows, run `validate_workflow` → `test_workflow` (pin data) → `execute_workflow` (webhook sibling) before talking about activation.
- **Iteration Mindset** — ship the POC, expand from real usage. Don't try to anticipate all edge cases on day one.

If the artifact will mutate live state (real Notion writes, real Telegram sends, paid API backfills), close the run with: *"This artifact's first real run is a halt-before-acting moment per CLAUDE.md. When you trigger it, page yourself via `bash .claude/hooks/notify-telegram.sh halt`."*

If the artifact is recurring, suggest: *"Want to wire this into `/schedule` as a cron routine?"* — but don't auto-create it. `/schedule` is a separate skill, opt-in only.

## Output contract

Every `/level-up` run produces:

1. **One `decisions/log.md` entry** — dated, with all 5 Method answers + autonomy + KPI.
2. **One scaffolded artifact** — prompt, tool, workflow SOP (+ workflow built in n8n if applicable), skill, or agent file. Frontmatter declares level, phase, KPI.
3. **A one-screen close** — what was scoped, what was built, what's the Bike Method Phase 1 next step (e.g. "run it manually 3 times, then advance to phase 2"). One sentence each.

## Critical implementation rules

1. **One interview = one artifact.** No multi-candidate parallel scoping. If the operator wants to scope two, run `/level-up` twice.
2. **Mindset phase always runs first.** Even if the operator comes in with a pre-formed idea — Mindset surfaces *why* it's leverage and what else might be higher-leverage.
3. **EAD enforces "eliminate first."** If the answer is Eliminate, exit cheerfully — that's a win, not a failure. Log it.
4. **Default to the lowest autonomy level that works.** Push back on L4. Require lower-level validation before L4.
5. **Boring-is-Beautiful default in Phase 3.** Default = highest non-AI option that solves the problem. Operator must explicitly choose more autonomy.
6. **Tie-to-KPI is mandatory.** If the operator can't name a Bucket + metric, skill stops. No exceptions.
7. **Bike Method ships into every artifact.** `bike-method-phase: 1` in frontmatter, regardless of designed autonomy level.
8. **Read-only on user files except `decisions/log.md` and the new artifact.** Don't modify `CLAUDE.md`, memory, existing workflows, or other skills as part of a `/level-up` run.
9. **Halt-aware.** If the artifact will mutate live prod state on first real run, close the run by reminding the operator about the halt-before-acting policy.
10. **Use existing primitives.** Before scaffolding new code, scan `tools/` and `workflows/` for prior art. Don't re-invent `tools/notion_session.py` or `tools/generate_pdf.py`.

## Verification (cold-test cases)

- **Eliminate-first test.** Feed an obviously eliminate-able candidate ("I copy a number from one Notion field to another every Monday"). Expected: skill suggests Eliminate (the field can be a formula or relation), exits, logs the win to `decisions/log.md`.
- **L4 push-back test.** Operator asks for autonomous email-replier on first build. Expected: skill insists on L1/L2 first, won't ship L4 without explicit override + acknowledgment that no lower level was tried.
- **Boring-is-Beautiful test.** Candidate solvable with deterministic Python (CSV reformat). Expected: skill recommends `tools/<name>.py` (option 2), not an AI-assisted skill.
- **Bike Method anti-skip.** Operator scaffolds, asks to advance to Phase 4 immediately. Expected: skill makes them confirm they've validated lower phases. Phase only advances by explicit file edit, never automatically.
- **No-KPI exit.** Operator picks a candidate but can't name a Bucket. Expected: skill stops at Step 5 with "name a number this moves or pick a different candidate."
- **Prior-art reuse.** Operator scopes "extract text from a PDF". Expected: skill points at existing `tools/extract_pdf_text.py` instead of scaffolding a new one.
