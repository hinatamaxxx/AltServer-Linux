#!/bin/sh
# Disposable Debian container only. Real packages/downloads; systemd calls recorded,
# never executed. Docker socket is used only for pull/image-inspect during prepare.
set -eu
export DEBIAN_FRONTEND=noninteractive
printf '#!/bin/sh\nexit 101\n' >/usr/sbin/policy-rc.d
chmod +x /usr/sbin/policy-rc.d
apt-get update
apt-get install -y python3 systemd docker.io ca-certificates curl avahi-daemon avahi-utils \
  libavahi-compat-libdnssd1 usbmuxd libimobiledevice-utils iproute2 util-linux
mkdir -p /run/systemd/system /work
cat >/usr/local/bin/systemctl <<'SH'
#!/bin/sh
printf '%s\n' "$*" >>/work/systemctl-calls
SH
chmod +x /usr/local/bin/systemctl
tar -xzf /source/dist/AltServer-Linux-amd64-setup.tar.gz -C /work
cd /work/AltServer-Linux
sh install.sh --prepare
sh install.sh --prepare
test ! -e /etc/altserver-native.env
test ! -e /etc/systemd/system/altserver-native.service
test -x /opt/altserver-native/bin/AltServer
test -x /opt/altserver-native/bin/netmuxd
! grep -q altserver /work/systemctl-calls
# Only synthetic device identity/pairing file; no iPhone is contacted.
export ALTSERVER_HOST_IP=192.0.2.1
export IPHONE_UDID=0000000000000000000000000000000000000000
export IPHONE_WIFI_MAC=02:00:00:00:00:01
mkdir -p /var/lib/lockdown
printf 'synthetic-test-fixture\n' >"/var/lib/lockdown/$IPHONE_UDID.plist"
sh install.sh --configure
sh install.sh --configure
test "$(stat -c %a /etc/altserver-native.env)" = 600
grep -q 'NETMUXD_REGISTER_MODE=api' /etc/altserver-native.env
grep -q 'sha256:' /etc/altserver-native.env
/usr/bin/systemd-analyze verify /etc/systemd/system/altserver-*.service \
  /etc/systemd/system/altserver-*.timer /etc/systemd/system/iphone-mobdev-*.service
before=$(sha256sum /etc/altserver-native.env)
if sh install.sh --prepare; then
  echo 'Existing installation was not protected' >&2; exit 1
fi
test "$before" = "$(sha256sum /etc/altserver-native.env)"
echo 'Extracted installer: real Debian packages, downloads, checksums, configuration and unit syntax passed.'
echo 'Service start/stop was simulated; no device or physical-host lifecycle tested.'
