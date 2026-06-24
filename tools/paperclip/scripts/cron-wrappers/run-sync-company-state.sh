#!/usr/bin/env bash
# Cron wrapper: refresh references/company-state/*.md snapshot from Notion + git.
# Runs twice daily on VPS via crontab. Idempotent.

set -e

cd "$(dirname "$0")/../../../.." # repo root

ENV_FILE_VPS="/home/paperclip/secrets/sync-company-state.env"
ENV_FILE_LOCAL=".env"

if [[ -f "${ENV_FILE_VPS}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE_VPS}"
  set +a
elif [[ -f "${ENV_FILE_LOCAL}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^[A-Z_][A-Z_0-9]*=' "${ENV_FILE_LOCAL}" | sed 's/[[:space:]]*$//')
  set +a
else
  echo "ERROR: no env file found at ${ENV_FILE_VPS} or ${ENV_FILE_LOCAL}" >&2
  exit 2
fi

echo "[run-sync-company-state] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting"
exec /usr/bin/python3 tools/sync_company_state.py
