---
name: build-hub-x
description: Use when the operator types /build-hub-x or asks to run the X / isolated-leaf build track. Runs a /build-hub session scoped to the X parallel track — the genuinely-isolated milestones (M3 Cortana chat, then M8 Subdomain inventory) — in the isolated git worktree ../hub-x on branch v2/x with its own dev DB + ports, enforcing the docs/TRACKS.md file-ownership contract (new files + append-only wiring only) so it never collides with the FE or BE tracks running in parallel.
---

You are running the **X build track** — the isolated-leaf lane of the parallel Hub build. This is a
**thin wrapper** over the core `/build-hub` procedure: follow that procedure, scoped to this track's
config, milestones, and (strict) ownership guardrail below. Read `<HUB_REPO>/docs/TRACKS.md` first.

## Track config (X)
- **HUB_REPO (worktree)** = `/Users/sexyjoaquin/Desktop/Claude Code/hub-x` (branch `v2/x`). Run every
  git/pnpm as `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …`.
- **Env:** before any pnpm / prisma / dev command, load the track env:
  `set -a; . "$HUB_REPO/.track.env"; set +a` (→ `DATABASE_URL=hub_dev_x`, api `PORT=3231`, `WEB_PORT=3002`).
- **If the worktree doesn't exist yet:** run
  `bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/setup-tracks.sh"` once, then continue.

## What this track builds
The **isolated leaves**: **M3 (Cortana central chat)** first, then **M8 (Subdomain inventory)** (see
`docs/ROADMAP.md § v2` + `docs/TRACKS.md`; check this worktree's `docs/STATE.md` for the next slice). M3 =
a new `CortanaService` proxying the Cortana loopback (`127.0.0.1:5600`) + a new chat panel. M8 = a new
`SubdomainEntry` table + router + page.

## Ownership guardrail (from TRACKS.md — strict: NEW files + append-only only)
- **You MAY create/edit NEW files only:** `apps/api/src/services/integrations/cortana/*`, a **new**
  `apps/web/src/components/cortana-chat.tsx`, `apps/web/src/app/app/subdomains/*`, an X-owned subdomain
  module, and X's **own new-table** migration (`SubdomainEntry` — a brand-new table). Plus this worktree's `docs/*`.
- **You MUST NOT touch:** FE's `apps/web/src/components/*` (incl. `command-palette.tsx` — **defer the
  Cortana palette entry until after FE merges**; ship M3 as a standalone panel/route first),
  `packages/ui/*`, BE's in-progress services, or any migration that ALTERs a shared table.
- On the **append-only shared api wiring** (`main.ts`, `services/index.ts`, `deps.ts`, `router.ts`) add
  lines only (register the Cortana service / subdomain router); don't reorder — expect a keep-both merge.
- Commit to `v2/x` only. **Never merge to `main`.**

## Procedure
Follow `.claude/skills/build-hub/SKILL.md` fully (preflight → ONE slice → verify against the DoD →
rewrite this worktree's `STATE.md` + a `SESSION-*.md` journal → auto-commit on `v2/x`), applying the
config + guardrail above. Verify green on THIS track (`. "$HUB_REPO/.track.env"` then
`pnpm -C "$HUB_REPO" typecheck && pnpm -C "$HUB_REPO" build` + the slice's smoke). **Halt** on M3's infra
gate: confirm the api can reach the Cortana loopback `127.0.0.1:5600` before wiring the proxy. One slice per session.
