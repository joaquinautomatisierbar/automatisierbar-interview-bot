#!/usr/bin/env bash
# Juglans usage sync (cron, hourly 08-21). Rolls DATA_DIR/usage_log.jsonl up into
# the "Juglans Usage" Notion DB (one row per day) so the operator can watch the
# pilot's engagement accumulate. Runs OUT-OF-BAND — never in the Streamlit client
# path — so the client UI is untouched. Idempotent + self-healing: each run
# re-aggregates the full log and upserts every day's row, so a missed run catches
# up on the next. No-ops cleanly if NOTION_API_KEY / JUGLANS_USAGE_DB_ID are unset.
#
# Install on the VPS:
#   sudo cp deploy/juglans-usage-sync.sh /srv/juglans/usage-sync.sh
#   sudo chmod +x /srv/juglans/usage-sync.sh
#   sudo chown paperclip:paperclip /srv/juglans/usage-sync.sh
#   # add JUGLANS_USAGE_DB_ID to /etc/juglans/env, then add to paperclip's crontab:
#   #   0 8-21 * * *  /srv/juglans/usage-sync.sh >> /srv/juglans/usage-sync.log 2>&1
set -euo pipefail

ENV_FILE=/etc/juglans/env
APP_DIR=/srv/juglans/app
PY=/srv/juglans/venv/bin/python

if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
fi
cd "$APP_DIR"
exec "$PY" tools/usage_notion_sync.py "$@"
