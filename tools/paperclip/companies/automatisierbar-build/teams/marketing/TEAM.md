---
name: Marketing
description: PR Director's team that converts weekly content briefs into rated LinkedIn post variants with image suggestions.
manager: pr-director
members:
  - copy-writer
  - hook-strategist
  - image-curator
---

## Mandate

Take each weekly LinkedIn content brief (Friday 16:00, produced by `tools/linkedin_brief.py`) and produce 5-7 rated post variants in the "LinkedIn Post Variants" Notion DB.

Each variant carries:

- Body (≤1300 chars, Hochdeutsch, Du-Form, hook-first, ≥1 concrete number)
- Rating 1-10 (Hook Strategist's score)
- Hook Type (H1-H10 from the Hormozi Hooks Playbook)
- Image Suggestion (auto-svg spec OR existing-asset path)
- Effect Goal (trust-build / lead-warm / brand-grow / proof)

## Workflow per brief

1. **PR Director** reads the brief, expands 2-3 angles to 5-7 variant specs, delegates work.
2. **Copy Writer** drafts post bodies per spec (one heartbeat per variant or batched 2-3).
3. **Hook Strategist** scores ALL drafts in one batch (rating + breakdown + improvement note).
4. **Image Curator** suggests 1-2 images per draft in one batch.
5. **PR Director** assembles + writes Notion rows + marks Issue done.
6. "Marketing Brief Ready" n8n workflow fires Telegram ping to operator.

## Constraints

- All 4 agents have `wakeOnDemand=false` + `cooldownSec=60` + `maxConcurrentRuns=1` (per `CLAUDE.md` budget policy).
- Per-week cost cap across team: CHF 3.
- Per-issue iteration cap: 2 loops with Copy Writer + Hook Strategist combined.
- Voice rules locked in `hormozi-copy-skills` SKILL.md — no buzzwords, no tool names in prose, no FTE framing.

## Phase 1 (current — Joaquin only)

- Validation period: 2-3 Fridays
- Success criteria: ≥2/7 variants per week publishable without major rewrite, cost <CHF 3/week
- Decisions logged in `decisions/log.md` each Friday

## Phase 2 (after Joaquin validation — multi-person)

- Per-person Notion DBs created for Nico/Tej/Patrik
- `linkedin_brief.py` parameterized with `--person` flag
- Per-person `prompts/linkedin_brief_synthesis.<person>.md` voice variants
- Setup CLI `tools/setup_personal_brief.py` for each person to bootstrap locally
