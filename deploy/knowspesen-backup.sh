#!/usr/bin/env bash
# KnowSpesen nightly backup wrapper (cron). Sources the service env so
# SPESEN_DB_PATH / SPESEN_RECEIPT_DIR / SPESEN_BACKUP_* / OPERATOR_TELEGRAM_* resolve,
# then runs the online-safe snapshot + rotation (+ optional off-box push).
#
# Install on the VPS:
#   sudo cp deploy/knowspesen-backup.sh /srv/knowspesen/backup.sh
#   sudo chmod +x /srv/knowspesen/backup.sh
#   # add to paperclip's crontab (see deploy/knowspesen-crontab.example)
set -euo pipefail

ENV_FILE=/etc/knowspesen/env
# The app dir is /srv/cockpit/app (shared code); older notes referenced a
# /srv/knowspesen/app symlink. Prefer the symlink if it exists, else the real dir.
APP_DIR=/srv/knowspesen/app
[ -d "$APP_DIR" ] || APP_DIR=/srv/cockpit/app
PY=/srv/cockpit/venv/bin/python3

if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
fi
cd "$APP_DIR"
exec "$PY" tools/spesen/backup.py "$@"
