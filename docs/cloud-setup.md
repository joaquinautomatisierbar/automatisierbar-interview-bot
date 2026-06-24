# Cloud setup — make the Claude app a peer to local Claude Code

Goal: work interchangeably on this repo from **local Claude Code** (Mac) and **Claude Code on the web / the Claude app** (phone). The cloud agent clones this repo, but several things that make up the local environment do **not** travel through git and must be configured once in the cloud environment UI.

## What already travels via git (no action needed)
- All code: `api.py`, `tools/`, `workflows/`, `prompts/`, `decisions/`, `data/`
- `CLAUDE.md` (project instructions)
- `.claude/settings.json`, `.claude/hooks/`, `.claude/commands/`
- `.claude/skills/` — including the 7 n8n skills (now committed here, not just `~/.claude/`)
- `.mcp.json` — `n8n-mcp` runs via `npx -y n8n-mcp` (portable, works local + cloud)

## What does NOT travel — configure once in the cloud
Open **claude.ai/code → the `automatisierbar-ops` environment → settings**.

### 1. Environment variables (secrets)
Copy each value from your local `.env` into the environment's **Environment variables** section. They persist across sessions. Stored plaintext — fine for a private solo environment.

**Core (set these first — most tools + MCP servers need them):**
`ANTHROPIC_API_KEY`, `NOTION_API_KEY`, `N8N_API_KEY`
- `N8N_API_URL` = `https://oojoaquin.app.n8n.cloud`  ← **new**, not in local `.env`. Needed to put the `n8n-mcp` server into management mode in the cloud (create/update workflows). Without it, n8n-mcp stays docs-only.
- `CONTEXT7_API_KEY` (optional) — only raises context7 rate limits; works without it.

**Notion / briefs:** `NOTION_BRIEFS_DB_ID`, `NOTION_POST_VARIANTS_DB_ID`, `BRIEF_PERSON`
**Telegram (operator + team):** `OPERATOR_TELEGRAM_BOT_TOKEN`, `OPERATOR_TELEGRAM_CHAT_ID`, `TEAM_TELEGRAM_BOT_TOKEN`, `JOAQUIN_CHAT_ID`, `PATRIK_CHAT_ID`, `NICO_CHAT_ID`, `TEJ_CHAT_ID`
**Voice (Vapi):** `VAPI_API_KEY`, `VAPI_PUBLIC_KEY`, `VAPI_ASSISTANT_ID`, `VAPI_PHONE_NUMBER_ID`
**Telephony (Twilio):** `TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY_SID`, `TWILIO_API_KEY_SECRET`, `TWILIO_PHONE_NUMBER`, `TWILIO_TEST_NUMBER`, `TWILIO_COMPLIANCE_BUNDLE_SID`
**Cockpit / app:** `COCKPIT_PASSWORD`, `PDF_API_KEY`, `WORKFLOW_F_WEBHOOK_SECRET`, `TRIGGER_SECRET_KEY`, `MARKETING_DISPATCHER_WEBHOOK_URL`
**Deploy / misc:** `RENDER_API_KEY_AUTOMATISIERBAR`, `RENDER_API_KEY_SEXYJOAQUIN15`, `GITLAB_PAT_SEXYJOAQUIN15`
**Fitness:** `INTERVALS_API_KEY`, `INTERVALS_ATHLETE_ID`, `HEVY_API_KEY`, `GARMIN_DISPLAY_NAME`, `GARMIN_TOKEN_DIR`, `N8N_WIDGET_PUSH_URL`, `N8N_WIDGET_GET_URL`

> Keep this list in sync when you add a key to `.env`. Names here are safe to commit; **values are not** — they only ever live in `.env` (gitignored) and the cloud UI.

### 2. Network access — REQUIRED, easy to miss
The cloud sandbox blocks arbitrary external APIs by default. Set the environment's network access to allow the domains the tools call, or nothing will reach the APIs even with secrets set:
- `api.anthropic.com`
- `api.notion.com`
- `oojoaquin.app.n8n.cloud` (n8n cloud)
- `api.vapi.ai`
- `api.twilio.com`
- `api.render.com`, `intervals.icu`, `api.hevyapp.com`, Garmin endpoints
- `api.telegram.org`

### 3. Setup script (install Python deps)
In the environment's **setup script** field:
```bash
pip install -r requirements.txt
```
Runs once when the environment is created (cached after). Needed to run `api.py` / the Python tools.

### 4. Google OAuth files (only if you use Drive/Sheets/Calendar via the Python tools)
`credentials.json` / `token.json` are gitignored and there's no file-secret store. Base64-encode each and add as env vars, then decode at session start:
```bash
# locally, to produce the values to paste:
base64 -i credentials.json    # -> set as GOOGLE_CREDENTIALS_B64
base64 -i token.json          # -> set as GOOGLE_TOKEN_B64
```
Add to the setup script:
```bash
[ -n "$GOOGLE_CREDENTIALS_B64" ] && echo "$GOOGLE_CREDENTIALS_B64" | base64 -d > credentials.json
[ -n "$GOOGLE_TOKEN_B64" ] && echo "$GOOGLE_TOKEN_B64" | base64 -d > token.json
```

### 5. MCP servers (wired in `.mcp.json` — portable, token-based)
Account-level claude.ai connectors are user-scoped and don't reliably appear in cloud sessions, so the high-value ones are wired as portable stdio servers in `.mcp.json`. They read their secrets from the env vars you set in step 1 (empty default locally, so they stay inert on the Mac where you use the hosted connectors instead):

| Server | Package | Needs (env) | Gives you |
|---|---|---|---|
| `n8n-mcp` | `n8n-mcp` | `N8N_API_URL` + `N8N_API_KEY` | n8n node docs, validation, **and** create/update/execute workflows on n8n cloud |
| `notion` | `@notionhq/notion-mcp-server` | `NOTION_API_KEY` (passed as `NOTION_TOKEN`) | Read/write Notion pages + databases |
| `context7` | `@upstash/context7-mcp` | `CONTEXT7_API_KEY` (optional) | Up-to-date library/framework docs |

The Notion integration token must have access to the relevant pages (same one your Python tools use).

**Gmail / Calendar / Drive:** not wired as MCP — those need interactive Google OAuth, which the sandbox can't do. Two options: (a) use the existing Python tools, which work off `credentials.json`/`token.json` (provide via the base64 method in step 4); or (b) ask to wire a refresh-token-based Google Workspace MCP as a follow-up. For most work here, (a) already covers it.

## Working interchangeably (local ↔ cloud)
- Cloud sessions branch + open PRs against `automatisierbar-ops`. Default branch `main` holds the full state.
- Pull cloud work to your Mac: `git pull ops main` (or the branch the cloud worked on).
- Push local work up: `git push ops <branch>`.
- `ops` = this private repo. (`joaquinautomatisierbar` = the old public repo that auto-deploys to Render — don't confuse them.)
