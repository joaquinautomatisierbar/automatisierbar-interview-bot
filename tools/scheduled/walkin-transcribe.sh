#!/usr/bin/env bash
# Walk-in voice-memo transcription — daily VPS cron entrypoint.
# Install on the cockpit VPS (runs as the cockpit.service user `paperclip`):
#   chmod +x /srv/cockpit/app/tools/scheduled/walkin-transcribe.sh
#   crontab -u paperclip -e   # then add:
#     CRON_TZ=Europe/Zurich
#     0 7 * * * /srv/cockpit/app/tools/scheduled/walkin-transcribe.sh
#
# Sources /etc/cockpit/env (same secrets file as cockpit.service), prefers the
# cockpit venv, runs tools/transcribe_walkin_memos.py. ALWAYS exits 0 — a non-zero
# from Python is logged but must not bubble up (cron would otherwise email failures).

set -u

APP_DIR="/srv/cockpit/app"
ENV_FILE="/etc/cockpit/env"
LOG_FILE="$APP_DIR/.tmp/walkin-transcribe.log"
ERR_FILE="$APP_DIR/.tmp/walkin-transcribe.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }
echo "[$(now)] === walkin-transcribe start ===" >> "$LOG_FILE"

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

"$PY" tools/transcribe_walkin_memos.py >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?
echo "[$(now)] === walkin-transcribe end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
