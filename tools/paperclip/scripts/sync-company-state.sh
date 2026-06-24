#!/usr/bin/env bash
# sync-company-state.sh — pull live company state from Notion into
# references/company-state/*.md. Idempotent + overwriting.
#
# Local usage (operator MacBook):
#   bash tools/paperclip/scripts/sync-company-state.sh
#
# VPS usage (systemd ExecStart):
#   /usr/bin/python3 /home/paperclip/_context/tools/sync_company_state.py
#   (this wrapper is for local convenience + env-file loading)

set -euo pipefail

# Resolve repo root regardless of cwd
if [[ -n "${PROJECT_ROOT:-}" ]]; then
  ROOT="${PROJECT_ROOT}"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
fi

cd "${ROOT}"

# Load .env if present (the python script also does this, but doing it here
# means downstream tools see the env vars too).
if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^[A-Z_][A-Z_0-9]*=' "${ROOT}/.env" | sed 's/[[:space:]]*$//')
  set +a
fi

echo "[sync-company-state] running from ${ROOT}"
python3 tools/sync_company_state.py "$@"
