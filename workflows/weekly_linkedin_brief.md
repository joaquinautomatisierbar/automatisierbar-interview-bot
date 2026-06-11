---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: posts published per week (target ≥1)
last_updated: 2026-05-10
---

# Weekly LinkedIn Content Brief

**Phase 1 (training wheels).** Friday auto-generates a structured brief
into Notion that the separate claude.ai LinkedIn brand project pulls
on demand. Brief contains raw signals + Hormozi-hook-mapped angles
— NOT finished posts. The brand chat writes the post.

| Component | Path |
|---|---|
| Orchestrator | `tools/linkedin_brief.py` |
| Signal modules | `tools/signals/{git,decisions,notion_diff,n8n}_signals.py` |
| Synthesis prompt | `prompts/linkedin_brief_synthesis.md` |
| Cron entrypoint | `tools/scheduled/linkedin-brief-friday.sh` |
| launchd plist | `.tmp/com.automatisierbar.linkedin-brief.plist` (staged, not installed) |
| Notion DB | "LinkedIn Content Briefs" (`NOTION_BRIEFS_DB_ID`) |

## Pipeline

```
Friday 16:00 launchd
  → tools/scheduled/linkedin-brief-friday.sh (activates .venv, sources .env)
  → tools/linkedin_brief.py
       collect_signals()
         ├─ git_signals (commits last 7d in this repo)
         ├─ decisions_signals (decisions/log.md window)
         ├─ notion_diff (Lead-DB / LinkedIn Activity / Call Analytics / Weekly Reports)
         └─ n8n_signals (executions stats — best-effort)
       _is_empty_week? → empty stub, status=Skipped, no LLM
       else → claude_client.generate_linkedin_brief(signals)
                model=claude-sonnet-4-6, system=prompts/linkedin_brief_synthesis.md
                retries: 3 with exponential backoff
                fail → _stub_brief() with raw signals only, status=Draft
       Notion: find_brief_for_week → create_brief_page or replace_brief_body
       Telegram: notify-telegram.sh checkpoint <url>  (or halt on stub/failure)
```

## Inputs

- `ANTHROPIC_API_KEY` (required for synthesis)
- `NOTION_API_KEY` (required for any Notion read/write)
- `NOTION_BRIEFS_DB_ID` (required for live write — set after bootstrap)
- `NOTION_LEADS_DB_ID` (optional — falls back to hardcoded Interview-Datenbank)
- `NOTION_LINKEDIN_DB_ID` (optional — skips if missing)
- `NOTION_CALL_ANALYTICS_DB_ID` (optional — skips if missing)
- `NOTION_WEEKLY_REPORTS_DB_ID` (optional — skips if missing)
- `N8N_API_KEY` + `N8N_BASE_URL` (optional — skips n8n stats if missing)
- `OPERATOR_TELEGRAM_BOT_TOKEN` + `OPERATOR_TELEGRAM_CHAT_ID` (for ping)

## Outputs

**Notion DB "LinkedIn Content Briefs"** — one row per week:
- `Name` (title): `Brief KW-<iso> · <week_of>`
- `Week Of` (date): the Friday anchor
- `Status` (select): `Draft` / `Reviewed` / `Posted` / `Skipped`
- `Commit Count`, `Decision Count` (number)
- `Posted URL` (url, manual fill after publish)
- Page body: full markdown brief in a `language: markdown` code block

**Telegram (operator chat)** — one message per run:
- Success: `[linkedin-brief] KW-XX · YYYY-MM-DD bis YYYY-MM-DD bereit (N Wörter, Status=Draft). <url>`
- Empty week: `… stille Woche, Status=Skipped. <url>`
- Synthesis failed: `… synthesis FAILED, stub written. Manual rewrite needed: <url>`

## Brief structure (markdown body)

1. `# Brief KW-<iso> · <week_of>`
2. `## Zahlen der Woche` — 3–6 lines, each with a real number
3. `## Was gebaut wurde` — 3–5 deterministic bullets from git+decisions
4. `## Strategische Entscheidungen` — one line per decisions/log entry in window
5. `## Operative Wins` — Notion DB diffs as plain text
6. `## Post-Angle-Vorschläge` — 2–3 angles, each mapped to H1–H10 hook with
   Auslöser / Konkreter Aufhänger / Zahl-Story-Pointe / Voice-Reminder
7. `## Roh-Material` — JSON block for the brand chat to pull exact strings

Hard cap: 800 words target (synthesis prompt enforces it; orchestrator
warns at >1000).

## Mid-week notes workflow (zero-typing skeleton)

The brief page can exist *before* Friday so you can capture observations,
customer quotes, and post-worthy moments as they happen. Friday's auto-run
**merges** instead of overwriting — your notes survive.

### How it runs (Monday 09:00 auto-cron)

A launchd job fires every **Monday 09:00 Europe/Zurich** and pre-creates the
upcoming Friday's brief page automatically. You don't have to type anything.

- Plist: `~/Library/LaunchAgents/com.automatisierbar.linkedin-brief-monday.plist`
- Wrapper: `tools/scheduled/linkedin-brief-monday.sh`
- Idempotent: if you already created the page (via `/new-brief` or manually),
  the Monday cron sees it and exits clean. Won't duplicate.
- Telegram ping on success with the new page URL.

### One-time macOS permission (required before Monday cron can run)

macOS blocks launchd-spawned processes from reading files under `~/Desktop/`
without Full Disk Access (TCC). Until you grant this, the Monday cron will
silently fail.

**Grant Full Disk Access to `/bin/bash`:**

1. System Settings → Privacy & Security → Full Disk Access
2. Click the `+` button (lock icon may prompt for password)
3. Press `Cmd+Shift+G` in the file picker, type `/bin/bash`, hit Enter
4. Click "Open" → confirm the toggle is ON

Verify with: `launchctl start com.automatisierbar.linkedin-brief-monday`
then `tail .tmp/linkedin-brief-monday-launchd.stderr` — should be empty.
If you still see "Operation not permitted", try granting FDA to
`/usr/libexec/launchd` or `/usr/local/bin/bash` instead.

### Manual fallback (if you skip the cron or it fires too early)

1. **Any time Mon–Thu** — in Claude Code, run:
   ```
   /new-brief
   ```
   The slash command computes the upcoming Friday, creates a Notion page with
   `Name = "Brief KW-XX · YYYY-MM-DD"`, `Week Of = <that Friday>`, `Status =
   Draft`, body = callout + `Wochen-Notizen` heading + empty paragraph.
   Returns the URL.

   Optional argument: `/new-brief 2026-05-22` to target a specific Friday
   (e.g. two Fridays out, or to fill a gap).

   Under the hood the command runs
   `python tools/linkedin_brief.py --create-page [--week-of YYYY-MM-DD]`.

2. **Throughout the week** — open the page and write whatever you want:
   paragraphs, bullets, callouts, headings, embedded screenshots, anything
   Notion supports. **Native Notion blocks** are preserved on Friday.

3. **Friday 16:00** — script finds your page (matching `Week Of`), preserves
   every user block, refreshes only the synthesis code block at the end.

### Auto-Title formula property

The DB has a read-only formula property `Auto-Title` that computes the
canonical title from `Week Of` (e.g. `Brief KW-20 · 2026-05-15`). If you
ever create a page manually and forget to set Name, this column displays the
correct title for reference.

To add it to an existing DB (one-time): `python tools/linkedin_brief.py
--add-auto-title`.

### Pure-Notion manual create (no Claude Code needed)

If you'd rather click `+ New` directly in Notion:

1. Open the `LinkedIn Content Briefs` DB.
2. Click `+ New`.
3. Set `Week Of` to the upcoming Friday.
4. (Optional) Type the Name — the `Auto-Title` formula column shows what it
   should be. Or leave Name blank; Friday-script doesn't depend on it.
5. Write your notes as native Notion blocks. No need to add the
   `Wochen-Notizen` heading manually unless you want the structure.

If you want true 1-click creation in Notion (no typing at all), set up a
Notion DB template manually:
- DB header → `+ New` dropdown → `+ New template`
- Name the template "Wochen-Brief"
- Pre-fill Status=Draft, add a `## Wochen-Notizen` heading
- Save
- Notion will now apply it on every `+ New` (you still type `Week Of`).

### Block-level contract (important)

The merge is **block-type-aware**, not text-aware:

| Block type | Who owns it | What happens on Friday |
|---|---|---|
| Paragraph, heading, bulleted/numbered list, callout, toggle, quote, divider, image, embed, code (non-markdown), table, anything else Notion-native | You | **Preserved untouched** |
| `code` block with `language: markdown` | The script | **Replaced wholesale** (backup written to `.tmp/` first) |

**Practical rule:** don't type inside the markdown code block — your edits there
will be lost on Friday (recoverable from `.tmp/` backup, but inconvenient).
Write notes as native Notion blocks above or below it.

### Status-locked pages

Once you promote a brief to `Reviewed` or `Posted` (e.g. after editing the
synthesis content for a final post), Friday's script **refuses to overwrite**
without `--force`. Protects your edits.

### Pre-merge backup

Every merge that touches an existing synthesis block writes the prior content
to:

```
.tmp/brief-pre-merge-<page-id-no-dashes>-<UTC-iso-timestamp>.md
```

Tiny text files; kept indefinitely. Recover from these if a merge clobbered
something.

---

## Manual operations

```bash
# Synthetic dry-run (no live signal calls):
python tools/linkedin_brief.py --dry-run --fixture .tmp/test_signals.json

# Real-signals dry-run for last week:
python tools/linkedin_brief.py --dry-run

# Specific week, real write:
python tools/linkedin_brief.py --week-of 2026-05-09

# Overwrite an existing brief:
python tools/linkedin_brief.py --week-of 2026-05-09 --force

# Bootstrap the Notion DB (one-time):
python tools/linkedin_brief.py --bootstrap-db --parent-page-id <notion-page-id>

# Sandbox-DB live write (e.g. testing in a separate Notion DB):
python tools/linkedin_brief.py --briefs-db-id <sandbox-db-id>
```

## Bike Method rollout

| Phase | Trigger | Behavior |
|---|---|---|
| **1 (default)** | First 2 Fridays | launchd OFF. Joaquin runs `--dry-run` manually, eyeballs output, runs without `--dry-run` to commit. Status defaults to `Draft`. |
| **2** | Weeks 3–4 | launchd loaded. Auto-runs Friday 16:00. Status=`Draft`. Joaquin marks `Reviewed` in Notion before brand chat trusts it. |
| **3** | Week 5+ | Edit `--status Reviewed` in the wrapper or change default in code. Telegram becomes informational only. |

Phase advances **only by editing** the `bike-method-phase` frontmatter
in this file plus updating the wrapper / launchd config. Never automatic.

## Halt-conditions (Telegram halt fired automatically)

- Synthesis failed terminally after 3 retries → stub brief written, halt ping with manual-rewrite request.
- Notion write failed → halt ping with the error.

## Edge cases

| Case | Behavior |
|---|---|
| Empty week (zero commits / decisions / DB diffs / executions) | Empty-stub brief, status=`Skipped`, no LLM call. |
| First-ever run, no `NOTION_BRIEFS_DB_ID` | Refuses with clear `--bootstrap-db` instruction. Exit code 2. |
| Brief for that week already exists | Refuses without `--force`. Exit code 1. |
| With `--force` | Replaces page body (archives existing children, appends fresh code block) and patches Status + counts. |
| `N8N_API_KEY` missing | n8n signal section returns `available=false`, brief still ships without exec stats. |
| Notion DB-key missing for any optional DB | That DB section reports `available=false`, brief synthesis ignores it. |
| Anthropic 429/5xx | Retry 3× with 0.2/0.8/3.2s exponential backoff. Terminal failure → stub brief + halt ping. |
| `--dry-run` | Prints brief to stdout. No Notion write. No Telegram. |

## Verification (run before enabling launchd)

1. **Synthetic fixture:** create `.tmp/test_signals.json` with hand-written sample signals; run `--dry-run --fixture` and read output.
2. **Real-signals dry-run:** `python tools/linkedin_brief.py --dry-run` — eyeball voice rules.
3. **Sandbox live write:** point `--briefs-db-id` at a throwaway Notion DB.
4. **Empty-week test:** `python tools/linkedin_brief.py --week-of 2025-12-25 --dry-run`.
5. **Idempotency:** run same `--week-of` twice — second refuses without `--force`.
6. **Brand-chat smoke:** open claude.ai LinkedIn project, ask "Lies den letzten Brief und gib mir 1 Post."

After 6/6 pass: install launchd plist, advance to Phase 2.

## Related

- `prompts/linkedin_voice.md` — comment-bot voice (NOT this brief). Coexists; different purpose.
- `tools/notion_linkedin.py` — owns the LinkedIn Activity DB. `notion_diff.py` calls into it.
- `references/business-context.md` — synthesis prompt loads §1+§2.
- `decisions/log.md` — primary narrative-rich source of post-worthy strategic moments.
