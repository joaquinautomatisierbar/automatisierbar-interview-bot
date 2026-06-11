#!/usr/bin/env bash
# Wait for a Telegram reply from OPERATOR_TELEGRAM_CHAT_ID and capture it.
# Usage: telegram-poll.sh [timeout_seconds]   (default 600 = 10 min)
# Exit codes:
#   0 — reply received; written to .tmp/telegram-reply.txt and echoed to stdout
#   1 — timeout, no reply within window
#   2 — missing OPERATOR_TELEGRAM_* env vars

set -u
timeout="${1:-600}"
poll_interval=3
http_long_poll=2  # Telegram getUpdates ?timeout= (long-poll, server-side hold)
http_max_time=5   # curl --max-time per request

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$PROJECT_ROOT/.tmp"
ENV_FILE="$PROJECT_ROOT/.env"
STATE_OFFSET="$TMP_DIR/telegram-last-update-id"
REPLY_FILE="$TMP_DIR/telegram-reply.txt"
HALT_MSG_FILE="$TMP_DIR/telegram-halt-message-id"
HALT_TAG_FILE="$TMP_DIR/telegram-halt-tag"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE" 2>/dev/null || true
  set +a
fi

token="${OPERATOR_TELEGRAM_BOT_TOKEN:-}"
chat_id="${OPERATOR_TELEGRAM_CHAT_ID:-}"

if [ -z "$token" ] || [ -z "$chat_id" ]; then
  echo "telegram-poll: OPERATOR_TELEGRAM_BOT_TOKEN or OPERATOR_TELEGRAM_CHAT_ID not set in $ENV_FILE" >&2
  exit 2
fi

mkdir -p "$TMP_DIR"

# Discard halt state files older than 1h (orphaned from a crashed prior session).
# This keeps the "empty file = no active halt" invariant; poller falls back to legacy.
find "$TMP_DIR" -maxdepth 1 -name 'telegram-halt-*' -mmin +60 -exec sh -c ': > "$1"' _ {} \; 2>/dev/null

# Bootstrap: if no offset state, seed from current latest update_id so we ignore
# any historical messages received before this poll started.
last_id=""
if [ -s "$STATE_OFFSET" ]; then
  last_id="$(tr -d '[:space:]' < "$STATE_OFFSET")"
fi

if [ -z "$last_id" ]; then
  seed_resp="$(curl --silent --max-time "$http_max_time" \
    "https://api.telegram.org/bot${token}/getUpdates?offset=-1&limit=1&timeout=0" 2>/dev/null || echo '')"
  seed_id="$(printf '%s' "$seed_resp" | python3 -c '
import json, sys
try:
  d = json.loads(sys.stdin.read() or "{}")
  if d.get("ok") and d.get("result"):
    print(d["result"][-1]["update_id"])
  else:
    print(0)
except Exception:
  print(0)
' 2>/dev/null)"
  last_id="${seed_id:-0}"
  printf '%s' "$last_id" > "$STATE_OFFSET"
fi

deadline=$(( $(date +%s) + timeout ))

# Read halt-thread filter state. If a halt is active, the poller only accepts:
#   (a) replies threaded to the halt's message_id, OR
#   (b) text replies starting with the halt's tag.
# If no halt state is present, fall back to "any text reply matches" (legacy).
target_msg_id=""
target_tag=""
[ -s "$HALT_MSG_FILE" ] && target_msg_id="$(tr -d '[:space:]' < "$HALT_MSG_FILE")"
[ -s "$HALT_TAG_FILE" ] && target_tag="$(tr -d '[:space:]' < "$HALT_TAG_FILE")"
strict_mode="off"
if [ -n "$target_msg_id" ] || [ -n "$target_tag" ]; then
  strict_mode="on"
fi

echo "telegram-poll: waiting up to ${timeout}s for a Telegram reply (offset=$last_id, filter=$strict_mode)" >&2

while [ "$(date +%s)" -lt "$deadline" ]; do
  next_offset=$((last_id + 1))
  resp="$(curl --silent --max-time "$http_max_time" \
    "https://api.telegram.org/bot${token}/getUpdates?offset=${next_offset}&timeout=${http_long_poll}" 2>/dev/null || echo '')"

  if [ -z "$resp" ]; then
    echo "telegram-poll: transient network error, retrying" >&2
    sleep "$poll_interval"
    continue
  fi

  parsed="$(printf '%s' "$resp" | OPERATOR_CHAT_ID="$chat_id" TARGET_MSG_ID="$target_msg_id" TARGET_TAG="$target_tag" python3 -c '
import json, os, sys
try:
  d = json.loads(sys.stdin.read() or "{}")
except Exception:
  print("ERR\t0\t0\t")
  sys.exit(0)
if not d.get("ok"):
  print("ERR\t0\t0\t")
  sys.exit(0)
target = str(os.environ.get("OPERATOR_CHAT_ID", ""))
target_msg_id = (os.environ.get("TARGET_MSG_ID") or "").strip()
target_tag = (os.environ.get("TARGET_TAG") or "").strip()
strict = bool(target_msg_id or target_tag)
match_id = 0
match_text = ""
max_id = 0
for upd in d.get("result", []):
  uid = upd.get("update_id", 0)
  if uid > max_id:
    max_id = uid
  if match_text:
    continue
  msg = upd.get("message") or {}
  chat = (msg.get("chat") or {})
  text = msg.get("text") or ""
  if str(chat.get("id")) != target:
    continue
  if not text:
    continue
  if strict:
    rtm = msg.get("reply_to_message") or {}
    is_thread_match = bool(target_msg_id) and str(rtm.get("message_id", "")) == target_msg_id
    is_tag_match = bool(target_tag) and text.lstrip().startswith(target_tag)
    if not (is_thread_match or is_tag_match):
      continue
    if is_tag_match and not is_thread_match:
      stripped = text.lstrip()[len(target_tag):].lstrip(" :,.\t")
      if stripped:
        text = stripped
  match_id = uid
  match_text = text
print(f"OK\t{max_id}\t{match_id}\t{match_text}")
' 2>/dev/null)"

  status="$(printf '%s' "$parsed" | cut -f1)"
  max_id="$(printf '%s' "$parsed" | cut -f2)"
  match_id="$(printf '%s' "$parsed" | cut -f3)"
  match_text="$(printf '%s' "$parsed" | cut -f4-)"

  if [ "$status" = "OK" ] && [ -n "$max_id" ] && [ "$max_id" != "0" ]; then
    last_id="$max_id"
    printf '%s' "$last_id" > "$STATE_OFFSET"
  fi

  if [ -n "$match_text" ] && [ "$match_id" != "0" ]; then
    printf '%s\n%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$match_text" > "$REPLY_FILE"
    printf '%s\n' "$match_text"
    echo "telegram-poll: captured reply from chat $chat_id" >&2
    : > "$HALT_MSG_FILE"
    : > "$HALT_TAG_FILE"
    exit 0
  fi

  sleep "$poll_interval"
done

echo "telegram-poll: no Telegram reply within ${timeout}s" >&2
: > "$HALT_MSG_FILE"
: > "$HALT_TAG_FILE"
exit 1
