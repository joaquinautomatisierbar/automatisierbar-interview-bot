#!/usr/bin/env bash
# Operator notifications to Telegram. Three modes:
#   notify-telegram.sh notification           # called by Notification hook; reads JSON event from stdin
#   notify-telegram.sh checkpoint "<summary>" # called explicitly at /loop milestones
#   notify-telegram.sh halt "<reason>"        # called explicitly before halting on a real blocker
# Silently no-ops if OPERATOR_TELEGRAM_BOT_TOKEN / OPERATOR_TELEGRAM_CHAT_ID are unset.
# Always exits 0 — a Telegram outage must not block Claude.

set -u
mode="${1:-}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE" 2>/dev/null || true
  set +a
fi

token="${OPERATOR_TELEGRAM_BOT_TOKEN:-}"
chat_id="${OPERATOR_TELEGRAM_CHAT_ID:-}"

if [ -z "$token" ] || [ -z "$chat_id" ]; then
  exit 0
fi

case "$mode" in
  notification)
    payload=""
    if [ ! -t 0 ]; then
      payload="$(cat 2>/dev/null || true)"
    fi
    msg_body="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
  d=json.loads(sys.stdin.read() or "{}")
  print(d.get("message") or d.get("notification",{}).get("message") or "")
except Exception:
  print("")
' 2>/dev/null)"
    [ -z "$msg_body" ] && msg_body="Claude needs attention"
    text="$(printf 'Claude needs attention: %s' "$msg_body")"
    ;;
  checkpoint)
    summary="${2:-checkpoint}"
    text="$(printf '[checkpoint] %s' "$summary")"
    ;;
  halt)
    reason="${2:-blocker}"
    project_name="$(basename "$PROJECT_ROOT")"
    # Short random tag — used as fallback match if user replies without threading.
    tag="$(head -c 8 /dev/urandom 2>/dev/null | xxd -p 2>/dev/null | head -c 6)"
    if [ -z "$tag" ]; then
      tag="$(printf '%06x' $((RANDOM * RANDOM)) | head -c 6)"
    fi
    tag="Q-${tag}"
    text="$(printf '[halt][%s][%s] %s\n\nReply directly to this message OR start your reply with %s' \
      "$project_name" "$tag" "$reason" "$tag")"
    mkdir -p "$PROJECT_ROOT/.tmp"
    : > "$PROJECT_ROOT/.tmp/telegram-reply.txt"
    : > "$PROJECT_ROOT/.tmp/telegram-last-update-id"
    : > "$PROJECT_ROOT/.tmp/telegram-halt-message-id"
    printf '%s' "$tag" > "$PROJECT_ROOT/.tmp/telegram-halt-tag"
    ;;
  *)
    exit 0
    ;;
esac

resp="$(curl --silent --show-error --max-time 5 \
  -X POST "https://api.telegram.org/bot${token}/sendMessage" \
  --data-urlencode "chat_id=${chat_id}" \
  --data-urlencode "text=${text}" \
  2>/dev/null || echo '')"

if [ "$mode" = "halt" ] && [ -n "$resp" ]; then
  printf '%s' "$resp" | python3 -c '
import json, sys
try:
  d = json.loads(sys.stdin.read() or "{}")
  if d.get("ok"):
    print(d["result"]["message_id"])
except Exception:
  pass
' > "$PROJECT_ROOT/.tmp/telegram-halt-message-id" 2>/dev/null || true
fi

exit 0
