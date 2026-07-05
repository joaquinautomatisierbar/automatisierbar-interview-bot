#!/usr/bin/env bash
# Mail-Sync CRM logger — VPS cron entrypoint (every ~5 min).
# Reads INBOX + Sent across the 5 team mailboxes, classifies each mail's intent, and pushes it
# to the Automatisierbar Hub as a tagged LeadMail. Never sends mail. ALWAYS exits 0.
#
# Install on the cockpit VPS (runs as the cockpit.service user `paperclip`):
#   chmod +x /srv/cockpit/app/tools/scheduled/mail-sync.sh
#   crontab -u paperclip -e   # then add:
#     CRON_TZ=Europe/Zurich
#     */5 * * * * /srv/cockpit/app/tools/scheduled/mail-sync.sh
#
# Needs, in /etc/cockpit/env: HUB_API_BASE (e.g. https://os.automatisierbar.ch),
# HUB_API_KEY (Hub API key with the leadmail:write scope), ANTHROPIC_API_KEY (classify), and the
# per-mailbox IMAP app-passwords already present for the inbox drafter / walk-in worker
# (JOAQUIN_/INFOMANIAK_/NICO_/TEJ_/PATRIK_IMAP_USER+PASSWORD). A mailbox with no creds is a
# logged no-op; a bad Hub push is retried next run (or marked terminal + one Telegram ping).

set -u

APP_DIR="/srv/cockpit/app"
ENV_FILE="/etc/cockpit/env"
LOG_FILE="$APP_DIR/.tmp/mail-sync.log"
ERR_FILE="$APP_DIR/.tmp/mail-sync.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }
echo "[$(now)] === mail-sync start ===" >> "$LOG_FILE"

cd "$APP_DIR" || { echo "[$(now)] ERR: cannot cd to $APP_DIR" >> "$ERR_FILE"; exit 0; }

# Parse the EnvironmentFile line-by-line (no shell expansion — values like base64 JSON must NOT
# be re-interpreted by the shell).
if [ -f "$ENV_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|\#*) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    key="$(echo "$key" | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')"
    case "$val" in \"*\") val="${val#\"}"; val="${val%\"}" ;; \'*\') val="${val#\'}"; val="${val%\'}" ;; esac
    [ -n "$key" ] && export "$key=$val"
  done < "$ENV_FILE"
fi

PY="/srv/cockpit/venv/bin/python"
[ -x "$PY" ] || PY="python3"

"$PY" tools/mail_sync/sync.py --mailbox all --max-scan 300 >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?
echo "[$(now)] === mail-sync end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
