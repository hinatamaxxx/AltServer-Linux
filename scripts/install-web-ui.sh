#!/bin/sh
# Optional component: never changes AltServer, pairing or Anisette configuration.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
case "${1:-}" in ''|--tailscale) ;; *) echo 'Usage: sudo sh scripts/install-web-ui.sh [--tailscale]' >&2; exit 1 ;; esac
[ "$(id -u)" = 0 ] || { echo 'Run with sudo' >&2; exit 1; }
[ -f /etc/altserver-native.env ] && [ -x /usr/local/sbin/altserver-native-probe ] || {
  echo 'Configure AltServer first (install.sh --configure).' >&2; exit 1;
}
command -v python3 >/dev/null
if [ "${1:-}" = --tailscale ]; then
  command -v tailscale >/dev/null
fi
[ -d /run/systemd/system ] || { echo 'systemd is required' >&2; exit 1; }
install -d -m 755 /opt/altserver-native/web /opt/altserver-native/web/static
install -m 644 "$root/web/server.py" /opt/altserver-native/web/server.py
install -m 644 "$root/web/passkeys.py" /opt/altserver-native/web/passkeys.py
install -m 644 "$root/web/requirements.txt" /opt/altserver-native/web/requirements.txt
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv
python3 -m venv /opt/altserver-native/web-venv
/opt/altserver-native/web-venv/bin/pip install -r /opt/altserver-native/web/requirements.txt
install -m 644 "$root/web/static/"* /opt/altserver-native/web/static/
install -d -m 700 /var/lib/altserver-webui
if [ ! -f /etc/altserver-webui.env ]; then
  umask 077
  printf 'WEBUI_LISTEN=127.0.0.1\nWEBUI_PORT=8787\n' >/etc/altserver-webui.env
fi
if [ "${1:-}" = --tailscale ]; then
  python3 "$root/scripts/configure-web-https.py"
fi
install -m 644 "$root/config/altserver-webui.service" /etc/systemd/system/altserver-webui.service
systemctl daemon-reload
systemctl enable --now altserver-webui.service
# Also loads updated files when an existing console is upgraded.
systemctl restart altserver-webui.service
echo 'Web UI installed. See the HTTPS URL above when using --tailscale.'
echo 'Open the HTTPS URL to enroll your passkey. See docs/web-ui.md for details.'
