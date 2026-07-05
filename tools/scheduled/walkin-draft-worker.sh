#!/usr/bin/env bash
# Walk-in auto-draft worker — VPS cron entrypoint (every ~3-5 min).
# Install on the cockpit VPS (runs as the cockpit.service user `paperclip`):
#   chmod +x /srv/cockpit/app/tools/scheduled/walkin-draft-worker.sh
#   crontab -u paperclip -e   # then add:
#     CRON_TZ=Europe/Zurich
#     */3 * * * * /srv/cockpit/app/tools/scheduled/walkin-draft-worker.sh
#
# Sources /etc/cockpit/env (same secrets file as cockpit.service), prefers the cockpit venv,
# runs tools/walkin_draft_worker.py. ALWAYS exits 0 — a non-zero from Python is logged but must
# not bubble up (cron would otherwise email failures). Quality over speed: no per-run timeout.
#
# Needs, in the env file: ANTHROPIC_API_KEY (draft + web-search), NOTION_API_KEY (lead note +
# live Follow-Up Script), and per-mailbox IMAP app-passwords for whoever enters walk-ins:
# NICO_IMAP_USER/PASSWORD, TEJ_IMAP_USER/PASSWORD, PATRIK_IMAP_USER/PASSWORD
# (joaquin@ + info@ already covered by JOAQUIN_IMAP_* / INFOMANIAK_IMAP_*). A mailbox with no
# creds moves its job to `failed` after retries + a single operator Telegram ping — never crashes.

set -u

APP_DIR="/srv/cockpit/app"
ENV_FILE="/etc/cockpit/env"
LOG_FILE="$APP_DIR/.tmp/walkin-draft-worker.log"
ERR_FILE="$APP_DIR/.tmp/walkin-draft-worker.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }
echo "[$(now)] === walkin-draft-worker start ===" >> "$LOG_FILE"

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

"$PY" tools/walkin_draft_worker.py --max-jobs 10 >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?
echo "[$(now)] === walkin-draft-worker end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
