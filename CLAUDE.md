# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

## n8n Documentation Access

You have access to n8n documentation via the `n8n-mcp` MCP server and 7 installed Claude Code skills (`~/.claude/skills/`). Before building or troubleshooting any n8n workflow, use these resources:

- **MCP tools**: `mcp__n8n-mcp__search_nodes`, `mcp__n8n-mcp__get_node`, `mcp__n8n-mcp__search_templates`, `mcp__n8n-mcp__tools_documentation` for live node/template lookups
- **Skills**: Expression syntax, MCP tool usage, workflow patterns, validation, node configuration, JavaScript/Python code nodes — activated automatically by context
- **Rule**: Never guess node parameters. Use `get_node` to retrieve exact type definitions before writing workflow code.

## Autonomy & Self-Testing

Default to executing tasks end-to-end yourself. Don't pause for user input on things you can do via MCP — testing, debugging, deploying workflow changes, validating outputs, iterating on prompts. Pause only when something is genuinely blocked (gated permissions, credential UIs, third-party policy walls).

**What you can do autonomously:**
- Build, validate, create, update, archive n8n workflows via `mcp__claude_ai_n8n__*`
- Trigger workflow executions via `execute_workflow` (Webhook/manual triggers) or `test_workflow` (pin data smoketest for logic-only validation)
- Read execution results via `get_execution` to verify behavior end-to-end
- Read/search Google Drive (read-only), Notion, Gmail, Calendar
- Create + update Notion pages and databases
- Read live workflow state via `get_workflow_details` before changes

**What's blocked at MCP-gateway level (don't waste tries):**
- Google Drive **mutations**: `copy_file`, file deletes, folder moves return 403. Read/list/metadata work.
- Workflow **activation toggle** in n8n cloud — UI-only, ask user.
- Credential setup in n8n (especially HTTP-Header-Auth like Anthropic API keys) — UI-only, ask user.

**Workaround pattern for Drive-write needs:** Build a Webhook-triggered "test/backfill" workflow inside n8n that does the Drive operation server-side. You can then trigger it via `execute_workflow` (webhook mode) and pass parameters in the body. The Cold Call pipeline already has this pattern: Workflow A (Drive Trigger, prod) + Workflow A2 (Webhook trigger, backfill/test) — A2 is callable from MCP.

**Smoketest hierarchy when iterating:**
1. **`validate_workflow`** — fastest, catches schema/expr errors before save
2. **`test_workflow` with pin data** — verify Code-node logic + IF routing without hitting external services (no real Notion writes, no LLM cost)
3. **`execute_workflow` on a webhook-triggered sibling workflow** — real end-to-end run, real writes
4. **`get_execution(includeData: true, nodeNames: [...])`** — inspect specific node outputs to debug

When you hit a real block, escalate ONCE with the exact action needed (e.g. "set Anthropic Header Auth cred named X"). Don't ping-pong.

## Halt-before-acting policy

The allowlist in `.claude/settings.json` handles tool-level pre-classification, but some halts are semantic (an `update_workflow` against a sandbox vs. the live Cold Call flow looks identical to the harness). Even when the allowlist would let a tool run, pause and call `bash .claude/hooks/notify-telegram.sh halt "<reason>"` before:

- Writing to a live Notion database with real lead/customer data (Cold Call Leads DB, production "Voice Call Agent" workflows). Sandbox/test DBs are fine.
- Activating, publishing, or executing an n8n workflow that sends real outbound messages (Telegram to real chat IDs, emails to real recipients). Pin-data tests and webhook test endpoints don't count.
- Spending paid API credits beyond a single sanity-check call (Anthropic, OpenAI, Brevo). One verification call is fine; a 200-row backfill is not.
- Any destructive git op (force-push, reset --hard, branch -D), even if technically allowlisted.

Cost of a clarifying ping is far lower than the cost of bad data in a production system.

## Business context — load before any strategic recommendation

Full reference: `references/business-context.md`. Single source of truth for what Automatisierbar sells, who the ICP is, current funnel reality, team capacity + time blocks, strategic priors, 6-month targets, and constraints. Read before answering any question that depends on offer/pricing/ICP/funnel/budget/team — your advice is only as good as this file is current. If a fact contradicts the doc, surface it; don't silently override. Doc is reviewed every 2 weeks (see `last_updated` field).

## Business decision support — distilled book library

Full reference: `references/library/INDEX.md` + `.claude/skills/library/SKILL.md` (auto-triggers on offers/pricing/leads/sales/retention/positioning/business-validation decisions). Pulls from distilled Hormozi $100M series + Testing Business Ideas. Cite framework + source when grounding recommendations. Always pair with `references/business-context.md` so framework advice lands on actual numbers, not generic SaaS templates.

## Operator brain — when to build, what autonomy to grant

Full reference: `references/operator-principles.md`. Distilled rules below — apply on every new request.

**Eliminate before you Automate.** When a candidate task surfaces, ask "what happens if we just stop doing this?" *before* asking "how do I automate it." Don't automate waste. If the answer is Eliminate, log it to `decisions/log.md` as a win and move on. EAD is the order: Eliminate → Automate (60/30/10) → Delegate.

**Map the process before you build.** Trigger / Data sources / Transformations / Decision points / Destination. If you can't articulate all five for a workflow you're about to build, stop and ask. Every `workflows/*.md` should make those five elements obvious.

**Default to the lowest autonomy level that solves the problem.** Workflows declare `autonomy-level: L<n>` in frontmatter:

| Level | What happens |
|---|---|
| L0 | Manual, no AI |
| L1 | AI suggests, human decides each step |
| L2 | AI drafts, human reviews + edits before send |
| L3 | AI runs end-to-end, human validates periodically |
| L4 | AI handles end-to-end, no per-event review |

Push autonomy up only after lower levels are validated. Workflows beat agents — if a decision doesn't *have* to be made by AI, don't let AI make it.

**Bike Method phases for rollout.** Workflows also declare `bike-method-phase: <1-4>`:

| Phase | What it means |
|---|---|
| 1 | Training wheels — run manually, watch every output |
| 2 | Guided — runs but every output is reviewed before it ships |
| 3 | Watched — runs autonomously, you sample-monitor + alert on anomalies |
| 4 | Hands-off — full autonomy, dashboard-level monitoring only |

**New workflows scaffold at phase 1 by default**, regardless of designed autonomy level. Phase advances only by explicit edit after validation — never automatically. Even at 90% confidence, roll out 10% of volume first; watch a week; expand.

**Tie every automation to a KPI.** When `/level-up` (or any new build) scopes work, the `decisions/log.md` entry must name a Bucket (more customers / more value per customer / less cost) and a specific metric. If it can't, the automation gets killed before it ships.

**Connection to the halt-before-acting policy above:** halts are the operational expression of the Bike Method. Phase 1/2 workflows that mutate live state should halt-before-acting on their first real run. Phase 3+ workflows have earned autonomous execution — but every newly *designed* workflow starts at Phase 1.

## Paperclip agent budget policy — no auto-loops, no surprise burn

After two incidents (2026-05-15 morning: CEO + AI-Tej/Nico/Patrik burned ~$38 in autonomous strategic planning; 2026-05-15 evening: CEO chat loop burned ~$15 in 1 hour by re-waking on its own comments), the policy for every paperclip agent in this project is:

**Defaults for ALL agents — apply on every hire and check on every audit:**

- `runtimeConfig.heartbeat.enabled: false` — no timer-based wake. Agents only run when explicitly triggered.
- `runtimeConfig.heartbeat.wakeOnDemand: false` — paperclip does NOT auto-wake on comment activity. This prevents the self-loop where an agent's own comment triggers its next run, infinite.
- `runtimeConfig.heartbeat.cooldownSec: ≥60` — if wakeOnDemand ever needs to be true (rare), the cooldown bounds re-fire frequency.
- `runtimeConfig.heartbeat.maxConcurrentRuns: 1` for chat / strategic agents; `2` max for build pipeline agents. Default of 20 is dangerous.

**Explicit triggering mechanisms (use these, NOT auto-wake):**

- `tools/paperclip/telegram_listener.py` triggers CEO on each new Telegram message via `paperclipai heartbeat run --agent-id <ceo>`. One trigger = one run = bounded cost.
- `tools/paperclip/orchestrator.js` (when started via `bash tools/paperclip/launchd/install.sh`) triggers build pipeline transitions on protocol markers + stall detection. It enforces iteration caps (8 Builder↔Test, 3 Builder↔Review) before halting via Telegram.
- `npx paperclipai heartbeat run --agent-id <id>` manual CLI trigger for one-shot wakes.

**Audit rules:**

- Before un-pausing any agent: verify the four `heartbeat.*` settings above. If `wakeOnDemand: true` is set, get explicit user approval first and explain the loop-risk.
- Cost-per-issue cap: if an issue burns > $5 in compute without progressing the user-facing outcome (no SHIP, no new artifact, no answered question), pause the assignee and halt-to-Telegram. Real build work is $5-30 in one cycle; chat replies are $0.05-0.30 each.
- "It was running while I slept" is a red flag, not a feature. Agents should sit idle until something happens that needs them.

**What this trades off:**

The AUT-24 build-pipeline auto-flow (CTO→Engineer→QA→Product→Release) DEPENDED on `wakeOnDemand: true`. With the new defaults, that auto-flow stops working — Engineer doesn't auto-wake when QA posts `READY_FOR_TEST`. Solution: run the orchestrator service which polls + explicitly triggers the next agent. Same end result, controlled fire rate, no loops.

**Bootstrap rule for newly-imported agents (2026-05-21 incident):**

`npx paperclipai company import --target existing --collision skip` does NOT auto-wire the paperclipai-bundled `paperclip` skill onto newly-created agents. Without that skill the agent's `claude` subprocess has no heartbeat procedure to run → `lastHeartbeatAt` stays `null` forever. Symptoms: Presentation Designer, Image Curator, Hook Strategist sat broken for ~4 days because of this.

**After every `paperclipai company import`** (or after manually creating an agent via the API), run:

```bash
# From a dir that has ./skills/ — typically the company source dir on VPS
cd /home/paperclip/automatisierbar-build
bash /home/paperclip/bootstrap-new-agents.sh 47196d38-2f19-4168-af8f-fe9451dff910
```

That script is idempotent: it lists all agents, finds any with `lastHeartbeatAt: null` AND missing `paperclipai/paperclip/paperclip` in their `desiredSkills`, then for each one runs `paperclipai agent local-cli` + PATCHes the 8 paperclipai-bundled skills + flips `wakeOnDemand=true` + fires one heartbeat. Local copy at [tools/paperclip/scripts/bootstrap-new-agents.sh](tools/paperclip/scripts/bootstrap-new-agents.sh). Healthy agents are skipped, so re-running is always safe.

## Operator Telegram notifications

Two notification surfaces available, separate from the leads/interview bot (which stays clean for real conversations):

1. **Auto (Notification hook):** `.claude/hooks/notify-telegram.sh` is wired to the `Notification` hook in `.claude/settings.json`. Fires automatically when I need user attention (permission prompt, idle waiting). User gets pinged on their phone.
2. **Explicit (checkpoint / halt):** I call the same script directly at meaningful moments:
   - `bash .claude/hooks/notify-telegram.sh checkpoint "<summary>"` — milestone in a long run (feature added, bug fixed, validation passed).
   - `bash .claude/hooks/notify-telegram.sh halt "<reason>"` — about to stop on a real blocker.

**One-time setup (user action required):**

1. Create a new bot via @BotFather → copy the bot token.
2. Send any message to the new bot from your personal Telegram so it has a chat to reply to.
3. Run `curl https://api.telegram.org/bot<TOKEN>/getUpdates` and copy your `chat.id` from the response.
4. Add to `.env`:
   ```
   OPERATOR_TELEGRAM_BOT_TOKEN=...
   OPERATOR_TELEGRAM_CHAT_ID=...
   ```

Until those are set, the script silently no-ops — hooks won't fail, just won't ping.

**Reply-during-halt (bidirectional, live session only):**

When you need a yes/no decision from the user mid-/loop, combine the halt notification with the poll script. Halt mode includes a project name + a short random tag like `Q-a8f2c1` in the message and captures Telegram's outbound `message_id`. The poller then accepts a reply only if it matches the halt by **either**:

1. **Reply-threading:** user long-presses the halt message in Telegram → taps **Reply** → types the answer. Telegram sets `reply_to_message.message_id` and the poller filters on it.
2. **Tag prefix:** user types a new plain message starting with the tag, e.g. `Q-a8f2c1 yes`. The poller strips the tag and any separator (`:`, `,`, `.`, space, tab) before capture.

Untagged plain replies are intentionally ignored when a halt is active. This means parallel halts can run without crosstalk *within a single project* — each halt's reply only matches its own poller.

```bash
bash .claude/hooks/notify-telegram.sh halt "Should I write 200 rows to the live Leads DB? Reply yes or no."
reply=$(bash .claude/hooks/telegram-poll.sh 600)  # 10-min timeout
case "$(echo "$reply" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')" in
  yes|y|ok|go|approve|approved) echo "user approved" ;;
  no|n|stop|abort|cancel) echo "user declined"; exit 1 ;;
  *) echo "ambiguous reply: $reply — re-ask or default to safe" ;;
esac
```

Constraints:

- Halts must be **single-question, ideally yes/no**. The poller captures the first matching reply only — "wait... no actually yes" gets recorded as "wait..."
- **Reply has to be threaded or tagged.** A bare "yes" message during an active halt is silently ignored. The halt message includes both options ("Reply directly to this message OR start your reply with Q-…") so the user always has a path.
- Only works while this Claude Code session is open. Closing the laptop kills the poll. For decisions you want to make from anywhere, anytime, defer the action to the next session instead of polling.
- 10-min default timeout. Adjust via `bash .claude/hooks/telegram-poll.sh 1800` for 30 min.
- Exit code 1 from the poller = timeout. Treat as "no answer" — pick a safe default (usually: don't proceed).
- Exit code 2 = `OPERATOR_TELEGRAM_*` env vars missing. Don't poll if you haven't seen a successful checkpoint message arrive — fall back to halting without waiting.

**Cross-project caveat (known limitation):**

Telegram's `getUpdates` API is a destructive queue per bot — once any caller advances the offset, all updates with smaller `update_id` are gone for everyone using that bot token. If two pollers run in different projects (different `.tmp/` dirs, same bot), Project B's poller can advance past a reply intended for Project A before A sees it.

What still works across projects:
- Each halt's filter is correctly scoped to its own message_id and tag, so even if a reply is consumed by the "wrong" project's poller, it won't be falsely captured — that poller will see "no match," advance, and the reply is lost rather than misrouted.
- The user can see *which* project a halt came from via the `[project-name]` prefix in every halt message.

What doesn't:
- Project A's halt will time out instead of getting the user's reply. The user has to retry by re-replying once Project B's poll completes.

If genuine cross-project parallelism becomes a real need, the fix is one of: (a) a single shared offset state file with `flock` across projects, (b) one bot per project, or (c) a centralized dispatcher. None of those are built — flag and revisit if the limitation bites.

**Legacy mode (no halt active):**

Calling `telegram-poll.sh` without a prior `halt` (state files empty) falls back to "any text from the operator chat captures." Use this only for ad-hoc testing — production halt flows should always pair `halt` + `poll`.

## Autonomous /loop pattern

When the user invokes `/loop` (especially dynamic mode without an interval), default to the following behavior so progress is visible without spamming every turn:

**Iteration cadence:**

- **Phase 1 — initial build:** get a working end-to-end version of whatever was requested. Validate with `validate_workflow` + pin-data `test_workflow`. Checkpoint via `bash .claude/hooks/notify-telegram.sh checkpoint "Initial build of X complete and validated"`.
- **Phase 2 — bug fixing & edge cases:** re-run with realistic pin data, identify failure modes, fix them, re-validate. Checkpoint after each meaningful fix.
- **Phase 3 — quality enhancements:** error handling, retries, logging, idempotency, parameter polish. Checkpoint after each meaningful improvement.
- **Phase 4 — documentation:** update the relevant `workflows/*.md` SOP. Checkpoint when done.

**Halt conditions** (call `bash .claude/hooks/notify-telegram.sh halt "<reason>"`, then stop):

- Missing credential or API key — page user with what's needed.
- Same error recurs 3 times despite different fixes — likely needs a human eye.
- Action requires going outside the allowlist (real Notion write, paid-API backfill, prod n8n activation) — confirm before doing.
- Diminishing returns: 2 consecutive iterations produce no measurable improvement.

**Budget defaults** (override per-task if user specifies):

- Wall-clock cap: 4 hours.
- Token cap: ~1M input tokens.
- If approaching either, checkpoint with status and ask whether to continue.

**Self-pacing for /loop dynamic mode:**

- Actively iterating with progress: no sleep, keep going.
- Waiting for a build/test that takes minutes: sleep 270s (stay in cache).
- Idle waiting on user input: sleep 1200–1800s (cache reset is fine, conserves spend).

## Scheduled remote-agent routines (`/schedule`)

`/schedule` creates cron-driven autonomous Claude runs in Anthropic's cloud — no local machine needed, separate billing per run. Use for recurring maintenance the user would otherwise do by hand.

**Candidate routines for this project (user must opt-in to create each):**

1. **Weekly Cold-Call pipeline audit** — every Sunday 02:00 local. Pulls last 7 days of executions for the Voice Call Agent workflows, identifies failed/retriable runs, posts a Telegram summary via the operator hook. Cost: ~1 short Claude run/week.
2. **Lead-DB hygiene check** — every Monday 09:00. Scans Notion Leads DB for entries with missing required fields, stale "in progress" states older than 14 days, or duplicate phone numbers. Posts findings to Telegram. Cost: ~1 short Claude run/week.
3. **Workflow validation drift** — first of each month. Re-runs `validate_workflow` against all Voice Call Agent workflows to catch silent drift after n8n upstream updates. Cost: ~1 short Claude run/month.

To create one: invoke `/schedule` and describe the routine + cron expression. To list/modify: `/schedule list`, update, or delete via the same skill. Don't auto-create routines without explicit user opt-in — each run costs API credits.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
