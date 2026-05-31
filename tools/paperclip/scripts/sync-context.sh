#!/usr/bin/env bash
# sync-context.sh — Mount the firm's canonical reference files into ~/_context/
# so every paperclip agent on this host can read them.
#
# Usage:
#   bash tools/paperclip/scripts/sync-context.sh                  # local sync (MacBook → ~/_context/)
#   bash tools/paperclip/scripts/sync-context.sh --push-to-vps    # rsync to VPS over SSH
#
# Run from anywhere. Idempotent — safe to run repeatedly. Existing files in
# ~/_context/ that no longer exist in the source are deleted (--delete).

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview}"
DEST="${HOME}/_context"
VPS_USER="paperclip"
VPS_HOST="72.61.106.8"
VPS_KEY="${HOME}/.ssh/paperclip_vps"
VPS_DEST="/home/${VPS_USER}/_context"

# Files / directories to mount. Keep this list small + curated. The full project
# tree is NOT mirrored — only the canonical reference assets.
MOUNT_PATHS=(
  "CLAUDE.md"
  "connections.md"
  "decisions/log.md"
  "references/business-context.md"
  "references/library"
  "references/operator-principles.md"
  "prompts/linkedin_brief_synthesis.md"
  "prompts/linkedin_voice.md"
  "Automatisierbar_Brand_Guide EXTERN copy.pdf"
  "automatisierbar_brandguide_02_prozess copy.pdf"
  "tools/visual_process_diagram.py"
  # ---- 2026-06-01: source code mount for Internal Planner + Test Data Generator ----
  # The two AI OS - OPERATIONS agents (Internal Planner, Test Data Generator) need
  # to read live source to plan / infer input shapes. Add the source surfaces they
  # operate on. Excluded automatically by .gitignore / rsync: .tmp, .venv,
  # node_modules, __pycache__, .pyc, .DS_Store.
  "api.py"
  "claude_client.py"
  "static/index.html"
  "tools/file_extract.py"
  "tools/generate_pdf.py"
  "tools/linkedin_brief.py"
  "tools/notion_session.py"
  "tools/paperclip"
  "tools/extract_pdf_text.py"
  "prompts/transcript_classification.md"
  "references"
)

PUSH_VPS=0
if [[ "${1:-}" == "--push-to-vps" ]]; then
  PUSH_VPS=1
fi

echo "[sync-context] source: ${PROJECT_ROOT}"
echo "[sync-context] dest:   ${DEST}"
mkdir -p "${DEST}"

# Local sync — rsync each path under ~/_context/ preserving relative structure.
for p in "${MOUNT_PATHS[@]}"; do
  src="${PROJECT_ROOT}/${p}"
  if [[ ! -e "${src}" ]]; then
    echo "  SKIP ${p} (source missing)"
    continue
  fi
  parent_dir="${DEST}/$(dirname "${p}")"
  mkdir -p "${parent_dir}"
  rsync -a --delete \
    --exclude '.git' --exclude '.tmp' --exclude '.venv' \
    --exclude 'node_modules' --exclude '__pycache__' \
    --exclude '*.pyc' --exclude '.DS_Store' \
    --exclude 'orchestrator-state.json' --exclude '.pipeline-events.log' \
    "${src}" "${parent_dir}/" 2>/dev/null || \
    rsync -a \
    --exclude '.git' --exclude '.tmp' --exclude '.venv' \
    --exclude 'node_modules' --exclude '__pycache__' \
    --exclude '*.pyc' --exclude '.DS_Store' \
    "${src}" "${parent_dir}/"
  echo "  OK   ${p}"
done

echo "[sync-context] local sync done. ${DEST} contents:"
ls -la "${DEST}" | head -20

# Optionally push to VPS.
if [[ "${PUSH_VPS}" -eq 1 ]]; then
  if [[ ! -f "${VPS_KEY}" ]]; then
    echo "[sync-context] ERROR: SSH key ${VPS_KEY} not found — cannot push to VPS"
    exit 1
  fi
  echo "[sync-context] pushing to ${VPS_USER}@${VPS_HOST}:${VPS_DEST}..."
  ssh -i "${VPS_KEY}" "${VPS_USER}@${VPS_HOST}" "mkdir -p ${VPS_DEST}"
  rsync -avz --delete -e "ssh -i ${VPS_KEY}" \
    "${DEST}/" "${VPS_USER}@${VPS_HOST}:${VPS_DEST}/"
  echo "[sync-context] VPS push done."
fi
