---
name: automatisierbar-context
description: >
  Load Automatisierbar's firm context — tech stack, business model, ICP, system connections, halt-policy — before doing any task.
  Use on every heartbeat when wake reason is a Build Issue. Without this context the agent will make wrong stack/scope/safety calls.
---

# Automatisierbar Context

Before you reason about any Build Issue, load these files into context. They are the source of truth for *what Automatisierbar does, how, and with what infrastructure*. The project root is `/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview/`.

## Required reads (every heartbeat)

1. **`CLAUDE.md`** — the firm's operating manual. Pay attention to:
   - The WAT framework (Workflows / Agents / Tools layering)
   - Halt-before-acting policy (when to call `notify-telegram.sh halt`)
   - Autonomy levels (L0–L4) and Bike-Method phases (1–4) in workflow frontmatter
   - n8n MCP capabilities + known gateway blocks (Drive copy_file = 403, etc.)

2. **`references/business-context.md`** — ICP, current goals, team capacity, tech stack trajectory ("n8n-heavy today, Trigger.dev adoption starting"), 6-month targets, constraints. Read before making any *strategic* tradeoff in a Build (e.g. "is this customer in the Treuhand/Immobilien/Anwalt ICP, or are we wasting an automation on a non-fit?").

3. **`connections.md`** — the system map. Every tool the AIOS can reach, the mechanism (mcp / n8n / script / hook), auth model, RW status. Read before planning ANY integration in a Build — if the system isn't in this file, the Build will fail at integration-time.

4. **`references/operator-principles.md`** — Eliminate → Automate → Delegate. The Bike Method. Tying every build to a KPI (more customers / more value per customer / less cost). Read before scoping any new Build to confirm it actually moves a named KPI bucket.

5. **`decisions/log.md`** — past architectural decisions and *why*. Read entries relevant to the current Build's stack choice (e.g. "2026-04-26 — Anthropic API via HTTP Request node, not the dedicated Anthropic node" if you're building anything that calls Claude in n8n).

## Memory layer

The auto-memory at `~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/` contains feedback + project state from prior sessions. Index file: `MEMORY.md`. Skim it for relevant memory entries before assuming a fresh approach is right — past corrections (`feedback_*.md`) bind your behavior.

## Hard rules from CLAUDE.md (do not violate)

- **Halt before:** writing to a live Notion DB with real lead/customer data; activating a workflow that sends real outbound (Telegram, email, Slack); paid-API backfills beyond a sanity-check call; destructive git ops.
- **Lead ICP whitelist:** automations should target backoffice-heavy SMEs (Immobilien / Treuhand / Anwalt / Steuerberater). Coiffeur / Restaurant / Bäckerei / trades are NOT ICP and don't have automation pain — flag if a Build brief targets one.
- **Telegram credentials are per-workflow.** Never share the Workflow Interview Bot cred across new workflows — caused a webhook-collision bug 2026-05-05.
- **n8n Notion getAll: always `simple: false` and `returnAll: true`.** Documented in decisions/log.md 2026-04-26.
- **Anthropic in n8n: use HTTP Request node** with Header Auth, not the dedicated Anthropic node. Established pattern.

## When to call halt

If the Build you're about to ship would:
- Write to the production Cold Call Leads DB or production "Voice Call Agent" workflow with real data → halt
- Send a real Telegram to a non-operator chat ID → halt
- Spend more than one sanity-check API call on paid services → halt
- Activate a workflow that publishes to live (real outbound) → halt

Use: `bash /Users/sexyjoaquin/Desktop/Claude\ Code/n8n\ Workflow\ Interview/.claude/hooks/notify-telegram.sh halt "<reason>"`

The user reads it on Telegram and either replies or doesn't — wait up to 10 min via `bash .claude/hooks/telegram-poll.sh 600`.
