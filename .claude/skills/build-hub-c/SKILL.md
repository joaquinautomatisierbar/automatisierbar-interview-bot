---
name: build-hub-c
description: Use when the operator types /build-hub-c or asks to run the C / chat build track. Runs a /build-hub session scoped to the C parallel track — Hub Chat + SyncUp calls (MC1 Channel/ChatMessage models + service → MC2 ChatGateway /chat namespace → MC3 chat UI (Kanäle/DMs/threads/unread) → MC4 attachments/polish → MC5 SyncUp via Jitsi → optional MC6 Add-Doc-from-chat) — in the isolated git worktree ../hub-c on branch v2/c with its own dev DB + ports, enforcing the docs/TRACKS.md file-ownership contract (X-style: new files + append-only wiring only, own new-table migrations) so it never collides with the FE, BE, X or V tracks running in parallel.
---

You are running the **C build track** — the chat/calls lane of the parallel Hub build. This is a
**thin wrapper** over the core `/build-hub` procedure: follow that procedure, scoped to this track's
config, milestones, and (strict) ownership guardrail below. Read `<HUB_REPO>/docs/TRACKS.md` first.

## Track config (C)
- **HUB_REPO (worktree)** = `/Users/sexyjoaquin/Desktop/Claude Code/hub-c` (branch `v2/c`). Run every
  git/pnpm as `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …` (shell cwd resets between calls — use the
  absolute path).
- **Env:** before any pnpm / prisma / dev command, load the track env:
  `set -a; . "$HUB_REPO/.track.env"; set +a` (→ `DATABASE_URL=hub_dev_c`, api `PORT=3251`, `WEB_PORT=3004`).
- **If the worktree doesn't exist yet:** run
  `TRACKS="c" bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/setup-tracks.sh"` once, then continue.

## What this track builds
**Hub Chat + SyncUp** — a TOP-LEVEL surface: it never depends on the view registry, `list-workspace.tsx`,
or any FE-owned component (see `docs/TRACKS.md § Current assignment` + this worktree's `docs/STATE.md`):
**MC1** chat data model + service + tRPC (new tables `Channel {kind ChannelKind(CHANNEL|DM), spaceId?,
isDefault, …}`, `ChannelMember {@@id([channelId,userId]), lastReadAt, notifyLevel}`, `ChatMessage
{body Json (TipTap), mentions String[], parentId? threads, @@index([channelId, createdAt])}`,
`ChatMessageAttachment` join table; membership-gated send/edit/delete, deterministic DM dedupe,
`markRead`, unread = count createdAt > lastReadAt; mentions → existing NotificationService with
`type:"chat_mention"` — `Notification.type` is a String, NO migration) → **MC2** ChatGateway (NEW file
`services/chat/chat-gateway.ts`: `attachChatGateway(io)` attaches the **`/chat` namespace** to the io
returned at `main.ts` bootstrap; membership-gated `chat:subscribe`, `chat:typing`, unread pushes to
`user:<id>` rooms; delivery = direct emit after persist — single-process api, pg_notify seam documented
for scale-out) → **MC3** chat UI (all new files: `lib/chat/chat-socket-provider.tsx` own client
connection, `components/chat/{channel-list,message-pane,chat-composer,thread-panel,unread-badge,dm-picker}.tsx`,
routes `app/app/chat/*`, ONE appended sidebar nav line; composer reuses the TipTap+mention setup
import-only; virtualized reverse-scroll via `@tanstack/react-virtual`) → **MC4** attachments + polish
(drag-drop presign upload via C's own presign path reusing `MinioStorageService` import-only, inline
image previews, notifyLevel mute, channel create/rename/archive) → **MC5** SyncUp via Jitsi (slice 1
gate-free: `syncup-button/panel.tsx` loading `external_api.js` from `NEXT_PUBLIC_JITSI_BASE_URL`
default meet.jit.si — flag its anonymous-room limits to the operator; room `hub-<channelId>-<nonce>`;
starting a SyncUp posts a join-link ChatMessage) → **MC6 (optional)** "Add Doc" from the composer.
- **v1 scope fence:** NO reactions, message search, pins, or edit-history. DMs are `Channel kind=DM`;
  threads are `parentId` only. SyncUp is capped at 2 slices.
- **Integrate MC1 to main early** at its milestone boundary (small schema substrate lands before V's
  later milestones pile up).

## Ownership guardrail (from TRACKS.md — strict: NEW files + append-only only)
- **You MAY create/edit NEW files only:** `apps/api/src/services/chat/*` (incl. `chat-gateway.ts` — a
  NEW file), `apps/api/src/trpc/routers/chat.router.ts`, `apps/web/src/components/chat/*`,
  `apps/web/src/lib/chat/*`, `apps/web/src/app/app/chat/*`, and C's **own new-table** migrations
  (`Channel`, `ChannelMember`, `ChatMessage`, `ChatMessageAttachment`, enum `ChannelKind`). Plus this
  worktree's `docs/*`.
- **You MUST NOT:** edit `socket-gateway.ts` / `realtime-listener.ts` (import `socket-auth` only);
  ALTER `Comment`/`Attachment`/`Notification` or any existing table (BE-owned); reuse the Comment table
  for chat (`recordId` is a required FK — chat gets its own tables); touch FE components, `packages/ui/*`,
  the view registry, or the `ViewType` enum (V adds `CHAT` there in its MV1 — a chat-as-view-tab via
  `typeConfig.channelId` is a LATER nicety, not MC1-5 scope).
- **schema.prisma discipline:** C's new models go in a delimited `// ── C track models ──` section at
  end-of-file; enum `ChannelKind` is C's own new enum; never reorder existing models.
- On the **append-only shared wiring** (`main.ts` — the `attachChatGateway(io, …)` + emitter-bind lines,
  `services/index.ts`, `deps.ts`, `router.ts`, `sidebar.tsx` — one Chat nav line) add lines only; don't
  reorder — expect a keep-both merge.
- **MC6 PRECONDITION:** V's MV7 (Doc) merged to `main` — verify via `git -C "$HUB_REPO" log --oneline main`
  before starting; absent → skip MC6 and pull forward MC4/MC5 leftovers.
- Jitsi `external_api.js` loads at runtime (script tag / dynamic), never bundled.
- Commit to `v2/c` only. **Never merge to `main` by hand** (integrate-track.sh does it at milestone ends).

## Halt gates (C)
- **MC5 slice 2:** self-hosted Jitsi on the VPS (docker-jitsi-meet at meet.automatisierbar.ch + JWT
  minted from the Hub session via a new `syncup-token.service.ts` + Caddy block) — operator-approved
  VPS work. Slice 1 (meet.jit.si embed) is gate-free but flag its moderator-login/time limits.
- **Two-browser live smokes** (MC2/MC3 DoD) are local-only — no live gate.

## Procedure
Follow `.claude/skills/build-hub/SKILL.md` fully (preflight → ONE slice → verify against the DoD →
rewrite this worktree's `STATE.md` + a `SESSION-*.md` journal → auto-commit on `v2/c` → auto-integrate
at milestone boundaries), applying the config + guardrail above. Verify green on THIS track
(`. "$HUB_REPO/.track.env"` then `pnpm -C "$HUB_REPO" typecheck && pnpm -C "$HUB_REPO" build` + the
slice's smoke — chat slices need a **two-browser live smoke with screenshots**: send/receive/thread/
unread badge clears on focus). One slice per session.
