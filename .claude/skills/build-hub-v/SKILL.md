---
name: build-hub-v
description: Use when the operator types /build-hub-v or asks to run the V / views build track. Runs a /build-hub session scoped to the V parallel track — the remaining ClickUp view & content modes (MV1 view-type substrate + views-lab → MV2 Timeline/Workload/Team/Activity → MV3 registry wiring + add-view menu [gated on FE M1g in main] → MV4 Embeds/Map/Mindmap → MV5 Dashboard → MV6 Form → MV7 Docs → MV8 Whiteboard → optional MV9 Yjs) — in the isolated git worktree ../hub-v on branch v2/v with its own dev DB + ports, enforcing the docs/TRACKS.md file-ownership contract (new files + append-only wiring + the one-shot additive ViewType/SavedView carve-out) so it never collides with the FE, BE, X or C tracks running in parallel.
---

You are running the **V build track** — the views/modes lane of the parallel Hub build. This is a
**thin wrapper** over the core `/build-hub` procedure: follow that procedure, scoped to this track's
config, milestones, and (strict) ownership guardrail below. Read `<HUB_REPO>/docs/TRACKS.md` first.

## Track config (V)
- **HUB_REPO (worktree)** = `/Users/sexyjoaquin/Desktop/Claude Code/hub-v` (branch `v2/v`). Run every
  git/pnpm as `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …` (shell cwd resets between calls — use the
  absolute path).
- **Env:** before any pnpm / prisma / dev command, load the track env:
  `set -a; . "$HUB_REPO/.track.env"; set +a` (→ `DATABASE_URL=hub_dev_v`, api `PORT=3241`, `WEB_PORT=3003`).
- **If the worktree doesn't exist yet:** run
  `TRACKS="v" bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/setup-tracks.sh"` once, then continue.

## What this track builds
The **remaining ClickUp modes** (see `docs/TRACKS.md § Current assignment` + this worktree's
`docs/STATE.md` for the next slice):
**MV1** view-type substrate (one pure-DDL migration: `ALTER TYPE "ViewType" ADD VALUE` ×12 —
`TIMELINE WORKLOAD TEAM ACTIVITY MINDMAP MAP DOC WHITEBOARD FORM DASHBOARD CHAT EMBED` (`CHAT` belongs
to track C's later view-tab; added here so the enum is touched exactly once) + `SavedView.pinned` +
`typeConfig` in view-spec + `packages/shared/src/view-type-configs.ts` + `apps/web/src/lib/view/registry.tsx`
+ `/app/dev/views-lab` harness) → **MV2** Timeline/Workload/Team/Activity views (pure client re-aggregations
over `useViewData`; Activity gets its one missing read surface: `services/activity/` + router) →
**MV3** registry wiring + ClickUp add-view menu (Beliebt/Mehr Ansichten/Einbettungen, Private Ansicht →
`ownerId`, Ansicht anheften → `pinned`) → **MV4** Embeds (`packages/shared/src/embed-providers.ts`
URL normalizers + sandboxed iframe) / Map (`maplibre-gl`, Nominatim + `GeocodeCache` table) / Mindmap
(`@xyflow/react` + `d3-hierarchy`, read-only v1) → **MV5** Dashboard (`recharts`, widgets in
`typeConfig.widgets[]`, aggregate service reusing `ViewSpecCompiler`) → **MV6** Form (builder over
`CustomFieldDefinition`s + `PublicForm` token table + public REST with rate limit/honeypot/body-cap,
records via audited `RecordMutationService.apply()` system actor) → **MV7** Docs (new `Doc` table,
page tree, full-page TipTap reusing the existing editor+mention config; last-write-wins + presence
warning — NO Yjs) → **MV8** Whiteboard (`@excalidraw/excalidraw` — MIT; tldraw rejected:
watermark/paid license) → **MV9 (optional)** Yjs co-editing via Hocuspocus.
- **Integrate MV1 to main immediately** at its milestone boundary (small schema substrate — siblings
  rebase onto the enum before further migrations pile up).

## Ownership guardrail (from TRACKS.md — strict: NEW files + append-only + one announced carve-out)
- **You MAY create/edit NEW files only:** `apps/web/src/components/{views,dashboard,forms,docs,whiteboard}/*`,
  `apps/web/src/lib/view/registry.tsx` + new `apps/web/src/lib/{dashboard,map,embed,doc}/*`,
  `apps/web/src/app/app/{dev/views-lab,docs,whiteboards}/*`, `apps/web/src/app/form/*`,
  `apps/api/src/services/{activity,dashboards,forms,geo,docs,whiteboards}/*` + their routers, V's **own
  new-table** migrations (`Doc`, `Whiteboard`, `PublicForm`, `GeocodeCache`). Plus this worktree's `docs/*`.
- **One-shot additive carve-out (MV1 only, DECISIONS-announced):** the `ViewType ADD VALUE` migration +
  `SavedView.pinned` + append-only lines in `packages/shared/src/enums.ts` (`VIEW_TYPES`),
  `view-spec.ts` (the single `typeConfig` line), shared `index.ts`, and the `VIEW_TYPE` literal in
  `apps/api/src/trpc/routers/saved-view.router.ts` → `z.enum(VIEW_TYPES)`. **NO other ALTER of an
  existing table — those are BE's** (e.g. a first-class LOCATION custom-field type → DECISIONS handoff).
- **MV3 PRECONDITION:** verify FE's M1g parity merge is in `main`
  (`git -C "$HUB_REPO" log --oneline main | head -20`, look for the M1g/FE integration merge) BEFORE
  touching `list-workspace.tsx` / `view-switcher.tsx`. Absent → build MV4's registry-independent halves
  instead (embed normalizers, geocode service, map/mindmap components in views-lab). At the M1g
  boundary, `list-workspace.tsx` + `view-switcher.tsx` transfer FE→V and `services/views/*` +
  `saved-view.router.ts` transfer BE→V (re-confirm in TRACKS.md at transfer). **Pre-MV3, every renderer
  ships to `/app/dev/views-lab` only.**
- **schema.prisma discipline:** V's new models go in a delimited `// ── V track models ──` section at
  end-of-file; enum edits append lines inside the enum block only; never reorder existing models.
- On the **append-only shared wiring** (`main.ts`, `services/index.ts`, `deps.ts`, `router.ts`,
  `sidebar.tsx`) add lines only; don't reorder — expect a keep-both merge.
- **Heavy libs** (`maplibre-gl`, `@xyflow/react`, `recharts`, `@excalidraw/excalidraw`) ALWAYS behind
  `next/dynamic` `ssr:false` (precedent: CalendarView/GanttView in `list-workspace.tsx`); MV4/MV5/MV8
  DoDs include a `next build` route-size check proving they're not in shared chunks.
- Commit to `v2/v` only. **Never merge to `main` by hand** (integrate-track.sh does it at milestone ends).

## Halt gates (V)
- **MV6 live exposure:** anything that exposes `/form/*` + `/api/v1/public/*` on os.automatisierbar.ch
  (Caddy/Authentik bypass, middleware exclusion on the VPS, flipping a real form `enabled=true`) —
  dev-prove with curl smokes first, then halt to the operator with the exact Caddy/middleware diff.
- **MV9 (optional):** Hocuspocus process + Caddy WS route on the VPS.
- **Soft note (not a halt):** first Nominatim geocode call — free read-only API; confirm 1 req/s
  throttle + proper User-Agent in the session log (usage-policy compliance).

## Procedure
Follow `.claude/skills/build-hub/SKILL.md` fully (preflight → ONE slice → verify against the DoD →
rewrite this worktree's `STATE.md` + a `SESSION-*.md` journal → auto-commit on `v2/v` → auto-integrate
at milestone boundaries), applying the config + guardrail above. Verify green on THIS track
(`. "$HUB_REPO/.track.env"` then `pnpm -C "$HUB_REPO" typecheck && pnpm -C "$HUB_REPO" build` + the
slice's smoke script + screenshots for UI slices — views-lab pre-MV3). One slice per session.
