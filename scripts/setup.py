#!/usr/bin/env python3
"""Two-stage Debian setup. Preparation never needs a phone or activates AltServer."""
import argparse
import hashlib
import ipaddress
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HOME = Path('/opt/altserver-native')
ENV = Path('/etc/altserver-native.env')
TAG = 'v0.1.0'
RELEASE = f'https://github.com/hinatamaxxx/AltServer-Linux/releases/download/{TAG}'
NETMUX_URL = ('https://github.com/jkcoxson/netmuxd/releases/download/v0.4.3/'
              'netmuxd-x86_64-unknown-linux-gnu.tar.gz')
NETMUX_SHA = '85b6598284fc639f2a282584461d05e2090b79bdf3ec949d2a5e5d3dc655dde4'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def download(url, target):
    with urllib.request.urlopen(url, timeout=60) as response, target.open('wb') as dest:
        shutil.copyfileobj(response, dest)


def verify(path, digest):
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Invalid SHA-256 manifest')
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f'Checksum mismatch: {path.name}')


def atomic_write(path, content, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validated_device(host, udid, mac, fallback):
    def ipv4(value):
        address = ipaddress.IPv4Address(value)
        if address.is_unspecified or address.is_loopback or address.is_multicast or int(address) == 0xffffffff:
            raise ValueError('Use a unicast LAN IPv4 address')
        return str(address)
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{8}-[0-9a-fA-F]{16})', udid):
        raise ValueError('Invalid iPhone UDID')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', mac):
        raise ValueError('Invalid iPhone Wi-Fi MAC address')
    return dict(ALTSERVER_HOST_IP=ipv4(host), IPHONE_UDID=udid,
                IPHONE_WIFI_MAC=mac.lower(), IPHONE_FALLBACK_IP=ipv4(fallback) if fallback else '')


def preflight():
    if os.geteuid() != 0:
        raise ValueError('Run with sudo: sudo sh install.sh --prepare')
    distro = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if distro.get('ID', '').strip('"') != 'debian' or distro.get('VERSION_ID', '').strip('"') not in ('12', '13'):
        raise ValueError('This setup supports Debian 12/13 with systemd')
    if platform.machine() != 'x86_64':
        raise ValueError('This release provides an amd64 setup only')
    if not Path('/run/systemd/system').is_dir():
        raise ValueError('Run setup on a Debian systemd host, not inside a container')


def prepare():
    # Existing installs must not lose their configuration, binaries or identity.
    if ENV.exists() or (HOME / 'bin/AltServer').exists():
        raise ValueError('Existing installation detected; see docs/setup.md before migrating')
    packages = ['ca-certificates', 'curl', 'avahi-daemon', 'avahi-utils',
                'libavahi-compat-libdnssd1', 'usbmuxd', 'libimobiledevice-utils',
                'iproute2', 'util-linux', 'python3']
    if not shutil.which('docker'):
        packages.append('docker.io')
    run('apt-get', 'update')
    run('apt-get', 'install', '-y', *packages,
        env=dict(os.environ, DEBIAN_FRONTEND='noninteractive'))
    run('systemctl', 'enable', '--now', 'docker.service', 'avahi-daemon.service')
    # Stage everything before creating the prepared installation directory.
    with tempfile.TemporaryDirectory(prefix='altserver-setup-') as tmp:
        stage = Path(tmp)
        alt = stage / 'AltServer-x86_64'
        sums = stage / 'SHA256SUMS'
        bundled = ROOT / 'dist/AltServer-x86_64'
        if bundled.is_file():
            shutil.copy2(bundled, alt)
            shutil.copy2(ROOT / 'dist/SHA256SUMS', sums)
        else:
            download(RELEASE + '/AltServer-x86_64', alt)
            download(RELEASE + '/SHA256SUMS', sums)
        matches = [line.split()[0] for line in sums.read_text().splitlines()
                   if len(line.split()) == 2 and line.split()[1].lstrip('*') == alt.name]
        if len(matches) != 1:
            raise ValueError('Release manifest has no unique AltServer checksum')
        verify(alt, matches[0])
        archive = stage / 'netmuxd.tar.gz'
        download(NETMUX_URL, archive)
        verify(archive, NETMUX_SHA)
        with tarfile.open(archive) as tar:
            members = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == 'netmuxd']
            if len(members) != 1:
                raise ValueError('Unexpected netmuxd archive')
            # Extract only the expected regular binary; never archive paths/links.
            with tar.extractfile(members[0]) as src, (stage / 'netmuxd').open('wb') as dst:
                shutil.copyfileobj(src, dst)
        for binary in (alt, stage / 'netmuxd'):
            binary.chmod(0o755)
            run(str(binary), '--help', stdout=subprocess.DEVNULL, timeout=15)
        run('docker', 'pull', 'dadoum/anisette-v3-server:latest')
        # Record the immutable digest actually pulled; later starts never track latest.
        import json
        image = json.loads(output('docker', 'image', 'inspect', 'dadoum/anisette-v3-server:latest'))[0]
        digests = [v for v in image.get('RepoDigests', []) if v.startswith('dadoum/anisette-v3-server@sha256:')]
        if not digests:
            raise ValueError('No immutable anisette image digest found')
        HOME.mkdir(parents=True, exist_ok=True)
        (HOME / 'logs').mkdir(exist_ok=True)
        atomic_write(HOME / 'bin/AltServer', alt.read_bytes(), 0o755)
        atomic_write(HOME / 'bin/netmuxd', (stage / 'netmuxd').read_bytes(), 0o755)
        atomic_write(HOME / 'anisette-image', (digests[0] + '\n').encode())
    print('Prepared. No iPhone required; AltServer has not been activated.')
    print('Later: connect and trust one iPhone by USB, then sudo sh install.sh --configure')


def configure():
    if ENV.exists():
        raise ValueError('Existing configuration retained; automatic overwrite is disabled')
    for path in ('bin/AltServer', 'bin/netmuxd', 'anisette-image'):
        if not (HOME / path).is_file():
            raise ValueError('Run --prepare first')
    host = os.environ.get('ALTSERVER_HOST_IP', '')
    if not host:
        import json
        routes = json.loads(output('ip', '-j', 'route', 'get', '1.1.1.1'))
        host = routes[0].get('prefsrc', '')
    udid, mac = os.environ.get('IPHONE_UDID', ''), os.environ.get('IPHONE_WIFI_MAC', '')
    if not udid or not mac:
        run('systemctl', 'start', 'usbmuxd.service')
        phones = output('idevice_id', '-l').splitlines()
        if len(phones) != 1:
            raise ValueError('Connect exactly one iPhone by USB and tap Trust, then rerun --configure')
        udid = phones[0]
        run('idevicepair', '-u', udid, 'validate', stdout=subprocess.DEVNULL)
        mac = output('ideviceinfo', '-u', udid, '-k', 'WiFiAddress')
    values = validated_device(host, udid, mac, os.environ.get('IPHONE_FALLBACK_IP', ''))
    if not (Path('/var/lib/lockdown') / (udid + '.plist')).is_file():
        raise ValueError('The configured iPhone has no local pairing record; pair it by USB first')
    image = (HOME / 'anisette-image').read_text().strip()
    if not re.fullmatch(r'dadoum/anisette-v3-server@sha256:[0-9a-f]{64}', image):
        raise ValueError('Invalid prepared anisette image digest')
    values.update(ALTSERVER_HOME=str(HOME), ALTSERVER_BIN=str(HOME / 'bin/AltServer'),
                  NETMUXD_BIN=str(HOME / 'bin/netmuxd'), USBMUXD_SOCKET_ADDRESS='127.0.0.1:27015',
                  NETMUXD_REGISTER_MODE='api', ALTSERVER_NO_SUBSCRIBE='1',
                  ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969', ANISETTE_URL='http://127.0.0.1:6969/',
                  ANISETTE_DOCKER_IMAGE=image, ANISETTE_STATE_DIR='/var/lib/altserver-native/anisette')
    atomic_write(ENV, ''.join(f'{k}={shlex.quote(v)}\n' for k, v in values.items()).encode())
    env = dict(os.environ, ENV_FILE=str(ENV))
    run('sh', str(ROOT / 'scripts/install-helper-scripts.sh'), env=env)
    run('sh', str(ROOT / 'scripts/install-systemd-units.sh'), env=env)
    run('systemctl', 'start', 'altserver-anisette-docker.service', 'altserver-native-netmuxd.service',
        'altserver-netmux-compat.service', 'iphone-mobdev-address.service', 'iphone-mobdev-service.service',
        'altserver-native.service', 'altserver-native-healthcheck.timer')
    print('Configured. Run sudo /usr/local/sbin/altserver-native-healthcheck to inspect readiness.')
    print('iPhone refresh and Apple sign-in still require verification in AltStore.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--prepare', action='store_true', help='install dependencies and stage binaries (default)')
    group.add_argument('--configure', action='store_true', help='pairing must already exist; activate services')
    args = parser.parse_args()
    preflight()
    configure() if args.configure else prepare()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Avoid printing subprocess arguments, which can contain device identifiers.
        message = str(error) if isinstance(error, ValueError) else type(error).__name__
        raise SystemExit('Setup stopped: ' + message)
