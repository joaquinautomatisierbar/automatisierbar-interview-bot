---
name: audit
description: Use when the user asks for an AIOS audit, asks to score the setup, says "is my AIOS working", "audit my setup", "find gaps in my AIOS", or wants to check structural health. Produces a Four-Cs scoreboard (Context / Connections / Capabilities / Cadence) with leverage-weighted top-3 fixes. Read-only by default. Re-run weekly to watch the score climb.
---

## What this skill does

Runs a **Four-Cs structural audit** on this project. Reads (never writes by default) the project's operating manual, memory, skills, hooks, connections, decisions, and references. Scores each of the Four Cs out of 25 (= 100 total). Surfaces strengths and the top-3 leverage-weighted gaps with concrete next-step commands tied to *our* tooling (n8n MCP, Telegram halt-poll, /loop, /schedule).

**Scope is structural — "is the AIOS built right?"** It is NOT a capability planner. Capability gaps ("you could build a daily brief if you wired Calendar write") belong to `/level-up`. The audit answers: are the files, registries, hooks, and connections in good shape?

First run is the baseline. Re-run weekly. Watching the score climb is the compounding hook.

> Adapted from the Four-Cs framing in Nate Herk's AIS-OS. Calibrated here to our WAT-framework + n8n + Telegram-halt setup.

## Today's context

- **Date:** !`date +%Y-%m-%d`
- **Project root:** the current working directory
- **Memory dir:** `~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/`

## The Four Cs (25 each = 100 total)

| Layer | Test |
|---|---|
| **Context** | Knows the operator + business — `CLAUDE.md`, memory, decisions, references |
| **Connections** | Reaches the operator's stuff — `connections.md`, MCPs, n8n credentials, .env keys, hooks |
| **Capabilities** | Knows how to do work — skills (`.claude/skills/`), workflows (`workflows/`), tools (`tools/`) |
| **Cadence** | Runs without being asked — `.claude/settings.json` hooks, `/schedule` routines, recurring `/loop` patterns |

## Execution

### Step 1: Discover the project shape (parallel reads)

Look for **patterns and intent**, not exact paths. Use `Read` / `Bash ls` / `Bash find` in parallel:

**Operating manual:** `CLAUDE.md` (root) — read fully, count words, scan for sections.

**Memory:** `~/.claude/projects/-Users-sexyjoaquin-*/memory/MEMORY.md` + sibling `*.md` files. Count entries.

**Skills (project-local):** `.claude/skills/*/SKILL.md` — count, read frontmatter.
**Skills (user-global):** `~/.claude/skills/*/SKILL.md` — count separately, do NOT include in capability score (this is a *project* audit).

**Workflows (this project's primary capability surface):** `workflows/*.md` — count + read frontmatter for `autonomy-level` and `bike-method-phase`.

**Tools:** `tools/*.py` (or `.js` / `.sh`) — count.

**Connection mechanisms — any of these counts as "reachable":**
- MCPs: `.mcp.json` (project) and `mcpServers` key in any `~/.claude/settings*.json`
- n8n credentials referenced in `workflows/*.md` (Notion, Drive, Anthropic, Telegram, SMTP, Gemini)
- Scripts in `tools/` documented in CLAUDE.md or workflow SOPs
- API keys in `.env` paired with a reference guide (`prompts/<tool>-*.md`, `references/<tool>-*.md`, or memory file)
- Hooks in `.claude/hooks/` (e.g. Telegram operator-notify)

**Connections registry:** `connections.md` (root). Read it — penalize if missing rows for reachable tools.

**Reference guides:** `references/*.md`, `prompts/*.md`, plus memory files prefixed `reference_*.md`.

**Decisions log:** `decisions/log.md` (root). Count entries dated within the last 90 days.

**Learning system** (added 2026-06-01 — the paperclip memory loop):
- `references/learnings/INDEX.md` — count entries across `global.md` + `operator-feedback.md` + `by-role/*.md`. Each entry starts with `## <slug>` H2 inside one of these files.
- `references/retros/` — count files matching `AUT-*.md` (excluding `INDEX.md`).
- Roughly count Issues shipped in last 30 days via paperclip API: `curl http://127.0.0.1:3100/api/companies/47196d38-2f19-4168-af8f-fe9451dff910/issues` → filter `status in ("done","in_review")` AND `updatedAt within last 30 days`. If the API is unreachable, skip — operator runs `/audit` from MacBook and the API may not be tunneled.

**Hooks / scheduled jobs:** `.claude/settings.json` `hooks` key. Look for `Notification`, `PreToolUse`, `Stop` — any of these = recurring trigger active.

**Recurring patterns documented in CLAUDE.md:** sections about `/schedule` cron routines, `/loop` autonomous mode, weekly rituals.

**Templates / scaffolds:** `templates/`, `.claude/templates/`, or canonical example files referenced by skills.

Don't penalize for non-canonical names if the *intent* is captured elsewhere.

### Step 2: Score each C (25 points each)

#### Context (25 pts)

| Criterion | Points | How to detect |
|---|---|---|
| `CLAUDE.md` exists, substantive (>2000 words, multi-section) | 5 | Read + count |
| Identity / role / voice / persona captured (operator brain, halt policy, autonomy expectations) | 5 | Sections like "Halt-before-acting", "Autonomy & Self-Testing", "Operator brain" — at least 2 such sections |
| Persistent memory exists with multiple entries | 5 | `MEMORY.md` index has ≥3 entries OR memory dir has ≥3 `.md` files |
| Reference guides + learnings exist | 5 | (a) `references/` or `prompts/` or memory `reference_*.md` count ≥2 → up to 3 pts; AND (b) `references/learnings/` exists with ≥1 entry across `global.md` / `operator-feedback.md` / `by-role/*.md` → up to 2 pts. If learnings dir is empty, hard cap at 3. |
| Decisions log has ≥3 entries within 90 days | 5 | `decisions/log.md` exists + count entries by `^## YYYY-` headers |

#### Connections (25 pts) — domain-aware, mechanism-agnostic

A "reachable" connection counts via ANY mechanism: MCP, n8n credential, script, hook, or `.env` key + reference guide.

**The 7 Tier-1 Universal Data Domains:**

| # | Domain | Examples for this project |
|---|---|---|
| 1 | Revenue / Financials | Stripe, QuickBooks, Skool, GoHighLevel |
| 2 | Customer interactions | Notion (Lead-DB, Call Analytics, LinkedIn Activity), Telegram bots, HubSpot |
| 3 | Calendar | Google Cal, Outlook, Calendly |
| 4 | Communication | Gmail, SMTP, Slack/Teams, Telegram operator-notify |
| 5 | Project / task tracking | Notion, n8n Cloud, ClickUp, Linear |
| 6 | Meeting intelligence | Granola, Otter, Fireflies, audio→Gemini transcription pipeline |
| 7 | Knowledge / files | Drive, local repo, auto-memory, Notion |

**Tier-2 (bonus):** AI service API keys (Anthropic, OpenAI, Gemini), decisions log, content/publishing surfaces.

| Criterion | Points | How to detect |
|---|---|---|
| Tier-1 domain coverage | 10 | 1.4 pts per tier-1 domain reachable. Round to nearest 0.5. Cap 10. |
| `connections.md` exists + accurate | 5 | 0 if missing. 2 if exists but stale/sparse. 5 if covers all reachable tools with mechanism + RW + last-checked. |
| Reference guides for connected tools | 5 | -1 per connected tool with no reference doc anywhere (memory, references/, prompts/). Floor 0. |
| At least one connection can WRITE (mutate external state) | 3 | n8n workflows that mutate Notion/Drive/Telegram, OR hooks that post Telegram. 0 if entirely read-only. |
| Auth / freshness — no stale `last checked` >30 days for active prod connections | 2 | Check `connections.md` `Last checked` column. -1 per stale row. Floor 0. |

#### Capabilities (25 pts)

| Criterion | Points | How to detect |
|---|---|---|
| ≥3 project skills installed (`.claude/skills/*/SKILL.md`) | 5 | Count |
| ≥1 user-built skill (not canonical onboard/audit/level-up) | 5 | Count skills NOT in `[onboard, audit, level-up, skill-creator, skill-builder, decision]` |
| ≥3 workflows in `workflows/*.md` (the primary capability surface in WAT) | 5 | Count |
| ≥3 tools in `tools/*.py` (deterministic execution layer) | 5 | Count |
| Workflows declare `autonomy-level` + `bike-method-phase` in frontmatter | 5 | -1 per workflow missing either field. Floor 0. |

#### Cadence (25 pts)

| Criterion | Points | How to detect |
|---|---|---|
| Hooks active in `.claude/settings.json` (Notification, PreToolUse, Stop, etc.) | 5 | At least one hook key with non-empty array |
| Telegram operator-notify wired (halt + checkpoint surface) | 5 | `.claude/hooks/notify-telegram.sh` + `telegram-poll.sh` exist + `OPERATOR_TELEGRAM_*` referenced in CLAUDE.md |
| Recurring trigger documented OR scheduled — `/schedule` cron routine OR n8n schedule-triggered workflow OR weekly ritual in CLAUDE.md | 5 | Schedule-trigger node in any `workflows/*.md`, `/schedule` section in CLAUDE.md, or active CronList entries |
| Recent activity / usage signal | 5 | Files in `workflows/` or `.claude/skills/` modified within 30 days OR `decisions/log.md` entry within 30 days |
| Retro coverage — paperclip is actually learning per shipped Issue | 5 | Count files in `references/retros/` matching `AUT-*.md` (exclude INDEX.md) → `R`. Count Issues shipped in last 30 days from paperclip API (status `done` or `in_review`, updatedAt within 30d) → `S`. Score: 0 if `S>0` and `R==0`; 2 if `R/S < 0.3`; 4 if `R/S < 0.7`; 5 if `R/S ≥ 0.7`. If API unreachable, just check `R ≥ 1` → 3 pts, `R ≥ 5` → 5 pts. |
| Company-state snapshot fresh + populated | 5 | (a) Each of `references/company-state/{founder-syncs,active-clients,this-week,team-capacity}.md` exists → 1 pt each (max 4). (b) Each file's `last_refreshed:` frontmatter is within 36h → bonus 1 pt if all 4 are fresh, -1 per stale file capped at -3. Floor 0. Cap 5. If the entire directory is missing, score 0 + flag "snapshot puller never ran — install via `bash tools/paperclip/scripts/sync-company-state.sh`". |

### Step 3: Identify top-3 gaps by leverage

For each criterion that lost points: **leverage = (points lost) × (impact multiplier).**

**Impact multipliers (calibrated to this project):**

- 0 tier-1 domains reachable: **4x** (AIOS is blind)
- ≤2 tier-1 domains reachable: **3x**
- `CLAUDE.md` missing or thin (<2000 words): **3x**
- 0 workflows declare autonomy-level / bike-method-phase: **2.5x** (every workflow is implicitly L4 — risky)
- Telegram operator-notify NOT wired: **2.5x** (no halt surface = no safe autonomy)
- 0 user-built skills: **2x**
- No recurring trigger anywhere: **2x**
- All connections read-only: **2x** (viewer, not an OS)
- No `decisions/log.md` OR no entries within 90 days: **1.5x**
- No reference guides for connected tools: **1.5x**
- All others: **1x**

Sort gaps by leverage descending. Take top 3. For each, write a one-line concrete next step using *our* tooling:

- **Need a new skill?** "Write `.claude/skills/<name>/SKILL.md` with YAML frontmatter (name, description). Or invoke `skill-creator` from user-global skills."
- **Need to log a decision?** "Append to `decisions/log.md` using the dated-header format."
- **Need to reach a tier-1 domain?** Prefer `n8n` workflow if write-capable, else `script` in `tools/<name>.py` + `references/<tool>-api.md`. MCP only if no API path exists.
- **Connected tool missing a reference guide?** "Save endpoints + auth + common queries to `references/<tool>-api.md` next time you touch that API."
- **Workflow missing autonomy/bike-method frontmatter?** "Add `autonomy-level: L<n>` and `bike-method-phase: <n>` YAML frontmatter at the top of each `workflows/*.md`."
- **Need a recurring trigger?** "Either add a Schedule trigger to an n8n workflow, or invoke `/schedule` to spin up a cloud cron routine."
- **No halt surface?** "Wire `.claude/hooks/notify-telegram.sh` per CLAUDE.md § Operator Telegram notifications + add `OPERATOR_TELEGRAM_*` to `.env`."

### Step 4: Output the report

Print directly in chat. Markdown. Format:

```
# AIOS Audit — {date}
**Score: {total}/100** ({stage})

Stage thresholds:
- 0-39  → Stage 0: Foundation
- 40-69 → Stage 1: Built
- 70-89 → Stage 2: Compounding
- 90-100→ Stage 3: Autonomous

## Scoreboard

Context        {bar}  {n}/25  {label}
Connections    {bar}  {n}/25  {label}
Capabilities   {bar}  {n}/25  {label}
Cadence        {bar}  {n}/25  {label}

(bar = ## per 5pts; label: "Strong" ≥20, "Solid" 15-19, "Thin" 8-14, "Missing" <8)

## Strengths
- {1-3 short bullets from highest-scoring criteria}

## Top 3 Gaps (ranked by leverage)
1. **{gap name}** (-{points lost} × {multiplier})
   → {concrete next-step}
2. **{gap name}** (-{points lost} × {multiplier})
   → {concrete next-step}
3. **{gap name}** (-{points lost} × {multiplier})
   → {concrete next-step}

## Suggested next: {single most leveraged action — usually #1 above}

## Learning Loop Health (added 2026-06-01)

Paperclip memory loop — surfaces whether the system is actually getting smarter per shipped Issue.

- **Learning density:** {N entries across `references/learnings/global.md` + `operator-feedback.md` + `by-role/*.md`}
- **Retro coverage:** {R retros in `references/retros/`} / {S Issues shipped last 30d} = {ratio}
- **Operator feedback freshness:** last entry in `operator-feedback.md` was {N days ago} — flag if >14d AND any agent run happened in that window
- **Pending pulls:** {P} RETRO comments on Issues without corresponding files in `references/retros/`
- **Company state freshness:** founder-syncs.md = {Xh old}, active-clients.md = {Yh old}, this-week.md = {Zh old}, team-capacity.md = {Wh old}. Flag if any >36h with "→ run `bash tools/paperclip/scripts/sync-company-state.sh` or check `systemctl status sync-company-state.timer` on VPS".

If ratio < 0.7 AND Issues are shipping: run `bash tools/paperclip/scripts/pull-retros.sh` to pull retros + commit. If still low after pull, the `write-retro` skill on Release Engineer may be skipping — check a recent Issue's comments for the `RETRO:` marker.
If operator-feedback hasn't been touched in 14+ days: surface as a gap — operator is correcting agents in this Claude Code session but not running `/remember` to propagate, so future agents will repeat the same mistakes.

---
Structural gaps only. To explore CAPABILITY gaps (what your AIOS could DO that it can't yet), run /level-up after this audit.
```

### Step 5: Offer to save the report

After printing, ask: *"Save this audit to `audits/audit-{date}.md` so you can track score over time?"*

If yes: write the file (creating `audits/` if needed). This is the **only** writable side effect of the skill.

## Critical rules

1. **Read-only by default.** Never modify `CLAUDE.md`, memory, skills, workflows, or any project file. Only optional write is the saved audit report.
2. **Be honest, not generous.** A 95/100 is a flex. Most setups land 50–75. If everything scores Strong, recheck the criteria — you're rounding up.
3. **Don't suggest skills that don't exist.** Point at what's actually available locally or in `~/.claude/skills/`.
4. **Speed matters.** Report in under 60 seconds wall-clock. Read targeted files, count via `find` / `ls`, only read frontmatter for skill/workflow inventory.
5. **Be flexible about file names.** Don't penalize for non-canonical names if the intent is captured (e.g. `prompts/transcript_classification.md` counts as a reference guide).
6. **Cadence detection is fuzzy.** Infer from skill names, n8n schedule triggers, and CronList output if available.
7. **Tier-2 connections are bonus, not required.** Weighting is on Tier-1 (the 7 universal domains).

## Verification (cold-test cases)

- **Fresh-clone test:** project has only CLAUDE.md + .claude/settings.json + this audit skill. Expected score: ~25–35. Top gap should be "no connections.md" or "no workflows."
- **Stale-connections test:** `connections.md` exists but every `Last checked` is >60 days old. Expected: -2 on freshness criterion, freshness flagged in top-3.
- **Frontmatter-missing test:** workflows exist but none declare `autonomy-level`. Expected: -5 on Capabilities, "add frontmatter" in top-3 with 2.5x multiplier.
- **Halt-surface-missing test:** `.claude/hooks/notify-telegram.sh` doesn't exist. Expected: -5 on Cadence, ranked top-3 with 2.5x multiplier.
