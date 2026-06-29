# Cockpit Booking — Deploy SOP (cockpit.automatisierbar.ch)

The booking tool (custom Calendly) is part of the Flask app (`api.py`). It runs on
the **VPS** (`187.124.188.2`, always-on, Caddy) under gunicorn + systemd — no Render
cold starts. The public booking page is **`/book`**; that's the link that replaces
the Google appointment-schedule link on automatisierbar.ch.

Routes added:
- `GET  /book` — public booking page (`static/book.html`)
- `GET  /api/book/slots` — bookable 60-min slots (windows − calendar busy)
- `POST /api/book/confirm` — book: calendar event + lead match/create + Appointment row + team Telegram
- `POST /api/cockpit/setup-appointments-db` — one-time: create the Notion Termine DB (auth)

Everything **degrades gracefully**: with no Google credential the slot engine serves
windows-only slots and the calendar write no-ops; with no Notion key the lead/appointment
writes no-op; with no Telegram token the notification is skipped. The page is usable the
moment it's served — the integrations light up as their credentials land.

---

## One-time setup on the VPS

```bash
# 1) Clone the repo (deploy branch) into /srv/cockpit/app
sudo mkdir -p /srv/cockpit && sudo chown paperclip:paperclip /srv/cockpit
git clone <repo-url> /srv/cockpit/app && cd /srv/cockpit/app
git checkout feat/cockpit-booking   # or main after merge

# 2) Python venv + deps
python3 -m venv /srv/cockpit/venv
/srv/cockpit/venv/bin/pip install -r requirements.txt

# 3) Secrets / config (root-only)
sudo mkdir -p /etc/cockpit
sudo cp deploy/cockpit.env.example /etc/cockpit/env
sudo nano /etc/cockpit/env        # fill in NOTION_API_KEY, calendar id+cred, telegram token, etc.
sudo chmod 600 /etc/cockpit/env

# 4) systemd service
sudo cp deploy/cockpit.service /etc/systemd/system/cockpit.service
sudo systemctl daemon-reload && sudo systemctl enable --now cockpit
journalctl -u cockpit -n 30        # confirm it started, bound to 127.0.0.1:8082

# 5) Caddy site block (TLS auto)
sudo sh -c 'cat >> /etc/caddy/Caddyfile' < deploy/Caddyfile.cockpit
sudo systemctl reload caddy
```

## Create the Notion Appointments DB (once, after step 3)

```bash
curl -X POST https://cockpit.automatisierbar.ch/api/cockpit/setup-appointments-db \
  -H "X-API-Key: $PDF_API_KEY" -H "Content-Type: application/json" -d '{}'
# → {"database_id": "..."} — put it in /etc/cockpit/env as COCKPIT_APPOINTMENTS_DB_ID,
#   then: sudo systemctl restart cockpit
```

## Redeploy (after code changes merge)

```bash
cd /srv/cockpit/app && git pull && /srv/cockpit/venv/bin/pip install -r requirements.txt
sudo systemctl restart cockpit
```

---

## Handoff — what needs YOU (UI-gated)

1. **DNS** — Infomaniak: add A-record `cockpit` → `187.124.188.2`.
2. **SSH** — give me access to `187.124.188.2` so I can run the steps above (or run them yourself).
3. **Shared "Automatisierbar" Google calendar** — confirm/create the one calendar that
   drives availability + holds the booked events. Then:
   - **Service account (recommended):** create one in Google Cloud, download its JSON,
     share the calendar with the SA email as "Make changes to events", paste JSON (or
     base64) into `GOOGLE_SERVICE_ACCOUNT_JSON`, set `COCKPIT_CALENDAR_ID`.
   - *(or an OAuth token file at `GOOGLE_TOKEN_JSON`.)*
4. **Team Telegram bot token** — set `OPERATOR_TELEGRAM_BOT_TOKEN` (the team group
   `-5026363666` is already the default `COCKPIT_TEAM_CHAT_ID`).
5. **Website** — once live, swap the Google appointment-schedule link on automatisierbar.ch
   for `https://cockpit.automatisierbar.ch/book`.

## Verify end-to-end (use a throwaway lead first)

```bash
curl -s 'https://cockpit.automatisierbar.ch/api/book/slots' | head
# Book a throwaway slot via the page, then check:
#  - Notion: a Termine row + a matched/created lead (War-Room: ◑ Reagiert)
#  - Google: the event exists with location = address, attendee invited
#  - Telegram: "Neue Buchung — UNASSIGNED, wer übernimmt?" in the team group
```

## Tweak availability

Edit `BOOKING_WINDOWS` (and `COCKPIT_LEAD_DAYS` / `COCKPIT_HORIZON_DAYS`) in `api.py`,
then redeploy. Default: Mon–Thu 09–12 & 14–17, Fri 09–12 & 14–16, 60-min slots, 24h
lead time, 21-day horizon, Europe/Zurich.
