# Cockpit — Booking Tool — Handoff & Status (2026-06-29)

## TL;DR
A custom Calendly for the 4-person Automatisierbar team is **LIVE and fully working** at
**https://cockpit.automatisierbar.ch/book**. A prospect books a 60-min on-site
"Prozessermittlung" with *Automatisierbar* (not an individual); the team decides who takes
it afterward. It runs on the VPS (Flask → gunicorn → systemd, behind Caddy). Code is on
branch `feat/cockpit-booking`.

**Paused here to fix a few bugs (Joaquin will list them), THEN swap the website link.**

---

## ✅ What's LIVE and verified working
- Branded **calendar** booking page (Calendly-style month picker), real Automatisierbar logo, HTTPS (Let's Encrypt).
- Fields mirror the old Google page 1:1: **Vor-&Nachname, E-Mail, Telefon, Firmenname, Firmenadresse** + optional **Notiz**.
- On confirm: **matches/creates a Notion lead** (Leads DB) + **writes a "Termine" appointment** + **Telegrams the team** ("Neue Buchung — UNASSIGNED, wer übernimmt?") + **emails the prospect from info@** with an "Zum Kalender hinzufügen" button.
- **Custom-request fallback** ("Kein passender Termin dabei?") → team Telegram + lead.
- Availability mirrors the Google settings: **Mon–Fri 08:00–18:00**, 24h notice, 45-min buffer, max 6/day, 30-day horizon, Europe/Zurich.

## ⏳ What's LEFT to do
1. **Fix the bugs Joaquin lists** (this is why we paused — he found issues, likely in the email content/format, page UX, Telegram text, or wording). *Ask him for specifics: where + what's wrong vs expected.*
2. **Swap the website link** — point automatisierbar.ch's booking button to `https://cockpit.automatisierbar.ch/book` (replacing the old Google appointment-schedule link). *Check if the marketing site is in this repo; if so do it in a PR.*
3. **(Optional) Google Calendar** — connect a Google calendar (service account: `COCKPIT_CALENDAR_ID` + `GOOGLE_SERVICE_ACCOUNT_JSON` in `/etc/cockpit/env`) so the page hides busy times AND auto-creates a real Google invite (truly-automatic calendar entry). Until then it serves windows-only slots and the email's add-to-calendar button covers it. Code is already written + graceful — just needs the credential.
4. **(Optional) MCP connectors** — Hostinger MCP (needs a Hostinger API token) + Infomaniak Mail MCP (token already saved). Both need one Claude restart to load. *Note: SSH already gives full server control, so this is convenience only.*
5. **Roadmap (later phases):** ~~Phase 2 internal team PWA + per-person logins + claim flow~~ **✅ BUILT** (see below); Phase 3 live IMAP inbox monitoring; Phase 4 follow-up-due aging zone.

   **Phase 2 — Team PWA + claim flow (built 2026-06-29):** Installable phone app at
   **`cockpit.automatisierbar.ch/team`** (`static/team.html` + `team.webmanifest` + `team-sw.js`).
   Per-person **magic-link** login: each member opens `/team?k=<token>` once (no passwords);
   identity is a signed 365-day session. The app lists upcoming Termine and lets a member tap
   **Übernehmen** to claim (writes `Claimed By` in the Termine DB + posts "✅ {name} übernimmt"
   to the team group). New API: `GET /api/team/whoami|appointments`, `POST
   /api/team/appointments/<id>/claim|unclaim`. Notion fns: `list_appointments`,
   `claim_appointment`, `unclaim_appointment` in `tools/notion_session.py`.

   **Telegram claim buttons** (optional, needs a NEW bot): the booking alert can carry inline
   `[Tej][Joaquin][Nico][Patrik]` buttons handled by `POST /api/team/telegram/webhook`. This uses
   a **dedicated `COCKPIT_TEAM_BOT_TOKEN`** — NOT the operator bot (a webhook on the operator bot
   would 409-break its `getUpdates` polling, per the Telegram-cred-scoping rule). Unset ⇒ the alert
   falls back to the plain operator-bot ping; the PWA claim covers it either way. To enable: create a
   bot via @BotFather, add it to the team group `-5026363666`, set `COCKPIT_TEAM_BOT_TOKEN` +
   `COCKPIT_TELEGRAM_WEBHOOK_SECRET` in `/etc/cockpit/env`, then `POST /api/team/telegram/setup-webhook`
   (X-API-Key) to register the webhook.

   **Setup:** set `COCKPIT_TEAM_TOKENS` (JSON `{"<token>":"Name"}`, 4 tokens) in `/etc/cockpit/env`,
   restart cockpit, hand each person their `/team?k=<token>` link.
6. **🔐 Rotate the Infomaniak full-workspace token** (it was pasted in chat). Reissue (ideally mail-only scope), then update `.env` + `/etc/cockpit/env` `INFOMANIAK_MAIL_TOKEN`.
7. **(Optional) Merge `feat/cockpit-booking` → `main`** (cleanup; deploy currently pulls the branch directly).

---

## Root routing (cockpit vs interview bot)
The same `api.py` is the public **interview bot** on Render *and* the cockpit app on the VPS. To keep the interview bot off the booking domain's front door, the env var `COCKPIT_HOME=1` (set only in `/etc/cockpit/env`) makes the bare root `/` serve the landing page `static/cockpit-home.html`; the interview bot moves to the **unlisted** `/interview` (no login, just not linked). On Render `COCKPIT_HOME` is unset, so `/` still serves the bot. Gate: `api._cockpit_home()`.

## Infrastructure — where everything lives
- **Live URL:** https://cockpit.automatisierbar.ch/book · health: `/health`
- **VPS:** Hostinger `187.124.188.2` (Ubuntu 24.04), runs Caddy (also serves fitness.automatisierbar.ch).
- **SSH (from Joaquin's Mac):** `ssh cockpit-vps` (alias in `~/.ssh/config` → root@187.124.188.2, key `~/.ssh/id_ed25519`). The key is authorized in `/root/.ssh/authorized_keys2` on the box.
- **App on box:** repo clone at `/srv/cockpit/app`, venv `/srv/cockpit/venv`, systemd unit `cockpit.service` running `gunicorn api:app --bind 127.0.0.1:8082`, Caddy site block `cockpit.automatisierbar.ch { reverse_proxy 127.0.0.1:8082 }`.
- **Server env (secrets):** `/etc/cockpit/env` (root, chmod 600). Keys: `PORT, FLASK_SECRET_KEY, NOTION_API_KEY, COCKPIT_PASSWORD, INFOMANIAK_IMAP_USER, INFOMANIAK_IMAP_PASSWORD, INFOMANIAK_MAIL_TOKEN, OPERATOR_TELEGRAM_BOT_TOKEN, PDF_API_KEY, COCKPIT_FROM_EMAIL=info@automatisierbar.ch, COCKPIT_FROM_NAME=Automatisierbar, COCKPIT_TEAM_CHAT_ID=-5026363666, COCKPIT_APPOINTMENTS_DB_ID`.
- **Repo:** GitHub `joaquinautomatisierbar/automatisierbar-interview-bot` (public, also auto-deploys `main`→Render — but we deploy the **branch** to the VPS, which does NOT touch Render). Branch `feat/cockpit-booking`, latest commit `f9b07f4`. Local: `/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview`.

## Key code files
- `api.py` — booking section near the end: `BOOKING_WINDOWS` + slot engine, routes `GET /book`, `GET /api/book/slots`, `POST /api/book/confirm`, `POST /api/book/request`, `POST /api/cockpit/setup-appointments-db`; Google Calendar helpers (graceful); `_send_team_telegram`.
- `tools/cockpit_email.py` — confirmation email. **Sends via Infomaniak Mail API as info@** (SMTP-as-joaquin@ failed with "Sender mismatch"); SMTP+`.ics` kept as fallback. `build_ics`, `_gcal_add_link`, `_send_via_mail_api`.
- `tools/notion_session.py` — `find_lead_by_email_or_phone`, `expand_lead`, `create_inbound_lead`, `create_appointment`, `create_appointments_db`, schema-aware `build_props`/`_fmt_prop`/`_prop_value`.
- `static/book.html` — the self-contained branded calendar page + custom-request box.
- `deploy/bootstrap.sh` — idempotent, detach-safe deploy script. `deploy/cockpit.service`, `Caddyfile.cockpit`, `cockpit.env.example`, `cockpit-deploy.md`.

## Key IDs / config values
- **Notion Leads DB ("Interview Datenbank"):** `31cbebb0c2f980479e9ffc59851f8a34`
- **Notion Termine/Appointments DB:** `38ebebb0-c2f9-817a-8384-de9c2dcf4164` (parent = Operations Cockpit `311bebb0c2f980de89a0f3d463a0fbce`)
- **Telegram team group:** `-5026363666` (posts via OPERATOR bot token)
- **Infomaniak Mail API:** base `https://mail.infomaniak.com/api`, send = `POST /mail/{uuid}/draft` with `action:"send"`, auth `Bearer $INFOMANIAK_MAIL_TOKEN`. **info@ mailbox uuid:** `f8c17c7b-86fd-3a44-8abe-2d9522a29552`.
- **Render service** (source of `NOTION_API_KEY`): `srv-d84g218js32c739r2u9g` (pulled via `RENDER_API_KEY_AUTOMATISIERBAR` in `.env`).
- **Booking settings (env-overridable, defaults in api.py):** `SLOT_MINUTES=60`, `COCKPIT_LEAD_DAYS=1` (24h), `COCKPIT_HORIZON_DAYS=30`, `COCKPIT_BUFFER_MINUTES=45`, `COCKPIT_MAX_PER_DAY=6`. Edit `BOOKING_WINDOWS` in api.py to change days/hours.

## Common commands
```bash
# Redeploy after pushing code to the branch:
ssh cockpit-vps 'cd /srv/cockpit/app && git fetch -q origin feat/cockpit-booking && \
  git reset -q --hard origin/feat/cockpit-booking && chown -R paperclip:paperclip /srv/cockpit && \
  systemctl restart cockpit && sleep 2 && systemctl is-active cockpit'

# Logs / status:
ssh cockpit-vps 'journalctl -u cockpit -n 50 --no-pager'
ssh cockpit-vps 'systemctl status cockpit'

# Edit a server env var then restart:
ssh cockpit-vps 'nano /etc/cockpit/env && systemctl restart cockpit'

# Public smoke test:
curl -s https://cockpit.automatisierbar.ch/api/book/slots | head
```

## Walk-in mode (Phase 1) — field PWA on the same app

New installable PWA at **walkin.automatisierbar.ch** (same Flask app, separate Caddy host + PWA scope). Two functions: **Neuer Lead** (capture → Leads DB row *and* a 💡-callout line, so `/walkinmail` + `/walkinleadsconvert` keep working) and **Sprachmemo** (record → VPS disk → daily Gemini transcription → "Walk-in Knowledge Base" Notion DB). Auth = the existing team magic-link (`COCKPIT_TEAM_TOKENS`, same 4 members) — no new tokens.

Routes: `GET /walkin` · `GET /walkin-sw.js` · `GET /walkin.webmanifest` · `GET /api/walkin/whoami` · `POST /api/walkin/lead` · `POST /api/walkin/memo` · `GET /api/walkin/memos` · `POST /api/walkin/setup-kb-db`.

**One-time setup on the VPS:**
```bash
# 1) DNS A-record: walkin -> 187.124.188.2  (then Caddy auto-issues TLS)
# 2) Caddy host block (deploy/Caddyfile.cockpit already has it):
ssh cockpit-vps 'nano /etc/caddy/Caddyfile && systemctl reload caddy'
# 3) Env (in /etc/cockpit/env): GEMINI_API_KEY=...  WALKIN_MEMO_DIR=/srv/cockpit/voice_memos
#    WALKIN_TRANSCRIBE_MAX_PER_DAY=10  WALKIN_MAX_AUDIO_MB=20   (see cockpit.env.example)
# 4) Memo dir:
ssh cockpit-vps 'sudo -u paperclip mkdir -p /srv/cockpit/voice_memos'
# 5) Deploy code (git pull + restart), then create the KB DB ONCE:
curl -s -X POST https://cockpit.automatisierbar.ch/api/walkin/setup-kb-db -H "X-API-Key: $PDF_API_KEY"
#    -> copy database_id into WALKIN_KB_DB_ID in /etc/cockpit/env, then restart cockpit.
# 6) Daily transcription cron (as paperclip):
#      CRON_TZ=Europe/Zurich
#      0 7 * * * /srv/cockpit/app/tools/scheduled/walkin-transcribe.sh
# 7) Each team member opens https://walkin.automatisierbar.ch/walkin?k=<their token> once → Add to Home Screen.
```

**Prereq:** `GEMINI_API_KEY` (free Google AI Studio key). Until set, the cron no-ops with a logged warning; capture + upload still work. Transcription log: `/srv/cockpit/app/.tmp/walkin-transcribe.log`.

**First real lead write halts to Telegram** (live Leads DB + live callout are production) — see `workflows/walkin_mode.md`.

## Gotchas we already solved (don't re-debug)
- **SSH:** root key auth needed; key went into `/root/.ssh/authorized_keys2` (the main `authorized_keys` had a glued-key newline issue). `PermitRootLogin` set via `/etc/ssh/sshd_config.d/99-cockpit.conf`.
- **`NOTION_API_KEY` is NOT in local `.env`** — it lives on Render; we pulled it via the Render API and put it in `/etc/cockpit/env`.
- **`import re` was missing** in `notion_session.py` (only triggered when Notion is live) — fixed.
- **Email "Sender mismatch":** Infomaniak refuses to let joaquin@ send *as* info@. Solution = Infomaniak **Mail API** (token), which sends as info@. info@ IS a real mailbox.
- **Hostinger browser terminal drops on long commands** — deploy runs detached (`setsid`) and logs to a file.
- **git "dubious ownership"** — `bootstrap.sh` adds `safe.directory` so root can operate on the paperclip-owned repo.

---

## Paste this into a NEW Claude session to continue
> Continue the **Cockpit booking tool** (custom Calendly) for Automatisierbar. It is LIVE at
> https://cockpit.automatisierbar.ch/book on the VPS (SSH alias `cockpit-vps` = root@187.124.188.2).
> Code is in this repo on branch `feat/cockpit-booking`; the full status + infra + IDs + commands
> are in `deploy/COCKPIT_HANDOFF.md` (and on my Desktop). The booking flow is fully working
> (page → Notion lead + Termine appointment + team Telegram + info@ confirmation email via the
> Infomaniak Mail API). I have a few bugs to fix first — here they are: [LIST YOUR BUGS]. After
> the bugs, we swap the website booking link to /book. Read `deploy/COCKPIT_HANDOFF.md` first.
