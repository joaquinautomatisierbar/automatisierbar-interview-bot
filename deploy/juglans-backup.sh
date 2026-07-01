#!/usr/bin/env bash
# Juglans nightly backup (cron). Tars DATA_DIR (drafts + custom positions — the
# only non-regeneratable data), rotates to JUGLANS_BACKUP_KEEP archives, and
# Telegram-pings the operator on failure. Self-contained (no Python needed).
#
# Install on the VPS:
#   sudo cp deploy/juglans-backup.sh /srv/juglans/backup.sh
#   sudo chmod +x /srv/juglans/backup.sh
#   # add to paperclip's crontab, e.g. nightly at 03:15:
#   #   15 3 * * *  /srv/juglans/backup.sh >> /srv/juglans/backup.log 2>&1
set -euo pipefail

ENV_FILE=/etc/juglans/env
[ -f "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }

DATA_DIR="${DATA_DIR:-/srv/juglans/data}"
BACKUP_DIR="${JUGLANS_BACKUP_DIR:-/srv/juglans/backups}"
KEEP="${JUGLANS_BACKUP_KEEP:-14}"

notify_fail() {
  local msg="$1"
  if [ -n "${OPERATOR_TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${OPERATOR_TELEGRAM_CHAT_ID:-}" ]; then
    curl -s -m 15 "https://api.telegram.org/bot${OPERATOR_TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${OPERATOR_TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=⚠️ Juglans backup failed: ${msg}" >/dev/null || true
  fi
  echo "[juglans-backup] FAIL: ${msg}" >&2
}
trap 'notify_fail "unexpected error on line $LINENO"' ERR

mkdir -p "$BACKUP_DIR"
stamp="$(date +%F_%H%M)"
archive="${BACKUP_DIR}/juglans-data-${stamp}.tar.gz"

tar czf "$archive" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
# Rotate: keep the newest $KEEP archives, delete the rest.
ls -1t "${BACKUP_DIR}"/juglans-data-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -f

echo "[juglans-backup] ok -> ${archive}"
