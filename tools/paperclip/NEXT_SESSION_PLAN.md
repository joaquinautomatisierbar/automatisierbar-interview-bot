# Next Session Plan — paperclip Build Pipeline

Last updated: 2026-05-15. Picks up where the rate-limit-pause cut off.

## State at pause (2026-05-15 12:33 CEST)

- paperclip on `:3100`, embedded postgres on `:54329`, healthy. Don't restart.
- 7 agents exist, ALL paused: CEO, Tej, Nico, Patrik (AI-duplicates of the real humans created by CEO during AUT-1 delegation), BuildEngineer, QAEngineer, ProductReviewer.
- 24 issues exist, AUT-1..AUT-23 = CEO/Tej/Nico/Patrik strategic-planning loop (much was theatrical AI-shadow-work, not real ops). AUT-24 = blocked smoke-test for the build pipeline.
- $37.87 burned across 70 runs in the auto-loop. Subscription_included billing (Claude.ai Max abo) — not real $, but real rate-limit consumption.

## Critical user feedback to incorporate (received 2026-05-15 ~12:35 CEST)

1. **No n8n bias.** Build agents currently anchored too hard on n8n MCP. Real customers might need trigger.dev, Render, Flask, plain Python scripts, etc. Pick best tool per problem; quality > complexity-aversion.
2. **Agents need real context.** Currently they get only AGENTS.md instructions + the issue description. They have NO access to: this project folder, `.env` credentials, the broader Automatisierbar tech stack documentation, business-context.md, operator-principles.md, CLAUDE.md, decisions/log.md, existing workflows in `workflows/`.
3. **Use paperclip-shipped skills** rather than reinventing. The skill library is: `paperclip` (heartbeat), `paperclip-create-agent`, `paperclip-create-plugin`, `paperclip-converting-plans-to-tasks`, `paperclip-dev`, `para-memory-files`, `terminal-bench-loop`, `diagnose-why-work-stopped`. Agents can opt-in via `desiredSkills` array on hire.

## Order of operations next session

### Step 0: Decide CEO scope (decision, not implementation)

The AI-Tej/Nico/Patrik duplicates are wasteful — real Tej/Nico/Patrik do this work in real life. Options:

- **A: Delete the AI-Tej/Nico/Patrik agents entirely.** Keep CEO but rewrite its AGENTS.md so it does NOT auto-create agents to handle delegations. CEO orchestrates the build pipeline only; people-tasks get raised as Issues for the operator (Joaquin) to assign.
- **B: Keep them but disable heartbeat + wakeOnDemand.** They're frozen state, can be "consulted" but not auto-run.
- **C: Repurpose them.** Real Tej/Nico/Patrik will eventually integrate as paperclip users (humans with accounts), and these agent-stubs become their AI assistants. Different scope, defer.

**Recommendation: Option A** for now. Cleanest. Reduces the surprise-budget-burn risk.

### Step 1: Audit Automatisierbar's tech stack + credentials available

Read in this order (under ~5 min):

- [.env](../../.env) — what credentials exist (names only, not values when reporting back)
- [references/business-context.md](../../references/business-context.md) — full tech stack, ICP, current goals
- [CLAUDE.md](../../CLAUDE.md) — autonomy rules, MCP capabilities, halt policy
- [connections.md](../../connections.md) — system connection map
- [decisions/log.md](../../decisions/log.md) — past architectural decisions (Flask on Render for interview bot, n8n for cold-call pipeline, etc.)
- `workflows/*.md` — existing SOPs, what's already built

Output: a compact `tools/paperclip/automatisierbar_context.md` that summarizes:
- Tech stack actually in use (Flask + Render, n8n cloud, Notion, Telegram bots, Gmail OAuth, Anthropic API, Gemini API, Apify for scraping, etc.)
- What credentials are in `.env` (names + purpose, no values)
- Naming conventions (workflow folders, Notion DB IDs, etc.)
- Halt-policy + halt-before-acting rules from CLAUDE.md (the agents need to honor these)

### Step 2: Rewrite the 3 agent AGENTS.md files

Each agent gets a richer instructions bundle that includes:

- The agent's role-specific system prompt (current content, edited)
- **No more n8n-first framing.** Replace with: "Pick the best tool per brief. Tool options below. Justify the choice in PRESENTATION.md."
- A list of tool options with one-line "use when" guides: n8n, trigger.dev, Render, Vercel, Flask, plain Python, native shell, etc.
- A reference to `automatisierbar_context.md` (auto-included in bundle)
- A reference to halt-before-acting rules from CLAUDE.md (auto-included in bundle)
- The `desiredSkills` array including: `paperclip` (heartbeat, default), `paperclip-converting-plans-to-tasks`, `para-memory-files` (so agents persist learning), `terminal-bench-loop` (Tester especially)

Use paperclip's `instructionsBundle.files["..."]` to bundle multiple files, not just AGENTS.md. The full file list lives in the agent's instruction dir and the LLM gets them all in context.

### Step 3: Update adapter config for context access

Each agent's `adapterConfig.cwd` should point to a working directory that has access to this project folder. Options:

- **Symlink the project folder into paperclip's workspace:** `ln -s "/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview" ~/.paperclip/instances/default/projects/{company}/{project}/_default/automatisierbar`
- **Set `cwd` to this project folder directly:** less clean but easier
- **Pass relevant files via `instructionsBundle.files`:** ~5-10 key files bundled at hire time. Read-only snapshot but bundled correctly.

Recommendation: combine — bundle the critical context docs (CLAUDE.md, business-context.md, operator-principles.md, automatisierbar_context.md) AND symlink the project folder into the workspace for live read access to `workflows/`, `prompts/`, `references/library/`, etc.

### Step 4: Update hire + re-hire

The existing agents (BuildEngineer, QAEngineer, ProductReviewer) have outdated AGENTS.md. Either:

- Edit them in place via the agent-update endpoint (find via `paperclip-create-agent` skill SKILL.md, step about updating)
- Or delete + re-hire fresh

Probably delete + re-hire — simpler.

### Step 5: Smoke test (resume AUT-24 or new Issue)

After agents are re-hired with proper context, re-trigger AUT-24 or create a fresh smoke-test Issue. Watch the loop. Validate:

- Builder picks a stack that matches the brief (could still be n8n for the Slack-notifier brief — that's appropriate — but the *reasoning* should be in PRESENTATION.md, not assumed)
- Builder references real Automatisierbar context (e.g. mentions our n8n cred conventions if it picks n8n)
- QA actually runs validate/test against the artifact
- Reviewer surfaces Klärungspunkte properly

### Step 6: ONLY THEN — start Phase 3 orchestrator

The orchestrator.js + comment-protocol enforcement is Phase 3 from the original plan. Don't start it until Step 5's smoke test passes.

## Things to NOT do next session

- Don't un-pause CEO + AI-Tej/Nico/Patrik before deciding Step 0 (they'll burn rate-limit on theater).
- Don't create new Issues for the CEO to plan unrelated to build-pipeline work.
- Don't add more agents until Builder/QA/Reviewer flow is proven.
- Don't fetch github.com/paperclipai/paperclip looking for sample companies — the npm distribution has the same skills + templates, just save the fetches.

## Open questions to confirm with user

- **Step 0 decision:** A/B/C for AI-Tej/Nico/Patrik?
- **Credential access:** the agents need `.env` access for things like ANTHROPIC_API_KEY, NOTION_API_KEY, N8N_API_KEY, GMAIL_OAUTH_*, etc. Pass via env vars at agent hire (`adapterConfig.env`), bundle a sanitized `.env.agent` file, or have agents call out to a credential manager? Default recommendation: pass via `adapterConfig.env` per-agent so each agent only gets what it needs.
- **Project folder symlink vs cwd vs bundle:** see Step 3 options.
