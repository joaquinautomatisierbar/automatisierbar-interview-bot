#!/usr/bin/env bash
# Bi-weekly Telegram ping reminding Joaquin to refresh references/business-context.md.
# Invoked by ~/Library/LaunchAgents/com.automatisierbar.refresh-business-context.plist
# every Monday at 09:00 Europe/Zurich. Self-gates to odd ISO weeks so it actually fires
# every 14 days (anchor: 2026-05-18 = ISO week 21, odd).
#
# Exits 0 always — a missed ping must not appear as a launchd failure.

set -u

PROJECT_ROOT="/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
LOG_FILE="$PROJECT_ROOT/.tmp/refresh-business-context-ping.log"
mkdir -p "$(dirname "$LOG_FILE")"

iso_week="$(date +%V)"
parity=$((10#$iso_week % 2))
now="$(date '+%Y-%m-%d %H:%M:%S %Z')"

if [ "$parity" -eq 0 ]; then
  echo "[$now] skipped — ISO week $iso_week is even (bi-weekly anchor is odd)" >> "$LOG_FILE"
  exit 0
fi

msg="Time to refresh references/business-context.md (last updated 2 weeks ago). Open Claude Code in this project and run /refresh-business-context to walk the bi-weekly update."

bash "$PROJECT_ROOT/.claude/hooks/notify-telegram.sh" checkpoint "$msg" >> "$LOG_FILE" 2>&1
echo "[$now] fired — ISO week $iso_week (odd), Telegram checkpoint dispatched" >> "$LOG_FILE"

exit 0
