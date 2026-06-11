#!/usr/bin/env bash
# Weekly LinkedIn content brief — Friday cron entrypoint.
# Invoked by ~/Library/LaunchAgents/com.automatisierbar.linkedin-brief.plist
# every Friday at 16:00 Europe/Zurich.
#
# Activates the project venv, sources .env, runs tools/linkedin_brief.py.
# Always exits 0 — any non-zero from the Python script is logged but does
# not bubble up to launchd (a "failed" launchd job stays failed and stops
# firing on schedule, which is worse than a bad brief).

set -u

PROJECT_ROOT="/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
LOG_FILE="$PROJECT_ROOT/.tmp/linkedin-brief-launchd.log"
ERR_FILE="$PROJECT_ROOT/.tmp/linkedin-brief-launchd.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }

echo "[$(now)] === linkedin-brief-friday start ===" >> "$LOG_FILE"

cd "$PROJECT_ROOT" || {
  echo "[$(now)] ERR: cannot cd to project root" >> "$ERR_FILE"
  exit 0
}

# Activate venv
if [ ! -x ".venv/bin/python" ]; then
  echo "[$(now)] ERR: .venv/bin/python missing" >> "$ERR_FILE"
  bash "$PROJECT_ROOT/.claude/hooks/notify-telegram.sh" halt \
    "[linkedin-brief] venv missing — manual setup needed" >> "$LOG_FILE" 2>&1 || true
  exit 0
fi

# Source .env, tolerating both "KEY=value" and "KEY = value" line styles.
# Python's _load_dotenv() handles either; bash `set -a; .` does not — fields
# with spaces around '=' get parsed as commands. Manual loop instead.
if [ -f ".env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    # Strip optional whitespace around the first '='
    key="${line%%=*}"
    val="${line#*=}"
    key="$(echo "$key" | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')"
    val="$(echo "$val" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')"
    # Strip surrounding single or double quotes from value
    case "$val" in
      \"*\") val="${val#\"}"; val="${val%\"}" ;;
      \'*\') val="${val#\'}"; val="${val%\'}" ;;
    esac
    [ -n "$key" ] && export "$key=$val"
  done < ".env"
fi

# Run the brief. Status defaults to Draft. Telegram pings happen inside Python.
.venv/bin/python tools/linkedin_brief.py >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?

echo "[$(now)] === linkedin-brief-friday end (rc=$rc) ===" >> "$LOG_FILE"

# launchd job stays "successful" — Python script handles its own escalation.
exit 0
