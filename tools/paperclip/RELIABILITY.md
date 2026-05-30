# Paperclip Pipeline — Reliability Runbook

The contract for what auto-recovers vs. what pages the operator. `preflight.js` enforces the
pre-dispatch checks; `orchestrator.js` enforces the in-flight ones. Both read
[`pipeline.config.json`](pipeline.config.json). Observe live state with `node pipeline_status.js`.

**Invariant:** every build issue must end in a *notified terminal state* — `done` (with location)
or `blocked` (with a categorized reason). No silent limbo.

---

## Health model — what "green" means before a build is dispatched

1. `GET /api/health` → `status: ok`, `authReady: true`.
2. systemd: `paperclip`, `paperclip-orchestrator` **active**; `paperclip-watchdog.timer` **active**.
   (`paperclip-listener` is *not* required — the dispatcher is the primary trigger, per operator decision 2026-05-29.)
3. Auth: `CLAUDE_CODE_OAUTH_TOKEN` present and **`ANTHROPIC_API_KEY` absent** (Max abo only — console
   pay-as-you-go burns the $100 budget in days; see CLAUDE.md budget policy).
4. Postgres: `dynamic_shared_memory_type = sysv` (POSIX `/dev/shm` files get silently cleaned → 503).
5. Every pipeline agent (resolved by `urlKey`): exists, not `paused`, not `error`, `lastHeartbeatAt != null`.
6. Build-class agents have `heartbeat.wakeOnDemand = true` + `cooldownSec = 60` (else handoffs don't fire
   on marker comments — see Failure #1).

---

## Failure taxonomy → recovery matrix

| # | Class | Symptom / detection signal | Policy | Enforced by |
|---|---|---|---|---|
| 1 | **wakeOnDemand regression** | build agents have `wakeOnDemand` unset → handoff marker comment doesn't wake the next agent; pipeline only advances on the orchestrator's 120s nudge | **Auto-fix:** PATCH `heartbeat.{wakeOnDemand:true,cooldownSec:60}` | preflight `--fix` |
| 2 | **Unbootstrapped agent** | `lastHeartbeatAt: null` + missing `paperclip` skill → agent never runs | **Auto-fix:** run `scripts/bootstrap-new-agents.sh`; **block dispatch** until green | preflight |
| 3 | **Paused / error agent** | `pausedAt` set or `status: error` | **Auto-recover:** `POST /api/agents/{id}/resume`; if still bad, **halt** | preflight + orchestrator |
| 4 | **Agent/company-ID drift** | tool can't resolve a `urlKey`, or orchestrator points at a dead company | **Halt** + reconcile to `pipeline.config.json` (tools resolve by `urlKey`, never hardcoded UUID) | preflight |
| 5 | **Postgres /dev/shm death** | `/api/health` → 503 `database_unreachable` | **Auto-recover:** watchdog restarts paperclip after 2 failed checks | watchdog timer |
| 6 | **Auth / no credit** | run `failed`, "Credit balance too low" / `authReady:false` | **Halt** (never add `ANTHROPIC_API_KEY`); preflight validates token | preflight |
| 7 | **Post-handoff crash** | marker posted, next assignee never woke (idle/error, no `executionRunId`, stalled > 120s) | **Auto-recover:** resume-then-heartbeat the next assignee | orchestrator |
| 8 | **Run-hung** | `executionRunId` set but no completion past `hungRunTimeoutSec` (1800s) | **Cancel + re-trigger once**, then halt | orchestrator *(gap today)* |
| 9 | **Iteration loop** | Build↔Test > 8 or Build↔Review > 3 runs | **Halt** with loop reason | orchestrator |
| 10 | **Approval / disposition wait** | `request_confirmation` open, or "Paperclip needs a disposition" | `[CLIENT]` → **auto-accept** agent plan-confirmation; `[INTERNAL]` → **escalate** to Telegram | orchestrator *(gap today)* |
| 11 | **Presentation-Designer stall** | `[CLIENT]` build routes through presentation-designer, which the orchestrator doesn't watch | **Fix:** add to watch set (`orchestratorWatchUrlKeys`) | orchestrator *(gap today)* |
| 12 | **Parent-child terminal gap** | parent `blocked` on a child that reached `in_review`/`done` (e.g. AUT-65 ← AUT-66) | **Notify** operator the tree is review-ready; don't leave parent silently blocked | orchestrator *(gap today)* |
| 13 | **Silent terminal state** | issue reaches `in_review` (the correct `[INTERNAL]` "await approval" state) without a clear ping | **Guarantee** one operator ping with location on reaching terminal | completion notify |
| 14 | **External / UI-only block** | Drive 403, n8n activate (UI), credential setup (UI) | **Halt** with the exact manual step (by design) | agent → orchestrator |

---

## Two enforcement points + the guarantee

- **preflight (pre-dispatch):** kills classes 1-6 before a build starts. Auto-fixes the cheap ones,
  blocks dispatch (non-zero exit) on anything red. The n8n dispatcher calls it before creating an issue.
- **orchestrator (in-flight):** catches classes 3, 7-12 on a 30s poll; resumes/heartbeats or halts;
  every halt writes a structured event + a categorized Telegram message.
- **completion guarantee (13):** on reaching `done` or `blocked`, fire exactly one operator ping,
  tag-aware (`[CLIENT]` → demo/ROI/workflow links; `[INTERNAL]` → branch + RELEASE_NOTES + "await merge").

---

## Live audit snapshot — 2026-05-29 (baseline before hardening)

- paperclip `ok` v2026.513.0; postgres `sysv` ✓; OAuth-only ✓; watchdog active ✓; **listener inactive**.
- **All 5 core build agents: `wakeOnDemand` unset** (Failure #1 — live, unfixed).
- Orchestrator watches 5 of 6 build agents — **missing presentation-designer** (#11).
- **AUT-65** blocked 3d on child **AUT-66** (`in_review`) — parent-child gap (#12), seen-but-ignored by the 3h health-check.
- 4 issues in `in_review` 6-10 days (AUT-66/46/29/10) — correct terminal state, awaiting operator.

---

## Bike-Method ramp gates (production autonomy graduation)

Autonomy is earned, not granted. Three gates between "+- works" and trusting the pipeline with
real customers / real-deploy. Each gate is a measurable, falsifiable thing — no vibes.

| Gate | Condition to clear | Effect of passing |
|---|---|---|
| **A — Canary green** | One green `canary.js` per track (INTERNAL + CLIENT), end-to-end through real agents, reaching terminal | The toolkit is live and proven; orchestrator + preflight + canary all wired |
| **B — Real builds, zero touch** | 3 consecutive real `[INTERNAL]` builds + 3 consecutive real `[CLIENT]` builds with **zero manual intervention** (no human heartbeat triggers, no manual resume, no halt that needs operator action) | `ORCH_AUTO_ACCEPT=1` may be enabled for `[CLIENT]` (pipeline auto-accepts agent plan-confirmations) |
| **C — Cost + latency in band** | Per-build Max-abo budget < $30 INTERNAL / < $40 CLIENT; wall-clock < 30min INTERNAL / < 90min CLIENT, sustained over 5 builds | Pipeline considered production-stable; Bike-Method Phase 3 → 4 transition for routine builds |

### Status as of 2026-05-30

- ✅ **Gate A — PASSED.** INTERNAL: AUT-115 (5/5 markers in 8 min, `in_review`). CLIENT: AUT-118/119 (CTO→child→Engineer→QA→Product→Release, 60 min, real multi-iteration recovery, ended `done`).
- ⏳ **Gate B — 0/3 + 0/3.** Counts the next 3 real builds per track from this point.
- ⏳ **Gate C — bands defined, not yet measured at scale.**

### Known follow-ups before Gate B counts cleanly

- `canary.js`: detect parent→child split on `[CLIENT]`, pivot watcher to the child (currently watcher dies on parent block).
- `canary.js` markers: include `PLAN_LOCKED` for CTO; tighten release-engineer regex to `RELEASE STAGED|RELEASE_NOTES` (the broad `release` matched stray text in the CLIENT canary scorecard).
- CTO routing: when CTO splits a `[CLIENT]` issue into a child, **preserve the `[CLIENT]` tag** so the Presentation Designer routing kicks in. AUT-119 ran as `[BUILD]` and skipped the Presentation Designer entirely (no process-diagram / ROI / demo script produced).

