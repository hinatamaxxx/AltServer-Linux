#!/bin/sh
# Optional component: never changes AltServer, pairing or Anisette configuration.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
[ "$(id -u)" = 0 ] || { echo 'Run with sudo' >&2; exit 1; }
[ -f /etc/altserver-native.env ] && [ -x /usr/local/sbin/altserver-native-probe ] || {
  echo 'Configure AltServer first (install.sh --configure).' >&2; exit 1;
}
command -v python3 >/dev/null
[ -d /run/systemd/system ] || { echo 'systemd is required' >&2; exit 1; }
install -d -m 755 /opt/altserver-native/web /opt/altserver-native/web/static
install -m 644 "$root/web/server.py" /opt/altserver-native/web/server.py
install -m 644 "$root/web/static/"* /opt/altserver-native/web/static/
install -d -m 700 /var/lib/altserver-webui
if [ ! -f /etc/altserver-webui.env ]; then
  umask 077
  printf 'WEBUI_LISTEN=127.0.0.1\nWEBUI_PORT=8787\n' >/etc/altserver-webui.env
fi
install -m 644 "$root/config/altserver-webui.service" /etc/systemd/system/altserver-webui.service
systemctl daemon-reload
systemctl enable --now altserver-webui.service
# Also loads updated files when an existing console is upgraded.
systemctl restart altserver-webui.service
echo 'Web UI installed. Default: http://127.0.0.1:8787'
echo 'Read docs/web-ui.md for remote access and the access-key command.'
