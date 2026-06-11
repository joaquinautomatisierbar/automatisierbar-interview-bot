#!/usr/bin/env bash
# Install + load the paperclip orchestrator AND the Telegram listener as launchd LaunchAgents.
# Run once. After install, both auto-start on login and restart on crash.

set -euo pipefail

PLIST_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/.paperclip/logs"

mkdir -p "$LOG_DIR"
mkdir -p "$AGENTS_DIR"

for PLIST_NAME in "com.automatisierbar.paperclip-orchestrator.plist" \
                  "com.automatisierbar.telegram-listener.plist"; do
  SRC="$PLIST_DIR/$PLIST_NAME"
  DST="$AGENTS_DIR/$PLIST_NAME"

  if [[ ! -f "$SRC" ]]; then
    echo "missing source plist: $SRC — skipping"
    continue
  fi

  # Unload if already loaded (no-op if not loaded)
  launchctl unload "$DST" 2>/dev/null || true

  # Symlink so edits to the source plist apply on next reload
  ln -sf "$SRC" "$DST"

  launchctl load -w "$DST"
  echo "Loaded: $DST"
done

echo
echo "Logs:"
echo "  $LOG_DIR/orchestrator.log + .err"
echo "  $LOG_DIR/telegram-listener.log + .err"
echo
echo "Verify with:"
echo "  launchctl list | grep automatisierbar"
echo "  tail -f $LOG_DIR/orchestrator.log"
echo "  tail -f $LOG_DIR/telegram-listener.log"
echo
echo "Stop one:"
echo "  launchctl unload \$HOME/Library/LaunchAgents/com.automatisierbar.<name>.plist"
echo
echo "Stop both:"
echo "  for p in \$HOME/Library/LaunchAgents/com.automatisierbar.*.plist; do launchctl unload \$p; done"
