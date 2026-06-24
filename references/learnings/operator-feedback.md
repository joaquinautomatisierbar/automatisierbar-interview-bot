# Operator Feedback (paperclip-visible mirror)

Mirror of operator-side Claude Code memory feedback entries. The operator types a correction or preference once via the `/remember` Claude Code skill; it lands in TWO places:

1. `~/.claude/projects/.../memory/<slug>.md` — session-continuity for Claude Code (this terminal)
2. **This file** — production-mount-feeder for paperclip agents (read on every agent activation)

Append-only. Operator edits are made via `/remember` so both locations stay in sync.

Frontmatter convention: see [INDEX.md](INDEX.md).

---

## lead-icp-backoffice-only

---
name: lead-icp-backoffice-only
description: Filter lead-gen targets to KMUs with real backoffice/paperwork; exclude walk-in retail and trades — they don't have automation pain to sell
type: learning
scope: global
created: 2026-05-09
issue: —
tags: [lead-gen, icp, scraping, sales]
---

Bias lead-gen search terms (Apify Google Maps Scraper, similar) toward SMEs with substantive backoffice work — contracts, billing, case mgmt, client admin — and EXCLUDE walk-in retail / front-of-house trades.

**Why:** Joaquin's offer is automation of office workflows. A Coiffeur or Bäckerei has near-zero backoffice — pitching them wastes call time and pollutes the Lead-DB with low-conversion ICP. Confirmed 2026-05-09: *"they barely have any backoffice, and would just fill our databank with stuff we dont need, instead go for something like immobilien, anwaltskanzelei, etc."*

**Whitelist:** Immobilien, Treuhand, Anwaltskanzlei, Steuerberater, Notar, Buchhaltung, Architekt, Ingenieurbüro, Versicherung, Versicherungsmakler, Vermögensverwaltung, Unternehmensberatung, Personalberatung, IT-Dienstleister, Werbeagentur, Marketingagentur, Webdesign-Agentur, Hausverwaltung, Liegenschaftsverwaltung.

**Blacklist:** Coiffeur, Restaurant, Bäckerei, Apotheke, Optiker, Fitnessstudio, Physiotherapie, Sanitär, Elektriker, Gartenbau.

**How to apply:** Anytime building or editing lead-source filters, search-term lists, ICP definitions, or scoring rules. If user says "broader coverage," add more white-collar categories (Notar, Personalberatung) before considering trades.

---

## no-n8n-bias-pick-best-tool

---
name: no-n8n-bias-pick-best-tool
description: Don't default to n8n for every automation; pick best tool per problem (n8n / trigger.dev / Render / Flask / native scripts)
type: learning
scope: global
created: 2026-05-15
issue: —
tags: [stack-choice, build-pipeline, n8n, trigger.dev, render, flask]
---

Don't auto-default to n8n when scoping a build. n8n is great for visual workflows where a non-developer needs to maintain the automation, but it's the wrong choice for:

- Cron-heavy or long-running background work → trigger.dev (first-class scheduling, retries, queues)
- Heavy Python/Node data transforms → Flask on Render or a worker
- API services with state → Render or Vercel
- One-shot scripts → just a Python file, no orchestrator at all
- Complex AI agents with tool-use loops → Claude Agent SDK or paperclip itself

**Why:** Operator framing 2026-05-15: *"yes as a visual builder n8n over Zapier, but if for the final solution trigger.dev or Render or Flask makes more sense, use them, it doesn't matter whether it's more complex, at the end we need the best product possible."*

**How to apply:**
- When scoping a build for a real customer brief, evaluate stack options on merit, not on "what's easiest in n8n"
- Cite the actual customer constraint (handover-to-non-developer? high-frequency cron? custom Python deps? statefulness?) when justifying the stack pick in PRESENTATION.md
- The interview brief sometimes implies the stack (e.g. "Klient hat schon n8n laufen" → use n8n). When unstated, choose the best fit per the constraints, not the path-of-least-resistance.

---

## telegram-credential-scoping-per-workflow

---
name: telegram-credential-scoping-per-workflow
description: Each Telegram-using n8n workflow has its own bot + cred; never share Interview-Bot cred across workflows
type: learning
scope: global
created: 2026-05-05
issue: —
tags: [n8n, telegram, credentials, webhook]
---

Every Telegram-using n8n workflow must use its OWN bot token + n8n credential. Do not share the Interview-Bot cred across workflows.

**Why:** 2026-05-05 webhook-collision bug — two workflows pointing at the same bot's `getUpdates` queue, second workflow consumed updates intended for the first, traffic silently disappeared. Each bot is a separate Telegram entity, and n8n's Telegram Trigger node hooks each cred to a specific bot's update stream.

**How to apply:**
- New Telegram-using workflow → create a new bot via @BotFather first, then a new n8n credential, then wire that cred specifically to the new workflow.
- Halt-poll uses its own dedicated bot (`OPERATOR_TELEGRAM_BOT_TOKEN`).
- Naming convention in n8n: cred name = workflow name (e.g. "Workflow Interview Bot", "automatisierbar Outreach", "Operator Halt").

---

## paperclip-agent-bootstrap-after-import

---
name: paperclip-agent-bootstrap-after-import
description: Every `paperclipai company import` must be followed by `bootstrap-new-agents.sh` — without the bundled `paperclip` skill, new agents never heartbeat
type: learning
scope: role:operator
created: 2026-05-21
issue: —
tags: [paperclip, bootstrap, heartbeat]
---

`npx paperclipai company import --target existing --collision skip` creates agents in the paperclip DB with their company-specific skills + AGENTS.md, BUT it does NOT auto-wire the paperclipai-bundled skill set (`paperclipai/paperclip/paperclip`, `…/diagnose-why-work-stopped`, `…/para-memory-files`, etc.).

The `paperclipai/paperclip/paperclip` skill contains the actual heartbeat procedure the claude subprocess runs. Without it, `lastHeartbeatAt` stays `null` forever.

**Why:** 2026-05-21 — Presentation Designer, Image Curator, Hook Strategist sat broken for 4 days. Discovered via the `/audit` skill flagging their stuck status.

**How to apply:**
- After ANY `paperclipai company import` (including `--target existing --collision skip`): immediately run `bash tools/paperclip/scripts/bootstrap-new-agents.sh <company-id>` on the VPS as `paperclip` user, from a directory containing `./skills/`.
- The script is idempotent. Re-running on a healthy company is a no-op.
- Verify: `GET /api/companies/<id>/agents` — no agent with `lastHeartbeatAt: null`.

Canonical bundled-skill list: `paperclipai/paperclip/{paperclip, diagnose-why-work-stopped, paperclip-converting-plans-to-tasks, paperclip-create-agent, paperclip-create-plugin, paperclip-dev, para-memory-files, terminal-bench-loop}`.

---

## linkedin-post-tone-no-confrontation

---
name: linkedin-post-tone-no-confrontation
description: LinkedIn original-posts must be friendly + quietly confident, never confrontational / imperative ("Hör auf X")
type: learning
scope: role:copy-writer
created: 2026-05-10
issue: —
tags: [linkedin, content, voice]
---

LinkedIn original posts (Hook + Body + CTA) must stay **friendly + quietly confident**. Never confrontational, never imperative ("Hör auf X", "Mach Y").

**Why:** Joaquin's brand voice is the antithesis of "harsh consultant Twitter." Confrontational framing damages trust signal for the Swiss-German KMU audience. Tested 2026-05-10 — imperative-tone variants got materially worse engagement vs. narrative + question-CTA variants.

**How to apply:**
- Use H1 / H4 / H7 / H9 hook variants from the LinkedIn briefs.
- Downweight H6 / H8 (imperative variants).
- Original-post voice ≠ comment voice. Original posts allow hashtags + automatisierbar mention; comments stay zero-hashtag, conversational.
- Narrative hook → → arrow recipes for the body → question-CTA at the end.

---

## linkedin-post-voice-differs-from-comment-voice

---
name: linkedin-post-voice-differs-from-comment-voice
description: Original-post voice is NOT the same as comment voice — derive from his prior posts (hashtags + automatisierbar mention OK)
type: learning
scope: role:copy-writer
created: 2026-05-04
issue: —
tags: [linkedin, content, voice]
---

`prompts/linkedin_voice.md` codifies the COMMENT voice (engagement bot). It is NOT the voice for original posts.

For original posts, derive the voice from Joaquin's prior LinkedIn posts:
- Hashtags are OK (1-2, on-brand)
- "@automatisierbar" mention is OK
- Narrative hook (first line is a story or observation, not a generic statement)
- → arrow recipes for body structure
- Question CTA at end ("Wie macht ihr das?")

**Why:** 2026-05-04 — early original posts generated from the comment-voice prompt felt stiff and zero-engagement. Pulled archive of his manual posts, identified the divergence, codified.

**How to apply:** When generating an original post (not a comment reply), DO NOT use `prompts/linkedin_voice.md`. Use the original-post voice profile in `prompts/linkedin_brief_synthesis.md` and check against the patterns above.
