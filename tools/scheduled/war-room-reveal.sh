#!/usr/bin/env bash
# War Room scoreboard — daily reveal/kickoff cron entrypoint.
# Invoked by launchd:
#   ~/Library/LaunchAgents/com.automatisierbar.war-room-reveal.plist   (PM, 20:00)
#   ~/Library/LaunchAgents/com.automatisierbar.war-room-kickoff.plist  (AM, 08:30, optional)
#
# Arg 1: mode = "pm" (default, full reveal + Pace-State write) or "kickoff" (AM nudge).
# Activates the project venv if present (else system python3), sources .env,
# runs tools/war_room_scoreboard.py. Always exits 0 — a non-zero from Python is
# logged but must not bubble up to launchd (a "failed" job stops firing).

set -u

MODE="${1:-pm}"
PROJECT_ROOT="/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
LOG_FILE="$PROJECT_ROOT/.tmp/war-room-${MODE}.log"
ERR_FILE="$PROJECT_ROOT/.tmp/war-room-${MODE}.err"
mkdir -p "$(dirname "$LOG_FILE")"

now() { date '+%Y-%m-%d %H:%M:%S %Z'; }
echo "[$(now)] === war-room-${MODE} start ===" >> "$LOG_FILE"

cd "$PROJECT_ROOT" || { echo "[$(now)] ERR: cannot cd to project root" >> "$ERR_FILE"; exit 0; }

# Source .env, tolerating both "KEY=value" and "KEY = value" styles.
if [ -f ".env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|\#*) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    key="$(echo "$key" | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')"
    val="$(echo "$val" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')"
    case "$val" in \"*\") val="${val#\"}"; val="${val%\"}" ;; \'*\') val="${val#\'}"; val="${val%\'}" ;; esac
    [ -n "$key" ] && export "$key=$val"
  done < ".env"
fi

# Prefer the project venv; fall back to system python3 (both carry `requests`).
PY="python3"
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"

"$PY" tools/war_room_scoreboard.py --mode "$MODE" >> "$LOG_FILE" 2>> "$ERR_FILE"
rc=$?
echo "[$(now)] === war-room-${MODE} end (rc=$rc) ===" >> "$LOG_FILE"
exit 0
