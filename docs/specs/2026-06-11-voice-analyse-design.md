# Voice Analyse — Deep Cold-Call Analytics

**Status:** spec / awaiting build go-ahead · **Date:** 2026-06-11 · follows Cockpit 2.0

## Context

The Cockpit 2.0 redesign deferred three deep-analytics views because they need
per-call detail that wasn't durably stored. This spec adds them on a new
**Analyse** page, powered by a durable **per-call store** so every call attempt is
captured at full fidelity — enabling true connect-rate-by-hour and historical
trends, not just the last-call-wins snapshot the Leads DB holds today.

**Decisions locked with the user:**
- Source: **durable per-call store** (not read-only Leads-DB aggregation).
- Placement: **new "Analyse" sidebar page** (keeps Übersicht a clean quick-scan).

**Each view maps to a decision:**
- **Beste Anrufzeit** (hour × weekday heatmap) → call in the windows that connect/convert → more output per hour (serves the 1000-call push).
- **Top-Probleme** → which pains to lead with in the script/offer.
- **Schmerzscore-Verteilung** → lead quality / which segments to prioritize.

## What already exists (reuse)

- Per-call data is computed today: `classify_call_outcome` ([tools/claude_client.py:1062](../../tools/claude_client.py)) returns `bucket, top_problem, schmerzscore, interview_completed, payment_discussed, appointment_*`.
- `_enrich_lead` ([api.py:1896](../../api.py)) already writes a connected-call footprint to the **Leads DB** (`Gesprächsdatum` datetime, `Top Problem`, `Schmnerzscore (1-5)`, `Zahlungsindikator`, `Pipeline Stage`). This is the **backfill source** for history.
- The fired-call list (`cockpit.fired[]`) and bucketing live in the batch finalize path; `fired_at` + Vapi `startedAt/endedAt` give per-call timestamps.
- Notion-write + caching patterns: `_write_session_summary` ([api.py:2067](../../api.py)), `_SPEND_CACHE` (60s budget cache) — mirror these.

## Architecture

### 1. Durable store — new Notion "Voice Calls" DB
Sibling of the existing Voice Sessions DB. **One row per fired call** (connected *and* no-answer, so connect-rate-by-hour works). Schema:

| Prop | Type | Source |
|---|---|---|
| Call (title) | title | `{firma} · {date}` |
| Call ID | rich_text | Vapi call id — **dedup key** |
| Date | date (w/ time) | `startedAt` or `fired_at` |
| Branche | select | lead branche |
| Firma | rich_text | lead firma |
| Lead ID | rich_text | Notion lead page id |
| Batch ID | rich_text | session batch id |
| Script Version | select | session script_version |
| Connected | checkbox | transcript + duration ≥ 8s |
| Bucket | select | hot/followup/cold/hangup/noanswer |
| Duration s | number | `_call_duration_s` |
| Cost CHF | number | vapi cost × 0.90 |
| Top Problem | rich_text | cls.top_problem |
| Schmerzscore | number | cls.schmerzscore |
| Payment | checkbox | cls.payment_discussed |
| Interview Completed | checkbox | cls.interview_completed |
| Disclose AI | checkbox | fired.disclose_ai |

### 2. Write hook — `_write_voice_call(rec)`
Best-effort, non-fatal (try/except + logger, like `_enrich_lead`). Wired into the
**finalize/bucketing path** so it runs for **every fired call once its bucket is
known** (incl. `noanswer`) — not only inside `_enrich_lead` (connected-only).
Dedup strategy: **append + dedupe-at-read by Call ID** (keeps the hot path a single
write, no pre-query). Aggregation keeps the latest row per Call ID.

### 3. Aggregation endpoint — `GET /api/cockpit/insights?days=N&branche=…`
Auth-gated (`_cockpit_auth_ok`). Queries Voice Calls DB (filter `Date ≥ cutoff`,
optional branche), paginates, dedupes by Call ID, returns:
```
{
  "time_of_day": [{dow:0-6, hour:0-23, calls, connected, hot}],
  "top_problems": [{problem, count, avg_schmerz}],   // normalized: trim+lowercase-group
  "schmerzscore": {"1":n,"2":n,"3":n,"4":n,"5":n},
  "kpis": {interview_completion_rate, payment_rate, chf_per_hot, avg_dur_hot, avg_dur_cold}
}
```
Cached ~5 min in-process (mirror `_SPEND_CACHE`).

### 4. Frontend — `static/analyse.html` in the shell
- Add `Analyse` to the `NAV` array in [static/cockpit-shell.js](../../static/cockpit-shell.js) (4th item + icon) and route `/voice/analyse` in api.py (mirrors `/voice/overview`).
- Topbar: period selector (reuse `.seg`) + branche filter.
- **Beste Anrufzeit:** CSS-grid heatmap, rows = weekdays, cols = business hours, cell intensity = selected metric, hover tooltip with raw counts. Metric toggle: Volumen / Connect-Rate / Hot-Rate.
- **Top-Probleme:** ranked `Shell.hbars` + avg-Schmerzscore badge per problem.
- **Schmerzscore-Verteilung:** 1–5 bar histogram + average.
- **Bonus KPI strip:** Interview-Completion %, Payment-Discussed %, CHF/Hot (stat cards).
- Reuses cockpit.css tokens + Shell chart helpers; add a `.heatmap` component to cockpit.css.

### 5. Optional backfill — seed history from the Leads DB
One-shot (script or `POST /api/cockpit/insights/backfill`): read Leads DB rows with
`Gesprächsdatum` set, map to Voice Calls rows (connected-only, last-call-wins), insert
if Call ID / lead+date not already present. Seeds the heatmap/lists so the page isn't
empty on day one. Marked optional.

## Build sequence
1. Create Voice Calls Notion DB (confirm parent page); capture DB id → config/env.
2. `_write_voice_call` + wire into the batch finalize path (every fired call).
3. `/api/cockpit/insights` endpoint + 5-min cache.
4. `static/analyse.html` + nav item + `/voice/analyse` route + `.heatmap` CSS.
5. (optional) Leads-DB backfill to seed history.
6. Verify: run a small real/pin batch → rows land in Voice Calls → endpoint aggregates → heatmap/lists render; toggle period + branche.

## Defaults (override if wrong)
- Heatmap: **Mo–Fr**, hours **08:00–19:00** (B2B Swiss cold-call window).
- Top-Probleme normalization: trim + case-insensitive grouping; show top 10.
- Backfill: **yes** (seed from Leads DB) so the page has data immediately.
- Write scope: **every fired call** incl. no-answer (required for connect-rate-by-hour).

## Halt / risk notes
- Creating the Voice Calls DB and writing per-call rows are **writes to live Notion**.
  It's a **new analytics DB** (not the Leads/customer DB), append-only, best-effort and
  non-fatal — low blast radius. Per the halt-before-acting policy, the **first real
  write run halts to Telegram** for confirmation. Writes are spaced by `gap_sec`; Notion
  rate limits are not a concern at cold-call volume.
- Render disk is ephemeral → Notion is the correct durable store (matches the existing
  Voice Sessions pattern); no new infra.
