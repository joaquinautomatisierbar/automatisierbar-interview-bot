#!/usr/bin/env bash
# install-linkedin-brief-vps.sh — install systemd timers on the paperclip VPS
# for the weekly LinkedIn brief (Monday skeleton + Friday synthesis) AND the
# twice-daily company-state snapshot refresh.
#
# Operator-side: run from local repo. SSHes to VPS, writes unit files via sudo,
# enables timers, fires one manual run of each to verify.
#
# Idempotent: re-running overwrites unit files with current versions.
#
# Usage:
#   bash tools/paperclip/scripts/install-linkedin-brief-vps.sh
#
# Pre-req — write the env files on VPS first (one-time):
#   ssh -i ~/.ssh/paperclip_vps paperclip@72.61.106.8
#   sudo tee /etc/paperclip/secrets/linkedin-brief.env <<EOF
#     ANTHROPIC_API_KEY=...
#     NOTION_API_KEY=...
#     NOTION_BRIEFS_DB_ID=...
#     NOTION_LEADS_DB_ID=...
#     NOTION_LINKEDIN_DB_ID=...
#     NOTION_CALL_ANALYTICS_DB_ID=...
#     NOTION_WEEKLY_REPORTS_DB_ID=...
#     N8N_API_KEY=...
#     N8N_BASE_URL=https://oojoaquin.app.n8n.cloud
#     OPERATOR_TELEGRAM_BOT_TOKEN=...
#     OPERATOR_TELEGRAM_CHAT_ID=...
#     BRIEF_PERSON=Joaquin
#   EOF
#   sudo chmod 600 /etc/paperclip/secrets/linkedin-brief.env
# Same for /etc/paperclip/secrets/sync-company-state.env (subset of above keys).

set -euo pipefail

VPS_USER="paperclip"
VPS_HOST="72.61.106.8"
VPS_KEY="${HOME}/.ssh/paperclip_vps"
CONTEXT="/home/${VPS_USER}/_context"

log() { echo "[install-brief] $*" >&2; }

vps() { ssh -i "${VPS_KEY}" "${VPS_USER}@${VPS_HOST}" "$@"; }
vps_sudo() { ssh -i "${VPS_KEY}" "${VPS_USER}@${VPS_HOST}" "sudo $*"; }

log "checking VPS reachability..."
vps "echo 'ok' && python3 --version && which systemctl" >&2

log "ensuring secrets dir exists..."
vps_sudo "mkdir -p /etc/paperclip/secrets"

log "checking env files exist..."
if ! vps "test -f /etc/paperclip/secrets/linkedin-brief.env"; then
  cat >&2 <<EOF
ERROR: /etc/paperclip/secrets/linkedin-brief.env does NOT exist on VPS.
Per the file header, create it manually (one-time) before running this installer.
EOF
  exit 2
fi
if ! vps "test -f /etc/paperclip/secrets/sync-company-state.env"; then
  log "WARN: /etc/paperclip/secrets/sync-company-state.env not found — using linkedin-brief.env as fallback (it's a superset)"
  vps_sudo "cp /etc/paperclip/secrets/linkedin-brief.env /etc/paperclip/secrets/sync-company-state.env"
fi
vps_sudo "chmod 600 /etc/paperclip/secrets/linkedin-brief.env /etc/paperclip/secrets/sync-company-state.env"

# ---------------------------------------------------------------------------
# Unit file: linkedin-brief-friday
# ---------------------------------------------------------------------------
cat > /tmp/linkedin-brief-friday.service <<EOF
[Unit]
Description=Weekly LinkedIn brief — synthesis (Friday)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${VPS_USER}
WorkingDirectory=${CONTEXT}
EnvironmentFile=/etc/paperclip/secrets/linkedin-brief.env
ExecStart=/usr/bin/python3 ${CONTEXT}/tools/linkedin_brief.py
StandardOutput=append:/var/log/paperclip/linkedin-brief.log
StandardError=append:/var/log/paperclip/linkedin-brief.log
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/linkedin-brief-friday.timer <<EOF
[Unit]
Description=Trigger weekly LinkedIn brief synthesis on Friday 16:00 Zurich
After=network-online.target

[Timer]
OnCalendar=Fri 16:00 Europe/Zurich
Persistent=true
Unit=linkedin-brief-friday.service

[Install]
WantedBy=timers.target
EOF

# ---------------------------------------------------------------------------
# Unit file: linkedin-brief-monday (skeleton creation)
# ---------------------------------------------------------------------------
cat > /tmp/linkedin-brief-monday.service <<EOF
[Unit]
Description=Weekly LinkedIn brief — skeleton creation (Monday)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${VPS_USER}
WorkingDirectory=${CONTEXT}
EnvironmentFile=/etc/paperclip/secrets/linkedin-brief.env
ExecStart=/usr/bin/python3 ${CONTEXT}/tools/linkedin_brief.py --create-page
StandardOutput=append:/var/log/paperclip/linkedin-brief.log
StandardError=append:/var/log/paperclip/linkedin-brief.log
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/linkedin-brief-monday.timer <<EOF
[Unit]
Description=Trigger Monday skeleton creation for the LinkedIn brief
After=network-online.target

[Timer]
OnCalendar=Mon 09:00 Europe/Zurich
Persistent=true
Unit=linkedin-brief-monday.service

[Install]
WantedBy=timers.target
EOF

# ---------------------------------------------------------------------------
# Unit file: sync-company-state (snapshot refresh 2x daily)
# ---------------------------------------------------------------------------
cat > /tmp/sync-company-state.service <<EOF
[Unit]
Description=Refresh references/company-state/*.md snapshot from Notion + git
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${VPS_USER}
WorkingDirectory=${CONTEXT}
EnvironmentFile=/etc/paperclip/secrets/sync-company-state.env
ExecStart=/usr/bin/python3 ${CONTEXT}/tools/sync_company_state.py
StandardOutput=append:/var/log/paperclip/sync-company-state.log
StandardError=append:/var/log/paperclip/sync-company-state.log
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/sync-company-state.timer <<EOF
[Unit]
Description=Refresh company-state snapshot twice daily
After=network-online.target

[Timer]
OnCalendar=*-*-* 06:00:00 Europe/Zurich
OnCalendar=*-*-* 14:00:00 Europe/Zurich
Persistent=true
Unit=sync-company-state.service

[Install]
WantedBy=timers.target
EOF

# ---------------------------------------------------------------------------
# Upload + install
# ---------------------------------------------------------------------------
log "uploading unit files to VPS /tmp..."
scp -i "${VPS_KEY}" \
  /tmp/linkedin-brief-friday.service \
  /tmp/linkedin-brief-friday.timer \
  /tmp/linkedin-brief-monday.service \
  /tmp/linkedin-brief-monday.timer \
  /tmp/sync-company-state.service \
  /tmp/sync-company-state.timer \
  "${VPS_USER}@${VPS_HOST}:/tmp/" >&2

log "moving into /etc/systemd/system/ and ensuring log dir..."
vps_sudo "mkdir -p /var/log/paperclip && chown ${VPS_USER}:${VPS_USER} /var/log/paperclip"
vps_sudo "mv /tmp/linkedin-brief-friday.service /tmp/linkedin-brief-friday.timer /tmp/linkedin-brief-monday.service /tmp/linkedin-brief-monday.timer /tmp/sync-company-state.service /tmp/sync-company-state.timer /etc/systemd/system/"
vps_sudo "systemctl daemon-reload"

log "enabling timers..."
vps_sudo "systemctl enable --now linkedin-brief-friday.timer linkedin-brief-monday.timer sync-company-state.timer"

log "timer status:"
vps "systemctl list-timers --all | grep -E 'linkedin-brief|sync-company-state' || true"

log ""
log "Firing one manual run of sync-company-state.service to verify..."
vps_sudo "systemctl start sync-company-state.service"
sleep 4
log "  service result:"
vps "systemctl status sync-company-state.service --no-pager | head -15"
log "  recent log lines:"
vps "tail -20 /var/log/paperclip/sync-company-state.log 2>/dev/null || echo '(no log lines yet)'"
log ""
log "Done. The Friday + Monday brief timers are enabled but won't fire until the next Fri/Mon."
log "To dry-run the Friday synthesis now: vps_sudo systemctl start linkedin-brief-friday.service"
log "To disable local macOS launchd after VPS-validated:"
log "  launchctl unload ~/Library/LaunchAgents/com.automatisierbar.linkedin-brief-monday.plist 2>/dev/null || true"
log "  launchctl unload ~/Library/LaunchAgents/com.automatisierbar.linkedin-brief-friday.plist 2>/dev/null || true"
