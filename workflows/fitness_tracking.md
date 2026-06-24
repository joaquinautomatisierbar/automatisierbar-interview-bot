---
title: Fitness Tracking & Motivation System
autonomy-level: L3
bike-method-phase: 2
kpi-bucket: more value per customer (personal — operator health/consistency/regeneration)
status: live — daily sync + dashboard + widget feed; ongoing Notion write needs token (see below)
last_updated: 2026-06-09
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
- **Adherence plan map** (`planned_for(date)`): Mobility daily; Cuff Mon/Wed/Fri; Cardio Wed+Sat; Strength Tue/Fri (Ph1) or Mon-Thu (Ph2). Tunable in the script; only applies W1-6 (Jun 22–Aug 2).

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

## Known limits / next
- Weekly Notion rollup is seeded manually for now; flesh out `--mode weekly` to upsert weekly rows once `NOTION_TOKEN` is in (then add a Monday launchd entry).
- Notion charts use relative date grouping (auto) — fine for trend; switch to per-day in UI if desired.
- Full Body / Increase Repetitions strength days still pending exercises (see fitness_comeback.md).
