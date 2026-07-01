---
name: build-hub-fe
description: Use when the operator types /build-hub-fe or asks to run the FE / frontend / parity build track. Runs a /build-hub session scoped to the FE parallel track — the ClickUp visual-parity arc (M1b→M1g) — in the isolated git worktree ../hub-fe on branch v2/fe with its own dev DB + ports, enforcing the docs/TRACKS.md file-ownership contract so it never collides with the BE or X tracks running in parallel.
---

You are running the **FE build track** — one lane of the parallel Hub build. This is a **thin wrapper**
over the core `/build-hub` procedure: follow that procedure end-to-end, scoped to this track's config,
milestones, and ownership guardrail below. Read `<HUB_REPO>/docs/TRACKS.md` first.

## Track config (FE)
- **HUB_REPO (worktree)** = `/Users/sexyjoaquin/Desktop/Claude Code/hub-fe` (branch `v2/fe`). Run every
  git/pnpm as `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …` (shell cwd resets between calls — use the
  absolute path).
- **Env:** before any pnpm / prisma / dev command, load the track env:
  `set -a; . "$HUB_REPO/.track.env"; set +a` (→ `DATABASE_URL=hub_dev_fe`, api `PORT=3211`, `WEB_PORT=3000`).
- **If the worktree doesn't exist yet:** run
  `bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/setup-tracks.sh"` once, then continue.

## What this track builds
The **ClickUp visual + feature parity** slices: **M1b → M1c → M1d → M1e → M1f → M1g** (see
`docs/ROADMAP.md § v2` + `docs/TRACKS.md`; check this worktree's `docs/STATE.md` for the exact next slice).
Ground truth = `/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview/references/clickup-capture/`
(M1a done). Each slice: read the relevant capture → reshape the matching component + `@hub/ui` tokens →
screenshot the local Hub → visual-diff against the capture → tick DoD.

## Ownership guardrail (from TRACKS.md — fail closed)
- **You MAY edit:** `apps/web/src/components/*`, `packages/ui/*`, `apps/web/src/app/globals.css`, and this
  worktree's `docs/STATE.md` / `docs/progress/*`.
- **You MUST NOT touch:** `apps/api/*` or `packages/db/*` (that's **BE**), or any other track's worktree/
  branch. If a parity fix seems to need an api/schema change, **HALT and flag it for the integrate
  session** — don't cross lanes.
- Commit to `v2/fe` only. **Never merge to `main`** (that's the serial integrate step, run from the main tree).

## Procedure
Follow `.claude/skills/build-hub/SKILL.md` fully (preflight → ONE slice → verify against the DoD →
rewrite this worktree's `STATE.md` + a `SESSION-*.md` journal → auto-commit on `v2/fe`), applying the
config + guardrail above. Verify green on THIS track (`. "$HUB_REPO/.track.env"` then
`pnpm -C "$HUB_REPO" typecheck && pnpm -C "$HUB_REPO" build`; M1 is UI-only, no live DB needed — visual
diffs are the evidence). Halt conditions per the core skill. Do not start a second slice in one session.
