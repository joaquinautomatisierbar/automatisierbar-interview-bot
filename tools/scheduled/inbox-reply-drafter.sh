#!/usr/bin/env bash
# Inbox auto-reply drafter — VPS cron entrypoint (every ~10 min).
# Install on the cockpit VPS (runs as the cockpit.service user `paperclip`):
#   chmod +x /srv/cockpit/app/tools/scheduled/inbox-reply-drafter.sh
#   crontab -u paperclip -e   # then add:
#     CRON_TZ=Europe/Zurich
#     */10 * * * * /srv/cockpit/app/tools/scheduled/inbox-reply-drafter.sh
#
# Sources /etc/cockpit/env (same secrets file as cockpit.service), prefers the cockpit
# venv, runs tools/inbox_reply_drafter.py. ALWAYS exits 0 — a non-zero from Python is
# logged but must not bubble up (cron would otherwise email failures).
#
# Needs JOAQUIN_IMAP_USER / JOAQUIN_IMAP_PASSWORD (joaquin@ mailbox app-password) in the
# env file; the cockpit's INFOMANIAK_IMAP_* point at info@, a different mailbox.

set -u

APP_DIR="/srv/cockpit/app"
ENV_FILE="/etc/cockpit/env"
LOG_FILE="$APP_DIR/.tmp/inbox-reply-drafter.log"
ERR_FILE="$APP_DIR/.tmp/inbox-reply-drafter.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }
echo "[$(now)] === inbox-reply-drafter start ===" >> "$LOG_FILE"

cd "$APP_DIR" || { echo "[$(now)] ERR: cannot cd to $APP_DIR" >> "$ERR_FILE"; exit 0; }

# Parse the EnvironmentFile line-by-line (no shell expansion — values like
# COCKPIT_PASSWORD=...$ or base64 JSON must NOT be re-interpreted by the shell).
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

"$PY" tools/inbox_reply_drafter.py >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?
echo "[$(now)] === inbox-reply-drafter end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
