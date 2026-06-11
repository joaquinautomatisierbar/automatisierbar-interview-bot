#!/usr/bin/env bash
# Monday LinkedIn-brief skeleton pre-create — launchd entrypoint.
# Invoked by ~/Library/LaunchAgents/com.automatisierbar.linkedin-brief-monday.plist
# every Monday at 09:00 Europe/Zurich.
#
# Computes the upcoming Friday, creates a skeleton page in the Notion
# "LinkedIn Content Briefs" DB if one doesn't already exist for that week.
# Idempotent: re-runs cleanly even if the page is already there.
#
# Always exits 0 — a missed ping must not turn launchd into a failure state.

set -u

PROJECT_ROOT="/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
LOG_FILE="$PROJECT_ROOT/.tmp/linkedin-brief-monday.log"
ERR_FILE="$PROJECT_ROOT/.tmp/linkedin-brief-monday.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }

echo "[$(now)] === linkedin-brief-monday start ===" >> "$LOG_FILE"

cd "$PROJECT_ROOT" || {
  echo "[$(now)] ERR: cannot cd to project root" >> "$ERR_FILE"
  exit 0
}

if [ ! -x ".venv/bin/python" ]; then
  echo "[$(now)] ERR: .venv/bin/python missing" >> "$ERR_FILE"
  bash "$PROJECT_ROOT/.claude/hooks/notify-telegram.sh" halt \
    "[linkedin-brief] Monday venv missing — manual setup needed" >> "$LOG_FILE" 2>&1 || true
  exit 0
fi

# Source .env (handles both "KEY=value" and "KEY = value" styles)
if [ -f ".env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    key="${line%%=*}"
    val="${line#*=}"
    key="$(echo "$key" | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')"
    val="$(echo "$val" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')"
    case "$val" in
      \"*\") val="${val#\"}"; val="${val%\"}" ;;
      \'*\') val="${val#\'}"; val="${val%\'}" ;;
    esac
    [ -n "$key" ] && export "$key=$val"
  done < ".env"
fi

# Pre-create the brief skeleton for the upcoming Friday.
# Python script handles the idempotency + Telegram ping.
.venv/bin/python tools/linkedin_brief.py --create-page >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?

echo "[$(now)] === linkedin-brief-monday end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
