# Deploy — Juglans Offerten-Generator (juglans.automatisierbar.ch/offerten)

Streamlit quote builder for **Juglans Landschaftsarchitektur (Philipp Busslinger)**,
run as a native systemd service behind the shared host Caddy on the VPS
(`187.124.188.2`) — same pattern as cockpit / knowspesen (no Docker).

```
Browser → HTTPS + Basic Auth (host Caddy) → 127.0.0.1:8085 (Streamlit, baseUrlPath=offerten)
                                              └─ /srv/juglans/{data (drafts+custom), tmp (catalog+projects_json)}
```

**Why not the repo:** the app bundle (`offerten-generator/`) carries client PII in
`seed/projects_json/`, so it is **not** committed to git — it's rsync'd to the VPS.
Only the secret-free `deploy/juglans.*` files live in the repo.

## Ports / paths
- Streamlit loopback port: **8085** (8082 cockpit, 8083 knowspesen taken).
- App dir: `/srv/juglans/app` · venv: `/srv/juglans/venv` · data: `/srv/juglans/data` · tmp: `/srv/juglans/tmp`.

## 0. DNS (operator / Tej — do first)
Add an A-record in the Infomaniak DNS panel: `juglans` → `187.124.188.2`.
Caddy issues the Let's Encrypt cert automatically within ~60s once it resolves.

## 1. Ship the app bundle (from the Mac, repo root)
```bash
rsync -az --delete \
  --exclude '.env' --exclude 'data/' --exclude '.tmp/' \
  --exclude '__pycache__/' --exclude '*.pyc' \
  "offerten-generator/" root@187.124.188.2:/srv/juglans/app/
```

## 2. One-time server setup (SSH root@187.124.188.2)
```bash
mkdir -p /srv/juglans/{data,tmp}
python3 -m venv /srv/juglans/venv
/srv/juglans/venv/bin/pip install -r /srv/juglans/app/requirements.txt

# Seed the catalog + historical offers into TMP_DIR, custom positions into DATA_DIR
cp /srv/juglans/app/seed/catalog.csv            /srv/juglans/tmp/catalog.csv
cp -r /srv/juglans/app/seed/projects_json       /srv/juglans/tmp/projects_json
cp /srv/juglans/app/seed/custom_positions.csv   /srv/juglans/data/custom_positions.csv

# Service unit + env. The deploy/ files live in the git repo (NOT in the rsync'd
# bundle), so scp them from the Mac:
#   scp deploy/juglans.service   root@187.124.188.2:/etc/systemd/system/juglans.service
#   scp deploy/juglans-backup.sh root@187.124.188.2:/srv/juglans/backup.sh
mkdir -p /etc/juglans
# Create /etc/juglans/env from deploy/juglans.env.example and fill: DATA_DIR, TMP_DIR,
# ANTHROPIC_API_KEY (Tej's), JUGLANS_FEEDBACK_DB_ID, and NOTION_API_KEY (reuse the
# operator token already in /etc/knowspesen/env):
#   grep -E '^(NOTION_API_KEY|OPERATOR_TELEGRAM_BOT_TOKEN|OPERATOR_TELEGRAM_CHAT_ID)=' \
#     /etc/knowspesen/env >> /etc/juglans/env
nano /etc/juglans/env
# 640 root:paperclip so systemd AND the paperclip backup cron can read it:
chown root:paperclip /etc/juglans/env && chmod 640 /etc/juglans/env

chown -R paperclip:paperclip /srv/juglans
systemctl daemon-reload && systemctl enable --now juglans
sleep 2
curl -sS http://127.0.0.1:8085/offerten/_stcore/health && echo   # -> "ok"
journalctl -u juglans -n 30 --no-pager
```

## 3. Caddy vhost (SSH, root)
Generate the login hash, paste the block, reload:
```bash
caddy hash-password --plaintext 'CHOOSE_A_PASSWORD'   # copy the $2a$... output
# Append deploy/Caddyfile.juglans to /etc/caddy/Caddyfile, replacing
# BASIC_AUTH_USER_HERE (e.g. busslinger) and BASIC_AUTH_HASH_HERE (the hash).
nano /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

## 4. Verify
```bash
curl -sSI https://juglans.automatisierbar.ch/offerten     # 401 without creds (Basic Auth up)
curl -sSI -u busslinger:PASSWORD https://juglans.automatisierbar.ch/offerten/  # 200
```
Then in a browser: log in → build a quote → add/remove a position (undo banner) →
save a draft → trigger one **KI-Vorschlag** (confirms the API key) → open the
sidebar **💬 Feedback an Automatisierbar**, send a test message, confirm it lands
in the Juglans Feedback Notion DB. Finally `systemctl restart juglans` and confirm
the draft persisted (volume/data OK).

## 5. Backups (optional, recommended from day 1)
```bash
cp /srv/juglans/app/deploy/juglans-backup.sh /srv/juglans/backup.sh
chmod +x /srv/juglans/backup.sh
# paperclip crontab:  15 3 * * *  /srv/juglans/backup.sh >> /srv/juglans/backup.log 2>&1
```

## 6. Usage tracker → Notion "Juglans Usage" DB (pilot ammo)
The app writes `DATA_DIR/usage_log.jsonl` (best-effort; auto-backed-up by the
nightly backup above — no change needed). A cron rolls that log up into one Notion
row per day so the operator can watch pilot engagement. Runs out-of-band, never in
the client path.
```bash
# 1) Add the Usage DB id to /etc/juglans/env (create the DB in Notion first; the
#    operator Notion token already in the env just needs the DB shared to it):
#      JUGLANS_USAGE_DB_ID=<the new db id>
nano /etc/juglans/env && systemctl restart juglans   # restart so the app picks up env (only needed if you also changed app-read vars)

# 2) Install the sync wrapper + hourly cron. The repo-root deploy/ is NOT in the
#    rsync'd app bundle, so scp the wrapper from the Mac (like juglans-backup.sh):
#      scp deploy/juglans-usage-sync.sh root@187.124.188.2:/srv/juglans/usage-sync.sh
chmod +x /srv/juglans/usage-sync.sh && chown paperclip:paperclip /srv/juglans/usage-sync.sh
# paperclip crontab:  0 8-21 * * *  /srv/juglans/usage-sync.sh >> /srv/juglans/usage-sync.log 2>&1

# 3) Sanity check (no writes): prints the per-day aggregate from the log
sudo -u paperclip /srv/juglans/venv/bin/python /srv/juglans/app/tools/usage_notion_sync.py --dry-run
```

`JUGLANS_USAGE_DB_ID` is read only by the cron (not the app), so no service restart
is required for the sync. If the id is unset the sync no-ops and the log still
accumulates locally.

## Update later

```bash
# from the Mac: rsync the new bundle, then on the VPS:
rsync -az --delete --exclude '.env' --exclude 'data/' --exclude '.tmp/' \
  "offerten-generator/" root@187.124.188.2:/srv/juglans/app/
ssh root@187.124.188.2 '/srv/juglans/venv/bin/pip install -r /srv/juglans/app/requirements.txt && systemctl restart juglans'
```

## Troubleshooting
- **502 / blank page:** `journalctl -u juglans -f`; confirm `--server.baseUrlPath=offerten` and that Caddy does NOT strip `/offerten` (no `handle_path`).
- **KI error:** `ANTHROPIC_API_KEY` set/valid in `/etc/juglans/env`? (Restart the service after editing.)
- **Feedback not landing:** `NOTION_API_KEY` + `JUGLANS_FEEDBACK_DB_ID` set, and the Notion **integration connected to the DB** (Notion → DB → ⋯ → Connections). A 404 in `journalctl` = integration not shared.
- **Data gone after restart:** `DATA_DIR`/`TMP_DIR` pointing at `/srv/juglans/...`?
