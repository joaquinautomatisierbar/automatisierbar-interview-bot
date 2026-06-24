#!/usr/bin/env bash
# Cron wrapper: weekly LinkedIn brief.
#
# Modes:
#   run-linkedin-brief.sh                  # Friday synthesis (no args)
#   run-linkedin-brief.sh --create-page    # Monday skeleton creation
#
# Reads env vars from /home/paperclip/secrets/linkedin-brief.env on VPS or
# from local repo .env if invoked locally for testing.

set -e

cd "$(dirname "$0")/../../../.." # repo root

ENV_FILE_VPS="/home/paperclip/secrets/linkedin-brief.env"
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

ARGS=()
if [[ "${1:-}" == "--create-page" ]]; then ARGS+=("--create-page"); fi

echo "[run-linkedin-brief] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting (args=${ARGS[*]:-synthesis})"
exec /usr/bin/python3 tools/linkedin_brief.py "${ARGS[@]}"
