---
name: build-hub-be
description: Use when the operator types /build-hub-be or asks to run the BE / backend build track. Runs a /build-hub session scoped to the BE parallel track — the backend spine (PRE-1 RecordType → PRE-2 NotionService → M2 Leads CRM → M4 → M6 → M5 → M7-backend) — in the isolated git worktree ../hub-be on branch v2/be with its own dev DB + ports, enforcing the docs/TRACKS.md file-ownership contract so it never collides with the FE or X tracks running in parallel.
---

You are running the **BE build track** — one lane of the parallel Hub build. This is a **thin wrapper**
over the core `/build-hub` procedure: follow that procedure end-to-end, scoped to this track's config,
milestones, and ownership guardrail below. Read `<HUB_REPO>/docs/TRACKS.md` first.

## Track config (BE)
- **HUB_REPO (worktree)** = `/Users/sexyjoaquin/Desktop/Claude Code/hub-be` (branch `v2/be`). Run every
  git/pnpm as `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …`.
- **Env:** before any pnpm / prisma / dev command, load the track env:
  `set -a; . "$HUB_REPO/.track.env"; set +a` (→ `DATABASE_URL=hub_dev_be`, api `PORT=3221`, `WEB_PORT=3001`).
- **If the worktree doesn't exist yet:** run
  `bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/setup-tracks.sh"` once, then continue.

## What this track builds
The **backend spine**: **PRE-1 (RecordType generalization) → PRE-2 (NotionService + sync worker) → M2
(Leads CRM) → M4 → M6 → M5 → M7-backend** (see `docs/ROADMAP.md § v2` + `docs/TRACKS.md`; check this
worktree's `docs/STATE.md` for the exact next slice). Port logic from the Flask repo's
`tools/notion_session.py` etc. to TS; reuse `RecordMutationService.apply()` + the `WebhookDispatcher`
worker template. **You are the sole author of migrations that ALTER an existing table.**

## Ownership guardrail (from TRACKS.md — fail closed)
- **You MAY edit:** `apps/api/*`, `packages/db/*`, `packages/shared/*`, **new** web route files
  (`apps/web/src/app/app/{leads,booking,walkin,interview,builds}/*`) and **new** feature components
  (e.g. `apps/web/src/components/lead-slideover.tsx`), plus this worktree's `docs/*`.
- **You MUST NOT edit FE's shared components** — `sidebar.tsx` (append-only nav lines are OK, keep-both),
  `view-switcher.tsx`, `list-workspace.tsx`, `board-view.tsx`, `table-view.tsx`, `calendar-view.tsx`,
  `gantt-view.tsx`, `task-slideover.tsx`, `command-palette.tsx`, `packages/ui/*`. A milestone that needs a
  change there (e.g. M7's FEEDBACK tab) is **deferred until after FE merges**.
- On the **append-only shared api wiring** (`main.ts`, `services/index.ts`, `deps.ts`, `router.ts`) add
  lines only; don't reorder. Commit to `v2/be` only. **Never merge to `main`.**

## Procedure
Follow `.claude/skills/build-hub/SKILL.md` fully (preflight → ONE slice → verify against the DoD →
rewrite this worktree's `STATE.md` + a `SESSION-*.md` journal → auto-commit on `v2/be`), applying the
config + guardrail above. Verify green on THIS track's own DB (`. "$HUB_REPO/.track.env"` then
`pnpm -C "$HUB_REPO" typecheck && pnpm -C "$HUB_REPO" build` + the milestone's smoke). **Halt-before-acting**
on the live gates: first live Notion write (PRE-2/M2/M4), paid Gemini (M4), live Google-Calendar/email
booking (M5) — dry-run first, then page the operator. One slice per session.
