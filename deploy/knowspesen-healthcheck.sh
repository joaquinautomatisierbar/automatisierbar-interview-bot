#!/usr/bin/env bash
# KnowSpesen uptime probe wrapper (cron, ~every 10 min). Hits the LIVE health URL and
# Telegram-alerts the operator on state changes (down / recovered). Sources the service
# env for OPERATOR_TELEGRAM_* + SPESEN_DB_PATH (dedup state) + SPESEN_HEALTH_URL.
#
# Install on the VPS:
#   sudo cp deploy/knowspesen-healthcheck.sh /srv/knowspesen/healthcheck.sh
#   sudo chmod +x /srv/knowspesen/healthcheck.sh
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
exec "$PY" tools/spesen/health_check.py "$@"
