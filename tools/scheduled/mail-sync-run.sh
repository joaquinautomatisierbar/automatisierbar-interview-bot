#!/usr/bin/env bash
# Manual mail-sync run helper (backfill / dry-run / debug). Parses /etc/cockpit/env the SAME
# line-by-line way the cron wrapper does — the env file holds values with spaces/commas
# (signatures, names) so it CANNOT be `source`d — then runs sync.py with whatever args you pass.
#
#   sudo -u paperclip bash tools/scheduled/mail-sync-run.sh --mailbox all --dry-run --verbose
#   sudo -u paperclip bash tools/scheduled/mail-sync-run.sh --mailbox joaquin --since-days 14
set -u
cd /srv/cockpit/app || exit 1
ENV_FILE="${MAIL_SYNC_ENV_FILE:-/etc/cockpit/env}"
if [ -f "$ENV_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|\#*) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    key="$(echo "$key" | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')"
    case "$val" in \"*\") val="${val#\"}"; val="${val%\"}" ;; \'*\') val="${val#\'}"; val="${val%\'}" ;; esac
    [ -n "$key" ] && export "$key=$val"
  done < "$ENV_FILE"
fi
PY=/srv/cockpit/venv/bin/python
[ -x "$PY" ] || PY=python3
exec "$PY" tools/mail_sync/sync.py "$@"
