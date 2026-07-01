---
name: build-hub
description: Use when the operator types /build-hub or asks to "continue the Hub build", "work on Automatisierbar Hub", "build the company OS", or "continue the ClickUp clone". Resumes the long, multi-session build of the Automatisierbar Hub app (a custom ClickUp-class company work OS in the SEPARATE repo automatisierbar-hub) by orienting from that repo's docs/ (STATE → ROADMAP → last session log → DECISIONS), continuing the next milestone's tasks with real verification, then writing state back and auto-committing in the Hub repo at session end. Self-paces across ~32 sessions and flags when a dedicated planning session is needed.
---

You are resuming a large, multi-session software build. The whole point of this skill is
**continuity without quality decay**: you orient from durable on-disk docs every time, do one bounded
chunk well, then write your state back so the next session (with a fresh/compacted context) continues
seamlessly. Never trust in-context memory over the docs.

## Config (single source of truth)

- **HUB_REPO** = `/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub` (the app being built — a
  SEPARATE git repo from this n8n project, which is only the launch pad / where this skill + Telegram
  hook + memory live).
- **Docs** (inside HUB_REPO): `docs/STATE.md` (cursor — read first), `docs/ROADMAP.md` (master plan),
  `docs/DECISIONS.md` (why), `docs/progress/SESSION-NNN-*.md` (journals), `docs/build-log.jsonl`.
- **Telegram hook** (this project): `bash .claude/hooks/notify-telegram.sh checkpoint|halt "<msg>"`.
- **Memory mirror**: `~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/project_automatisierbar_hub.md`.
- Run all git/pnpm commands against the Hub repo with `git -C "$HUB_REPO" …` / `pnpm -C "$HUB_REPO" …`
  (the shell cwd resets between calls — always use absolute paths, don't rely on `cd`).

## 1. Preflight / orientation (ALWAYS first — never skip)

1. Confirm HUB_REPO exists and is the right repo: `git -C "$HUB_REPO" rev-parse --show-toplevel` and a
   quick `git -C "$HUB_REPO" log --oneline -3`.
2. Read **`docs/STATE.md`** in full → then the **active-milestone section** of `docs/ROADMAP.md` →
   then the **latest** `docs/progress/SESSION-*.md` → skim `docs/DECISIONS.md`. This is your context.
3. Verify a **green starting point**: `pnpm -C "$HUB_REPO" install` only if deps changed, then
   `pnpm -C "$HUB_REPO" typecheck`. If STATE claims green but it's red, **the first task is to restore
   green** before any new work (note it in the session log).
4. Announce to the operator, briefly: active milestone, what STATE says is next, and the proposed
   session goal (usually "complete milestone M<n>" or a named sub-chunk). Then proceed autonomously —
   do NOT wait for per-step approval (autonomy default per CLAUDE.md). Only stop for a Halt condition.

## 2. Work loop (bounded: ONE milestone or sub-milestone per session, max)

Follow the `/loop` four-phase cadence, scoped to the chunk:

- **Phase 1 build** — implement the next 1–N tasks from STATE/ROADMAP for the active milestone.
- **Phase 2 bugs/edge-cases** — exercise realistic inputs; fix failure modes.
- **Phase 3 hardening** — error handling, idempotency, types, small refactors.
- **Phase 4 docs** — update in-repo docs/comments for what changed.

Rules while building:
- Reuse the established patterns (service layer → Prisma; `RecordMutationService.apply()`; the shared
  `FilterSpec`; `@hub/ui` tokens; the generic-Record model). Don't invent parallel patterns.
- **Verify with evidence** against the milestone's **Definition of Done** in ROADMAP — typecheck +
  build always; plus tests / running the app / curling endpoints / (M3+) a two-browser realtime check.
  Never mark a checklist item done without the command output proving it.
- After each completed unit, tick its box in `docs/STATE.md`'s checklist (keep STATE live as you go).
- On **milestone completion**, send a Telegram checkpoint:
  `bash .claude/hooks/notify-telegram.sh checkpoint "Hub M<n> complete: <one-line>"`.

## 3. End-of-session protocol (run BEFORE you stop — this is the continuity guarantee)

1. **Rewrite `docs/STATE.md`**: build status (run typecheck to confirm green/red), active milestone +
   %, checklist state, the next 1–3 concrete tasks, open questions, blockers, last-commit + last-session
   pointer, dated.
2. **Write `docs/progress/SESSION-NNN-YYYY-MM-DD.md`** (next N; today's date): goal, done,
   verified-with-evidence, decisions, deferred, next-session pointer.
3. Append any real decisions to `docs/DECISIONS.md`; append one summary line to `docs/build-log.jsonl`.
4. Update the memory file `project_automatisierbar_hub.md` (current-state one-liner) so this project's
   auto-memory stays accurate.
5. **Auto-commit in the Hub repo** (this is pre-authorized for this skill): stage + commit at session
   end and at each milestone completion, conventional message e.g.
   `git -C "$HUB_REPO" add -A && git -C "$HUB_REPO" commit -m "M1: hierarchy + task CRUD (session 003)"`.
   Do **NOT push** (no remote yet / push is a halt-gated step) unless the operator says so.
6. Final Telegram checkpoint with the session summary.
7. **(Track mode only — auto-integrate at MILESTONE completion.)** If `$HUB_TRACK` is set (you were
   launched via `/build-hub-fe|-be|-x`) **and this session completed a full milestone** (its milestone DoD
   is now met, not just one slice), run the integrator after committing:
   `bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/integrate-track.sh" "$HUB_TRACK"`.
   - **Exit 0** → it merged your branch into `main`, gated on typecheck+build+tests, and rebased the other
     *clean* tracks. Note the integration in STATE + the Telegram checkpoint. **Then re-run this milestone's
     LIVE smokes against `main`** (the gate runs unit tests only; live smokes need services up).
   - **Non-zero** → a merge conflict or a red post-merge DoD; `main` was left/rolled back to its last-good
     state. **HALT** to Telegram with the script output + the exact `$BR`↔main conflict, and stop — a
     `/build-hub-integrate` (or manual) session resolves it. Do NOT force it.
   - Mid-milestone slices do **not** integrate (only milestone boundaries do). Disable entirely with
     `HUB_NO_AUTO_INTEGRATE=1` or a `<hub-repo>/.no-auto-integrate` file.

## 4. Halt conditions (call `notify-telegram.sh halt "<reason+exact ask>"`, then stop)

- A task can only progress via a credential / UI-gated / external action: **Authentik provider, DNS
  A-record, VPS SSH, GitHub remote/push, paid API**. Halt with the precise ask.
- About to mutate live/external state (VPS deploy, push, real outbound sends, live Notion) →
  halt-before-acting per CLAUDE.md.
- Same failure 3× despite different fixes, or 2 consecutive units with no measurable progress.
- A task cannot be done within ROADMAP's architecture (drift) → halt and recommend a re-planning session.
- Budget guard: a chunk burns far beyond a normal cycle with no shippable progress → checkpoint + ask.

## 5. Re-planning triggers (recommend the operator run a planning session — EnterPlanMode — don't improvise)

- **Milestone boundary**: at each milestone's end, review the DoD; if reality diverged from ROADMAP,
  update ROADMAP before starting the next milestone.
- **Before any "future phase"** in ROADMAP — **go-live/VPS deploy, GitHub push, Chat, Docs (Yjs),
  time-tracking, dashboards, the Notion migration** — each gets its own plan. Stop and say so.
- **Open-questions threshold**: if `docs/STATE.md` has >5 unresolved open questions, recommend a
  planning session to clear them.
- **Periodic full-app review**: every milestone (~6–8 sessions), re-verify the whole app builds + runs
  end-to-end and the plan still holds; note findings in the session log.

## Guardrails

- One milestone per session — resist scope creep; a smaller, fully-verified, committed chunk beats a
  large half-done one.
- The docs are authoritative. If the code and STATE disagree, reconcile first (quick `git log` +
  typecheck) and fix STATE before building.
- Keep `pnpm -C "$HUB_REPO" typecheck` green at session end, always. Run `pnpm -C "$HUB_REPO"
  db:generate` after any Prisma schema change.
- Never push or deploy without an explicit operator OK (halt-gated).

## Parallel tracks (optional speed-up)

The v2 arc can be built by **several `/build-hub` sessions at once**, each in its own git worktree +
branch + dev DB + ports so they never collide. Don't run plain `/build-hub` in parallel (they'd share the
`main` cursor + tree). Instead use the **track-scoped variants**: **`/build-hub-fe`** (ClickUp parity),
**`/build-hub-be`** (backend spine), **`/build-hub-x`** (isolated leaves). One-time setup:
`bash "$HUB_REPO/infra/setup-tracks.sh"`. The coordination contract (roster, file-ownership, migration
rule, merge protocol) is `automatisierbar-hub/docs/TRACKS.md`. **Integration is automatic:** at each
track's *milestone* completion the session runs `infra/integrate-track.sh <track>` — merge → DoD gate
(typecheck+build+tests) → rebase the other clean tracks; conflict/red rolls back + halts. Force/resolve
manually with `/build-hub-integrate`. Kill-switch: `HUB_NO_AUTO_INTEGRATE=1` or a `.no-auto-integrate` file.

## Pointers

- Master plan: `automatisierbar-hub/docs/ROADMAP.md` · Current cursor: `…/docs/STATE.md`
- Parallel-build contract: `automatisierbar-hub/docs/TRACKS.md` · setup: `infra/setup-tracks.sh`
- Origin architecture plan: `~/.claude/plans/what-i-will-want-frolicking-bonbon.md`
- Repo memory: `project_automatisierbar_hub.md` (this project's memory folder).
