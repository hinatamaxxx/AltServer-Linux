#!/usr/bin/env python3
"""Two-stage Debian setup. Preparation never needs a phone or activates AltServer."""
import argparse
import hashlib
import json
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
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
HOME = Path('/opt/altserver-native')
ENV = Path('/etc/altserver-native.env')
TAG = (ROOT / 'VERSION').read_text().strip()
if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', TAG):
    raise ValueError('Invalid setup VERSION')
RELEASE = f'https://github.com/hinatamaxxx/AltServer-Linux/releases/download/{TAG}'
NETMUX_LATEST = 'https://api.github.com/repos/jkcoxson/netmuxd/releases/latest'
NETMUX_ASSET = 'netmuxd-x86_64-unknown-linux-gnu.tar.gz'
# Local anisette: Apple's Windows iCloud runtime under Wine (anisette/icloud-wine).
ICLOUD_IMAGE_TAG = f'altserver-icloud-anisette:{TAG}'
ICLOUD_STATE = Path('/var/lib/altserver-native/icloud-local')
APPLE_DIR = HOME / 'icloud-local/apple'
APPLE_ROOT_URL = 'https://www.apple.com/appleca/AppleIncRootCertificate.cer'
APPLE_ROOT_SHA256 = 'b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024'
# The helper's native offsets are verified for these exact Apple binaries only.
APPLE_RUNTIME_SHA256 = {
    'Internet Services/iCloud_main.dll': '9e3af0c4cf50cc65554a9478aa7b381ff351373bdf034413a877f52912ff5010',
    'Apple Application Support/CoreADI.dll': '961539f222aa018ef5b32fc0c82fca6d3e2a70100c0037741530ee5324447f9b',
}
APPLE_RUNTIME_LIMIT = 1024 * 1024 * 1024


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


def latest_netmux_release():
    request = urllib.request.Request(NETMUX_LATEST, headers={
        'Accept': 'application/vnd.github+json', 'User-Agent': 'AltServer-Linux-setup/' + TAG})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError('netmuxd release metadata is too large')
    release = json.loads(data)
    if not isinstance(release, dict) or release.get('draft') is not False or release.get('prerelease') is not False:
        raise ValueError('No public stable netmuxd release found')
    version, assets = release.get('tag_name'), release.get('assets')
    if not isinstance(version, str) or not version or not isinstance(assets, list):
        raise ValueError('Invalid netmuxd release metadata')
    matches = [a for a in assets if isinstance(a, dict) and a.get('name') == NETMUX_ASSET]
    if len(matches) != 1:
        raise ValueError('Latest netmuxd release has no unique Linux amd64 asset')
    asset = matches[0]
    url = ('https://github.com/jkcoxson/netmuxd/releases/download/'
           + urllib.parse.quote(version, safe='') + '/' + NETMUX_ASSET)
    digest = asset.get('digest')
    if asset.get('browser_download_url') != url or not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Latest netmuxd asset has no valid upstream URL or SHA-256 digest')
    return dict(version=version, url=url, sha256=digest.removeprefix('sha256:'))


def verify_binary_version(path):
    actual = subprocess.check_output([str(path), '--version'], text=True, timeout=15).strip()
    if actual != f'AltServer-Linux {TAG}':
        raise ValueError('AltServer binary version does not match this setup')


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


def import_apple_runtime(archive):
    """Install Apple's runtime from scripts/windows/export-apple-runtime.ps1 output."""
    archive = Path(archive)
    if not archive.is_file():
        raise ValueError('Apple runtime archive not found')
    APPLE_DIR.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.apple-', dir=APPLE_DIR.parent))
    try:
        total = 0
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts
                if member.name.startswith('/') or '..' in parts or not parts or parts[0] != 'Apple':
                    raise ValueError('Unexpected path in Apple runtime archive')
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError('Apple runtime archive may contain only regular files')
                total += member.size
                if total > APPLE_RUNTIME_LIMIT:
                    raise ValueError('Apple runtime archive is too large')
                target = stage.joinpath(*parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, target.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                target.chmod(0o644)
        for name, digest in APPLE_RUNTIME_SHA256.items():
            if not (stage / name).is_file():
                raise ValueError('Apple runtime archive lacks ' + name)
            verify(stage / name, digest)
        certificate = stage / 'AppleIncRootCertificate.cer'
        download(APPLE_ROOT_URL, certificate)
        verify(certificate, APPLE_ROOT_SHA256)
        certificate.chmod(0o644)
        for directory in [stage, *(d for d in stage.rglob('*') if d.is_dir())]:
            directory.chmod(0o755)
        if APPLE_DIR.exists():
            previous = APPLE_DIR.with_name('apple.previous')
            if previous.exists():
                shutil.rmtree(previous)
            os.replace(APPLE_DIR, previous)
        os.replace(stage, APPLE_DIR)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print('Apple runtime installed. It contains no account data; Wine state is kept separately.')
    if ENV.exists():
        run('systemctl', 'restart', 'altserver-icloud-local.service')


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
        if not ENV.exists() and (HOME / 'setup-state.json').is_file():
            state = json.loads((HOME / 'setup-state.json').read_text())
            if state.get('version') == TAG and state.get('phase') == 'prepared' and all((HOME / p).is_file() for p in
                                                       ('bin/AltServer', 'bin/netmuxd', 'anisette-image')):
                print('Already prepared. Import the Apple runtime, connect/trust an iPhone, then use --configure.')
                return
        raise ValueError('Existing installation detected; see docs/setup.md before migrating')
    packages = ['ca-certificates', 'curl', 'avahi-daemon', 'avahi-utils',
                'libavahi-compat-libdnssd1', 'usbmuxd', 'libimobiledevice-utils',
                'iproute2', 'util-linux', 'python3', 'python3-srp', 'python3-cryptography']
    if not shutil.which('docker'):
        packages.append('docker.io')
    run('apt-get', 'update')
    run('apt-get', 'install', '-y', *packages,
        env=dict(os.environ, DEBIAN_FRONTEND='noninteractive'))
    run('systemctl', 'enable', '--now', 'docker.service', 'avahi-daemon.service')
    # Resolve once per preparation, so the URL and digest refer to the same release.
    netmux = latest_netmux_release()
    print('Preparing netmuxd ' + netmux['version'] + ' (latest official release).')
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
        download(netmux['url'], archive)
        verify(archive, netmux['sha256'])
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
        verify_binary_version(alt)
        run('docker', 'build', '-t', ICLOUD_IMAGE_TAG, str(ROOT / 'anisette/icloud-wine'))
        # Record the immutable image ID actually built; later starts never rebuild or retag.
        image = output('docker', 'image', 'inspect', '--format', '{{.Id}}', ICLOUD_IMAGE_TAG)
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
            raise ValueError('No immutable anisette image ID found')
        HOME.mkdir(parents=True, exist_ok=True)
        (HOME / 'logs').mkdir(exist_ok=True)
        atomic_write(HOME / 'bin/AltServer', alt.read_bytes(), 0o755)
        atomic_write(HOME / 'bin/netmuxd', (stage / 'netmuxd').read_bytes(), 0o755)
        atomic_write(HOME / 'anisette-image', (image + '\n').encode())
        atomic_write(HOME / 'setup-state.json', json.dumps(dict(version=TAG, phase='prepared', netmuxd=netmux)).encode())
    print('Prepared. No iPhone required; AltServer has not been activated.')
    print('Next: sudo sh install.sh --import-apple-runtime apple-runtime.tar.gz (see docs/setup.md)')
    print('Then connect and trust one iPhone by USB, and run sudo sh install.sh --configure')


def configure():
    state_path = HOME / 'setup-state.json'
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    if state.get('version') != TAG:
        raise ValueError('Prepared version differs or is missing; existing files retained. See docs/setup.md')
    if ENV.exists():
        digest = hashlib.sha256(ENV.read_bytes()).hexdigest()
        if state.get('configuration_sha256') != digest:
            raise ValueError('Existing configuration retained; automatic overwrite is disabled')
        if state.get('phase') == 'configured':
            print('Already configured. Use systemctl or the healthcheck to inspect services.')
            return
        if state.get('phase') != 'configuring':
            raise ValueError('Unknown setup state; configuration retained')
        activate(state)
        return
    if state.get('phase') != 'prepared':
        raise ValueError('Run --prepare first; existing setup state retained')
    for path in ('bin/AltServer', 'bin/netmuxd', 'anisette-image'):
        if not (HOME / path).is_file():
            raise ValueError('Run --prepare first')
    host = os.environ.get('ALTSERVER_HOST_IP', '')
    if not host:
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
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('Invalid prepared anisette image ID')
    values.update(ALTSERVER_HOME=str(HOME), ALTSERVER_BIN=str(HOME / 'bin/AltServer'),
                  NETMUXD_BIN=str(HOME / 'bin/netmuxd'), USBMUXD_SOCKET_ADDRESS='127.0.0.1:27015',
                  NETMUXD_REGISTER_MODE='api', ALTSERVER_NO_SUBSCRIBE='1',
                  ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6972', ANISETTE_URL='http://127.0.0.1:6972/',
                  ICLOUD_ANISETTE_IMAGE=image, ICLOUD_ANISETTE_STATE_DIR=str(ICLOUD_STATE),
                  ICLOUD_ANISETTE_APPLE_DIR=str(APPLE_DIR))
    content = ''.join(f'{k}={shlex.quote(v)}\n' for k, v in values.items()).encode()
    state.update(version=TAG, phase='configuring', configuration_sha256=hashlib.sha256(content).hexdigest())
    atomic_write(HOME / 'setup-state.json', json.dumps(state).encode())
    atomic_write(ENV, content)
    activate(state)


def activate(state):
    if state.get('version') != TAG:
        raise ValueError('Cannot activate files prepared by another version')
    env = dict(os.environ, ENV_FILE=str(ENV))
    run('sh', str(ROOT / 'scripts/install-helper-scripts.sh'), env=env)
    run('sh', str(ROOT / 'scripts/install-systemd-units.sh'), env=env)
    run('systemctl', 'start', 'altserver-icloud-local.service', 'altserver-native-netmuxd.service',
        'iphone-mobdev-address.service', 'iphone-mobdev-service.service',
        'altserver-native.service', 'altserver-native-healthcheck.timer')
    state['phase'] = 'configured'
    atomic_write(HOME / 'setup-state.json', json.dumps(state).encode())
    print('Configured. Run sudo /usr/local/sbin/altserver-native-healthcheck to inspect readiness.')
    if not (APPLE_DIR / 'AppleIncRootCertificate.cer').is_file():
        print('Anisette waits for the Apple runtime: sudo sh install.sh --import-apple-runtime <archive>')
    print('iPhone refresh and Apple sign-in still require verification in AltStore.')
    print('If AltStore fails with -22411 and shows no code field, run: sudo altserver-apple-trust')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--prepare', action='store_true', help='install dependencies and stage binaries (default)')
    group.add_argument('--configure', action='store_true', help='pairing must already exist; activate services')
    group.add_argument('--import-apple-runtime', metavar='ARCHIVE',
                       help='install Apple iCloud runtime exported by scripts/windows/export-apple-runtime.ps1')
    args = parser.parse_args()
    preflight()
    import fcntl
    with open('/run/lock/altserver-setup.lock', 'w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another setup process is running')
        if args.import_apple_runtime:
            import_apple_runtime(args.import_apple_runtime)
        else:
            configure() if args.configure else prepare()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Avoid printing subprocess arguments, which can contain device identifiers.
        message = str(error) if isinstance(error, ValueError) else type(error).__name__
        raise SystemExit('Setup stopped: ' + message)
