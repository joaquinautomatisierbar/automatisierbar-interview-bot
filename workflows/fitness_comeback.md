---
title: Fitness Comeback Protokoll — Scheduling Automation
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more value per customer (personal — operator health/durability)
status: live (Weeks 1–6); Phase 3 parked
last_updated: 2026-06-09
---

# Comeback Protokoll — Fitness Scheduling

Turns the Notion plan **"Comeback Protokoll — 10 Wochen"**
(page `37abebb0c2f981b1b58de7438b8cd7ee`) into a running schedule across three surfaces.
Covers **Weeks 1–6** (Phase 1 Runterfahren + Phase 2 Basis). **Week 1 = Mon 2026-06-22.**
Phase 3 (W7–10) is deliberately not programmed — it's built later from real Intervals.icu recovery data.

## Process map (Trigger / Data / Transform / Decision / Destination)
- **Trigger:** manual (operator runs the n8n workflow; calendar + Hevy were one-time pushes).
- **Data sources:** the Notion plan (sessions, sets/reps, HR zones, phase gates); athlete profile (max HR 209, athlete `i608463`).
- **Transformations:** a Code node computes all 12 cardio events from a single `startMonday` constant; HR targets expressed as % of max HR.
- **Decision points:** Phase 1 = swim-only (no running per the plan); Phase 2 introduces easy run (W4) then 4×4 (W5–6). 4×4s carry a "nur bei grüner HRV-Ampel" cue. HRV traffic-light governs daily execution (operator-side, not automated).
- **Destination:** Intervals.icu → Garmin FR265 (cardio); Google Calendar (full schedule view); Hevy (strength routines).

## Surfaces & IDs

### 1. Cardio → Intervals.icu → Garmin  (the re-runnable automation)
- n8n workflow: **`Etz18IKR0HMxQVff`** "Fitness — Cardio Scheduler (Intervals.icu → Garmin)", folder *Fitness* (`fGJnKeuwRBvetPNf`), project `yIB26z0C1Q40e0oB`.
- Nodes: Manual Trigger → Code "Build 6-Week Cardio" → HTTP "Bulk Upsert to Intervals.icu".
- Credential: Intervals.icu API KEY (httpBasicAuth `Y25K8d7i1vRSXs3K`, username `API_KEY`).
- 12 events: 6 Phase-1 swims (Wed+Sat, 35→40 min), Phase-2 swim Thu + run Fri (W4 easy Z2, W5–6 4×4).
- **Re-anchor:** change `const startMonday = '2026-06-22'` in the Code node and re-run. Idempotent.

### 2. Google Calendar  (one-time push, MCP)
- Calendar `sexyjoaquin15@gmail.com` (Europe/Zurich), colorId `2` (Sage), titles prefixed `🏋️`.
- 13 recurring series: 1 daily Mobility+Cuff floor (DAILY×42 from Jun 22) + 6 Phase-1 weekday + 6 Phase-2 weekday (WEEKLY×3 each; Phase 2 anchored Jul 13).
- Re-push = delete the `🏋️`/Sage events in range + recreate (no dedicated calendar exists; can't create one via API).

### 3. Hevy  (one-time creation via API)
- Routine folder "Comeback Protokoll" id **`3019499`**. Routines:
  - 🦵 Leg Day — Gym `5b321cb1-b502-4dec-a7c9-2afe94b79e7c`
  - 💪 Back & Biceps — Pull `7290b7e0-383e-4401-bac3-492e0ca05da3`
  - 🔱 Chest & Triceps — Push `6f930fde-8a7e-463e-af18-747680e6e468`
  - 🔥 Abs — regressiert `285134a3-48f9-4970-9920-f851725c9ba4`
  - 🛡️ Cuff & Schulter-Reha `486445c4-5ad7-4339-b878-fe606e682374`
  - 🟦 Full Body — reduziert `993c1473-de83-41c2-a149-3b34573b45f8` (Phase-1 Fr, Calisthenics/Home variant; horizontal-pull-biased, no overhead/deep-dips, RIR 3–4; added 2026-06-28)
- Credential (n8n, unused by curl path): Hevy API KEY (httpHeaderAuth `6bF3t3aZ0GpEDcu2`, header `api-key`).
- Created directly via Hevy API (curl), not an n8n workflow — routines are one-time templates; re-running a creator would duplicate (use PUT `/v1/routines/{id}` to edit).

### 4. Garmin Connect — native named Mobility + Cuff workouts (garth)
- **Why not Intervals.icu:** Intervals.icu strips step *names* — a workout_doc step stores only `{duration}` (no label), and rep-only steps vanish. Verified live. So mobility/cuff (which need named moves) can't go via the Intervals→Garmin bridge. The user's old "Mobility Workout" (id 1595331994) failed because it was sportType **`mobility`**, which the FR265 does not accept as a downloadable workout.
- **Solution:** create native Garmin workouts via the unofficial API using **garth** (SSO login `joaquingamonal@icloud.com`, no MFA on the account). Token persisted at `~/.garminconnect` (outside git); password never stored.
- **Key facts:** sportType must be a FR265-supported downloadable type — used **`strength_training`** (id 5). Endpoint `POST /workout-service/workout` (JSON), schedule via `POST /workout-service/schedule/{workoutId}` `{date}`, delete `DELETE /workout-service/workout/{id}`. Step schema: `ExecutableStepDTO` with `stepType` (warmup1/cooldown2/interval3/recovery4/rest5/repeat6), `endCondition` (lap.button1/time2/reps10/iterations7), `category` + `exerciseName` (FIT enum), `description`. Validate exercise codes by POST→readback (invalid `exerciseName` is silently nulled).
- **Workouts created:** 🧘 Mobility — Daily `1596765340` (8 moves, reuses his valid mobility codes) · 🛡️ Cuff & Schulter-Reha `1596765342` (SHOULDER_STABILITY: FLOOR_Y/T/I_RAISE, CABLE_EXTERNAL/INTERNAL_ROTATION, DUMBBELL_FACE_PULL_WITH_EXTERNAL_ROTATION, BAND_EXTERNAL_ROTATION). Scheduled Phase 1: Mobility daily + Cuff Mon/Wed/Fri (Jun 22–Jul 12).
- **Validated-invalid codes** (nulled by Garmin, don't use): 90_DEGREE_CABLE_EXTERNAL_ROTATION, FACE_PULL, SCAPULAR_PULL_UP, BAND_PULL_APART, SCAPTION, REVERSE_FLY. Build helper at `/tmp/garmin_build.py` (session-local).
- **Open:** scheduling stops Jul 12 (extend into Phase 2 on request); old broken "Mobility Workout" 1595331994 can be deleted; user should verify on watch after a Garmin Connect sync.

## API recipes learned (verified live)
- **Intervals.icu HR target syntax:** `description` line `- 35m 70-75% HR` → parses to `{hr:{start,end,units:"%hr"}}` + auto training-load.
- **Intervals.icu intervals:** text `4x` repeat does NOT parse via the API. Use structured `workout_doc.steps` with a nested `{"reps":4,"steps":[...]}` block (load stays null — cosmetic).
- **Idempotency:** `POST /api/v1/athlete/{id}/events/bulk?upsert=true` upserts on `external_id` (convention `ab-fit-w{N}-{day}-{type}`). Single `POST .../events` with `upsertOnUid` does NOT dedupe on external_id (caused the original 3 dupes).
- **Delete:** `DELETE /api/v1/athlete/{id}/events/{eventId}` (200).
- **Hevy:** `POST /v1/routine_folders` body `{"routine_folder":{"title":...}}`; `POST /v1/routines` body `{"routine":{title,folder_id,notes,exercises:[{exercise_template_id,superset_id,rest_seconds,notes,sets:[{type:"normal",reps|weight_kg|duration_seconds}]}]}}`. Set field depends on template `type` (reps_only→reps, weight_reps→weight_kg+reps, duration→duration_seconds). Custom-template creation via API not cleanly supported.

## Open items
- **Full Body** (Phase-1 Fr) built in Hevy 2026-06-28 (Calisthenics/Home variant, derived from plan constraints since the original list was never provided). Still **not on Calendar** + **Increase Repetitions** day-tile remains unbuilt (exercises never provided).
- Door-frame isometric rotations + Mobility flow stay in Notion (holds aren't Hevy-loggable).
- Shoulder physio assessment gates all overhead/push progression (Phase 3) — surfaced in notes, not enforceable.

## Phase 3 (later)
Program VO2max 60+ block (4×4 progression), gated planche/handstand, plyo return, sport reintroduction — from Intervals.icu trend data once W1–6 are through. Do not write it ahead of the data.
