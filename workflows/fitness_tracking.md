---
title: Fitness Tracking & Motivation System
autonomy-level: L3
bike-method-phase: 2
kpi-bucket: more value per customer (personal — operator health/consistency/regeneration)
status: live — daily sync + Notion + Scriptable widget + web dashboard (fitness.automatisierbar.ch); week-as-a-whole adherence
last_updated: 2026-06-28
---

# Fitness Tracking & Motivation System

Closes the feedback loop on the Comeback: **Garmin + Hevy → Notion** daily, weekly summaries,
a motivating Notion dashboard, and an iPhone home-screen widget. Built 2026-06-09.

## Architecture
```
Garmin FR265 ─nightly─► Garmin Connect ─garth (token resume, NO login)─┐
Hevy ──────────────────────── api-key ─────────────────────────────────┤
                                                                        ▼
                                            ~/.comeback-sync/fitness_sync.py   (launchd 07/13/20h)
                                            compute: adherence · HRV-Ampel · trends · volume
                                              ├─► Notion 3 DBs (if NOTION_TOKEN set)
                                              └─► n8n "Fitness — Widget JSON" (POST ingest)
                                                                        │
                          ┌──────────────────────────────────────────────┴────────────┐
                          ▼                                                             ▼
              Notion hub: 📊 Tracking & Fortschritt                      Scriptable widget (GET /fitness-widget)
        (headline · trajectory · 4 charts · 2 linked tables)         week row · HRV-Ampel dial · streak
```
- **Garmin = garth, token-resume only** (Intervals.icu wellness lacks HRV/VO2max for this athlete — verified — so garth is the source). Token at `~/.garminconnect` (1-yr). Daily loop never logs in → no MFA/Cloudflare block; if the token dies it Telegram-halts and exits (no stdin wait).
- **Compute in Python, Notion is display.** Every value (adherence, Ampel, trends, emoji bars) is computed in the script and written as plain values → no dependency on Notion formulas/charts to be "correct".

## Key IDs
- Notion hub: `37bbebb0c2f98131827bf239ef41115a` · Dashboard page: `37bbebb0c2f981208e93eb58958be66c`
- Daily Log db `551b60032992485c8caa47ae1ca4f447` (ds `215e466b-f99a-419b-99b2-2de7f903a626`)
- Workouts db `bce09993b23d4c8da3ce8144d9bcc5c0` (ds `a90f41d0-327c-4c61-9685-16e35a0c4e10`)
- Weekly Summary db `c2fa8adb06774a11809040e1c6574c97` (ds `0929c338-d3ee-4a3b-b8ba-96f104ecb9b6`)
- n8n widget workflow `uaEuGP0DOVi6Z75H` (Fitness folder `fGJnKeuwRBvetPNf`), published.
  - ingest POST `https://oojoaquin.app.n8n.cloud/webhook/fitness-widget-ingest`
  - serve  GET  `https://oojoaquin.app.n8n.cloud/webhook/fitness-widget`  (stores payload in workflow static data)
- Garmin: garth token `~/.garminconnect`, displayName `113231a6-c1df-4d69-b74c-e164e72f5aa6`, athlete VO2max 56.9.

## Files
- Canonical script: `tools/fitness/fitness_sync.py` (repo, version-controlled).
- **Deployed copy: `~/.comeback-sync/`** — own venv + focused `.env`. launchd runs THIS copy, not the repo, because macOS TCC blocks background agents from `~/Desktop`. **After editing the repo script, redeploy:** `cp tools/fitness/fitness_sync.py ~/.comeback-sync/`.
- **Sync host = VPS (Option B, since 2026-06-09 eve):** `paperclip@187.124.188.2:~/comeback-sync/` (own venv garth 0.8 + requests; garth token at VPS `~/.garminconnect`; SSH key `~/.ssh/paperclip_vps`). Cron `0 5,11,18 * * *` UTC (= 07/13/20 Zurich CEST; box is `Etc/UTC`), log `~/comeback-sync/sync.log`. Always-on, laptop-independent. **Redeploy after editing the repo script:** `scp tools/fitness/fitness_sync.py paperclip@187.124.188.2:~/comeback-sync/`.
  - **2026-06-22 — re-deployed here after the Paperclip VPS consolidation killed the old host.** The cron originally lived on `72.61.106.8`, which was decommissioned/refunded in the migration to `187.124.188.2`; comeback-sync was NOT carried over by the Paperclip rsync, so the widget + Notion dashboard silently froze on the last push (Jun 13 05:00 UTC). Rebuilt from scratch on the new box: dirs + venv + garth token scp'd from Mac + `.env` (NOTION_API_KEY appended from `/etc/paperclip/secrets`, `GARMIN_TOKEN_DIR=/home/paperclip/.garminconnect`) + crontab entry. Verified end-to-end: `daily: 10 days -> Notion daily 10, weekly 3` + widget pushed. **Lesson: comeback-sync lives outside the Paperclip data tree, so any future VPS move must re-deploy it explicitly.**
- Mac launchd (`com.automatisierbar.fitnesssync.plist`) is **disabled** (renamed `.disabled`) to avoid double-runs; `~/.comeback-sync/` on the Mac remains as dev/backup. (Background jobs can't run from `~/Desktop` due to macOS TCC — hence both copies live outside it.)
- Widget: `tools/fitness/widget.js` (Scriptable). `WIDGET_URL` already set to the serve endpoint.

## Sync modes
`fitness_sync.py --mode <mode>` (run with `~/.comeback-sync/venv/bin/python3`):
- `daily` — today + trailing 3 days → Notion (if token) + widget push. **launchd uses this.**
- `weekly` — recompute recent weeks (rollup) + widget push.
- `backfill --days N` — last N days → Notion + widget.
- `emit --days N` — print computed rows + `mcp_daily` (SQLite-prop format) + widget JSON as JSON; **no writes** (used to seed via the Notion MCP without a token).
- `widget` — build + push only the widget JSON.

## Data model (computed)
- **Daily Log** (key Tag=ISO date): done flags (Mobility/Cuff/Cardio/Kraft from Garmin activities + Hevy), HRV ms + **HRV-Ampel** (numeric vs Garmin baseline; sleep<6h downgrades green→gelb), RHR, Schlaf h (glitch <2h dropped), Schlaf-Score, Body Battery (day max), VO2max, Readiness, Training Load, Schritte, Kraft-Volumen, Adhärenz (done/planned), Trend arrow (HRV vs 7-day avg).
- **Weekly Summary** (key Woche=ISO): sessions done/planned, Adhärenz, HRV/RHR Ø + Δ, Schlaf Ø, VO2max + Δ, volumes, Streak, Trajektorie headline, emoji Fortschritt bar.
- **Adherence plan map** (`planned_for(date)`): Mobility daily; Cuff Mon/Wed/Fri; Cardio Wed+Sat; Strength Tue/Thu/Fri (Ph1: Legs/Increase-Reps/Full-Body) or Mon-Thu (Ph2). Tunable in the script; only applies W1-6 (Jun 22–Aug 2). (Thu strength added 2026-06-28 with the Increase Repetitions rep-ladder; locked by `test_fitness_sync.py`, week planned total W1 = 15.)
- **Week-as-a-whole adherence (2026-06-28).** Weekly completeness is a day-independent **bag of sessions** (`week_bag`): it counts planned vs done session *types* across the whole ISO week and credits `Σ min(done[t], planned[t]) / Σ planned[t]`, capped per-type. So a session done on a different day than scheduled (swim Mon instead of Wed; full-body on Sun instead of Tue) still credits the week. `annotate_week_coverage` flags such days `covered` + `moved` (only when the type's full weekly quota is met, so it never contradicts a sub-100% week). Daily checkboxes stay literal (honest per-day record); only the *weekly* number + widget/dashboard use the bag. A moved session (surplus done on a non-scheduled day) covers the earliest still-missed planned slot of its type (greedy 1:1), display-only — the bag counts each session once via its `done` day so coverage never inflates the number. **Guarded by `tools/fitness/test_fitness_sync.py`** (11 invariant checks; run `~/.comeback-sync/venv/bin/python3 tools/fitness/test_fitness_sync.py` after ANY edit to `week_bag`/`annotate_week_coverage`/`build_week_view`).

## Ongoing Notion write path — RESOLVED (2026-06-11)
**Live + autonomous.** The VPS reuses the existing Notion integration token from `/etc/paperclip/secrets` (`NOTION_API_KEY`, ntn_ — the hub + 3 DBs are connected to that integration). It's copied into VPS `~/comeback-sync/.env`; the script's `NOTION_TOKEN` falls back to `NOTION_API_KEY`. Daily cron upserts daily rows **and** current/prev ISO-week summaries (idempotent by Tag/Woche; verified 36 daily rows, no duplicates). No token paste was needed.

<details><summary>Original note (historical)</summary>

### (was) the one open item
The cron currently pushes the **widget** every run (no token needed) and writes **Notion only if `NOTION_TOKEN` is set** in `~/.comeback-sync/.env`. The 31-day backfill + 5 weekly rows were seeded via the Notion MCP (so the dashboard is fully populated now). To automate ongoing daily Notion rows:
1. notion.so/my-integrations → New internal integration → copy `secret_…`.
2. Share the hub page ("Comeback — Kommandozentrale") with that integration (… → Connections).
3. Add `NOTION_TOKEN=secret_…` to `~/.comeback-sync/.env`. Done — next sync writes daily rows.
(Alternative considered: route through the existing n8n Notion cred; not wired because the token path is simpler/more reliable. The DB ids above are ready for either.)

</details>

## Operations
- **Re-seed / extend history via MCP (no token):** `~/.comeback-sync/venv/bin/python3 fitness_sync.py --mode emit --days N` → take `mcp_daily` → `notion-create-pages` into Daily Log ds. (Use upsert/dedupe by `Tag` to avoid duplicates on re-run.)
- **Run now:** `launchctl start com.automatisierbar.fitnesssync` (or run the script directly).
- **Verify widget:** `curl https://oojoaquin.app.n8n.cloud/webhook/fitness-widget`.
- **Garmin token refresh (≈yearly):** re-run garth login (see workflows/fitness_comeback.md) and copy the token to `~/.garminconnect`.

## Dashboard — fitness.automatisierbar.ch (phone web app)
Phone-first PWA (Clean-Minimal, "instrument readout": Space Grotesk + JetBrains Mono, pine/mist palette).
Built 2026-06-28. Source: `tools/fitness/dashboard/` (`index.html` single-file + `manifest.webmanifest` +
`sw.js` offline cache + `icon.svg`/`icon-{180,192,512}.png`, icons rasterized by `scratchpad/gen_icons.py`).
**v2 (2026-06-28):** the hero is a horizontal **week swipe-pager** over `weeks_view` (W1–W6; future weeks
planned-only from `planned_for`, no Garmin cost) — swipe to preview upcoming weeks. The ring is **Garmin-
style adherence-coloured** (`adhColor`: ≥90% #fa37ff · 70–90% #5fa6fe · 50–70% #25e673 · 30–50% #fc7728 ·
<30% #f04740; fill = week progress, colour = on-track adherence; future = neutral); WOCHEN history bars use
the same ramp. **Tapping a day** opens a bottom-sheet with that day's `sessions` (each planned type + status
done/verschoben/verpasst/anstehend + real name: "Leg Day · 15 Sätze · 88 min", "Schwimmen · 35 min").
Today's HRV+verdict is a slim global strip under the pager. Other panels: today's Garmin metrics ·
HRV/RHR/Schlaf/VO2max sparklines · recent Hevy workouts · 6-week adherence history · streak.
- **Data:** `fitness_sync.py` writes `dashboard.json` (superset of the widget JSON: `build_dashboard_json`) on
  every cron run. Target dir = env `DASHBOARD_DIR` (VPS = `/srv/fitness`), else `<script_dir>/dashboard`.
  Per-day `sessions` come from `day_sessions` (Hevy titles for strength, classified Garmin activities for
  cardio/mobility/cuff); `weeks_view` from `build_week_view`; rows carry `activities` (name+klass+dur).
- **Hosting:** Caddy on the VPS (`187.124.188.2`) serves `/srv/fitness` (file_server). Web root is `/srv/fitness`
  — NOT `~/comeback-sync/dashboard` — because the `caddy` user can't traverse `/home/paperclip` (mode 750).
  `/srv/fitness` is `paperclip:paperclip 755` so the cron writes it and caddy reads it.
- **Auth = URL token** (no login; mobile-friendly). Caddy gates ONLY the data file (`/dashboard.json`) on
  `?k=<TOKEN>` OR cookie `k` — the app shell (html/manifest/icons) is public, which avoids a cookie-race on the
  manifest/icon sub-requests at first load (only `dashboard.json` holds personal data). `index.html`
  turns the `?k=` into a 1-year cookie so the saved home-screen app authorises every launch. Token lives only in
  the Caddyfile + the operator's saved URL (it's personal, low-stakes). Block appended to `/etc/caddy/Caddyfile`
  (backup at `/etc/caddy/Caddyfile.bak.<ts>`); `sudo caddy validate` then `systemctl reload caddy`.
- **DNS:** needs an A-record `fitness.automatisierbar.ch → 187.124.188.2` (Infomaniak). Until it exists Caddy
  retries the LE cert every 60s (harmless NXDOMAIN errors); the cert auto-issues once DNS resolves.
- **Redeploy frontend:** `scp tools/fitness/dashboard/{index.html,manifest.webmanifest,sw.js,icon*} paperclip@187.124.188.2:/srv/fitness/`
  then bump the `comeback-v<n>` cache name in `sw.js` to bust the service-worker cache.

## Known limits / next
- Weekly Notion rollup is seeded manually for now; flesh out `--mode weekly` to upsert weekly rows once `NOTION_TOKEN` is in (then add a Monday launchd entry).
- Notion charts use relative date grouping (auto) — fine for trend; switch to per-day in UI if desired.
- Full Body + Increase Repetitions strength days now BUILT in Hevy (2026-06-28); Full Body still pending a Calendar series. Hevy routine maintenance is version-controlled in `tools/fitness/hevy_routine_sync.py` + `hevy_routines.json`; Garmin named workouts in `tools/fitness/garmin_workout_builder.py` + `garmin_workouts.json` (see fitness_comeback.md).
