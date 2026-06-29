#!/usr/bin/env bash
# Idempotent one-shot deploy of the Cockpit booking app on the VPS (runs as root).
# Survives browser-terminal disconnects when launched detached:
#   curl -fsSL -o /root/cockpit_deploy.sh \
#     https://raw.githubusercontent.com/joaquinautomatisierbar/automatisierbar-interview-bot/feat/cockpit-booking/deploy/bootstrap.sh \
#   && setsid bash /root/cockpit_deploy.sh >/root/cockpit_deploy.log 2>&1 </dev/null & echo "started pid $!"
# Then: tail -n 40 /root/cockpit_deploy.log
set -e
REPO=https://github.com/joaquinautomatisierbar/automatisierbar-interview-bot.git
BRANCH=feat/cockpit-booking

echo "[1/7] repo"
mkdir -p /srv/cockpit
# Allow root to operate on the repo even if a prior run chowned it to paperclip.
git config --global --add safe.directory /srv/cockpit/app || true
if [ -d /srv/cockpit/app/.git ]; then
  git -C /srv/cockpit/app fetch -q origin "$BRANCH"
  git -C /srv/cockpit/app checkout -q -B "$BRANCH" origin/"$BRANCH"
else
  rm -rf /srv/cockpit/app
  git clone -q -b "$BRANCH" "$REPO" /srv/cockpit/app
fi

echo "[2/7] venv + dependencies (this is the slow part)"
python3 -m venv /srv/cockpit/venv
/srv/cockpit/venv/bin/pip install -q --upgrade pip
/srv/cockpit/venv/bin/pip install -q -r /srv/cockpit/app/requirements.txt

echo "[3/7] env file"
mkdir -p /etc/cockpit
[ -f /etc/cockpit/env ] || printf 'PORT=8082\nFLASK_SECRET_KEY=%s\n' \
  "$(python3 -c 'import secrets;print(secrets.token_hex(24))')" > /etc/cockpit/env
chmod 600 /etc/cockpit/env

echo "[4/7] ownership"
chown -R paperclip:paperclip /srv/cockpit

echo "[5/7] systemd unit"
cat > /etc/systemd/system/cockpit.service <<'UNITEOF'
[Unit]
Description=Automatisierbar Cockpit (booking)
After=network.target
[Service]
Type=simple
User=paperclip
WorkingDirectory=/srv/cockpit/app
EnvironmentFile=/etc/cockpit/env
ExecStart=/srv/cockpit/venv/bin/gunicorn api:app --bind 127.0.0.1:8082 --workers 2 --timeout 120
Restart=on-failure
RestartSec=3
[Install]
WantedBy=multi-user.target
UNITEOF

echo "[6/7] start service + caddy site"
systemctl daemon-reload
systemctl enable --now cockpit || true
sleep 3
if ! grep -q "cockpit.automatisierbar.ch" /etc/caddy/Caddyfile; then
  cat >> /etc/caddy/Caddyfile <<'CADDYEOF'

cockpit.automatisierbar.ch {
	encode zstd gzip
	reverse_proxy 127.0.0.1:8082
}
CADDYEOF
fi
systemctl reload caddy || true

echo "[7/7] verify"
sleep 2
curl -s -o /dev/null -w "  local app /health: %{http_code}\n" http://127.0.0.1:8082/health || true
echo -n "  cockpit service: "; systemctl is-active cockpit || true
systemctl is-active --quiet cockpit || journalctl -u cockpit -n 25 --no-pager || true
echo "==== BOOTSTRAP DONE -> https://cockpit.automatisierbar.ch/book ===="
