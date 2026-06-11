---
name: project-reference-context
description: >
  Read-only access to the firm's canonical reference files (CLAUDE.md, business-context,
  Hormozi library, brand guides, decisions log, prompts). Always consult these BEFORE
  making any decision that touches firm conventions, brand voice, customer ICP, or
  operating principles. Without this, agents reason in a vacuum and contradict
  established firm practice.
---

# Project Reference Context

Every Automatisierbar paperclip agent runs with read-only access to a snapshot of the firm's canonical references at `~/_context/`. This is the same body of knowledge Joaquin's Claude Code has via the project's `CLAUDE.md` and `references/` directories.

**You must `ls ~/_context/` and consult the relevant files BEFORE planning anything substantive.** If you skip this and your output contradicts a documented firm rule, that's a fail — you had the file, you didn't read it.

## What's in `~/_context/`

| File | When to consult |
|---|---|
| `CLAUDE.md` | Always — at minimum the WAT framework, halt-before-acting policy, and paperclip agent budget policy sections |
| `references/business-context.md` | Anytime customer/ICP/offer/pricing/funnel decisions are in scope (sales-facing builds, marketing posts, ROI estimates) |
| `references/library/INDEX.md` | Index into the Hormozi library — read this to find which topic file applies |
| `references/library/Leads-and-acquisition.md` | LinkedIn copy, lead-magnet builds, anything with a hook |
| `references/library/Offers-and-pricing.md` | Pricing decisions, value-stack framing, guarantees |
| `references/library/Positioning-and-proof.md` | Avatar/niche/brand positioning, proof assets |
| `references/library/Sales-and-closing.md` | Sales-script builds, objection-handling automations |
| `references/operator-principles.md` | EAD (Eliminate→Automate→Delegate), Bike Method, KPI buckets — ground every new automation here |
| `prompts/linkedin_brief_synthesis.md` | LinkedIn brief author voice + H1-H10 hook library — **Marketing-dept agents must consult** |
| `prompts/linkedin_voice.md` | LinkedIn comment-bot voice (3 fixed Joaquin-cases) — for comment-style outputs |
| `Automatisierbar_Brand_Guide EXTERN copy.pdf` | Brand palette, logo usage, typography — for any visual/presentation artifact |
| `automatisierbar_brandguide_02_prozess copy.pdf` | Process-diagram visual conventions — Presentation Designer must consult |
| `connections.md` | System inventory: what services exist (Notion DBs, n8n workflows, Render services, GitHub repos) |
| `decisions/log.md` | Recent strategic decisions + rationale — check before proposing anything that overlaps |

## How to use

```bash
# Cheap orient
ls ~/_context/
ls ~/_context/references/library/

# Read what's relevant to your task
cat ~/_context/CLAUDE.md | head -200
cat ~/_context/references/business-context.md
```

**For PDF brand guides**, use `pdftotext` (already installed on VPS) or just summarize from the filename + context if the PDF can't be parsed cheaply:

```bash
pdftotext ~/_context/Automatisierbar_Brand_Guide\ EXTERN\ copy.pdf - | head -100
```

If `pdftotext` isn't available, mention this in the comment as a known limitation rather than guessing brand colors.

## Decision-time checks

Before planning or shipping:

- **Touching customer-facing copy / presentation / demo?** Read `references/business-context.md` (ICP, voice tone, no-go words) + `prompts/linkedin_brief_synthesis.md` style rules.
- **Touching live infrastructure / paperclip / n8n / Render?** Read `CLAUDE.md` halt-before-acting + budget policy sections.
- **Designing a marketing post / LinkedIn brief?** Read the Hormozi `Leads-and-acquisition.md` (Hooks Playbook H1-H10).
- **Quoting CHF savings / ROI math?** Read `references/operator-principles.md` (Bike Method ramps, KPI buckets) + check `references/business-context.md` for current hourly rate convention (default CHF 70 unless otherwise noted).
- **About to recommend a stack / tool?** Read `pick-best-stack` skill *and* check `connections.md` to see what's already wired.

## What this skill does NOT do

- It is **not** an editor — `_context/` is read-only at the agent level. If something is wrong, post a comment flagging it and route to CTO; don't try to overwrite the source files.
- It does **not** include real-time state (current Notion lead pages, current n8n executions, current GitHub commits). For live state, use the appropriate MCP tools (`mcp__claude_ai_Notion__*`, `mcp__claude_ai_n8n__*`).
- It is **not** a substitute for the per-issue context (the brief, the comments, the prior agents' handoff markers). Read those first; `_context/` is the firm-wide grounding layer beneath them.

## Failure mode

If `~/_context/` is missing or empty:

- Post a comment: `BLOCKED: ~/_context/ missing — run sync-context.sh on this host`
- Reassign to CTO (CTO can SSH or trigger the sync)
- Do not proceed with planning/building based on guesses about firm conventions
