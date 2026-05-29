#!/bin/bash
# Polls paperclip /api/health; if DB unreachable for 2 consecutive checks, restart paperclip.
STATE=/var/run/paperclip-watchdog-fails
fails=$(cat $STATE 2>/dev/null || echo 0)
status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3100/api/health)
if [ "$status" = "200" ]; then
  echo 0 > $STATE
  exit 0
fi
fails=$((fails+1))
echo $fails > $STATE
logger -t paperclip-watchdog "health=$status fails=$fails"
if [ $fails -ge 2 ]; then
  logger -t paperclip-watchdog "RESTARTING paperclip after $fails consecutive unhealthy checks"
  systemctl restart paperclip
  echo 0 > $STATE
fi
