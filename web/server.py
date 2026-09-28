#!/usr/bin/env python3
"""Authenticated, optional administration UI for the existing systemd stack."""
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import threading
import time
from urllib.parse import urlsplit

UNITS = {
    'altserver': 'altserver-native.service',
    'netmuxd': 'altserver-native-netmuxd.service',
    'anisette': 'altserver-anisette-docker.service',
    'discovery': 'iphone-mobdev-service.service',
    'health': 'altserver-native-healthcheck.timer',
}
STATIC = {'/passkeys.js': ('passkeys.js', 'text/javascript; charset=utf-8'), '/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8')}


def now():
    return datetime.now(timezone.utc).isoformat()


def load_environment(path):
    result = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not key.replace('_', '').isalnum():
            raise ValueError('Invalid environment file')
        values = shlex.split(value, comments=True)
        if len(values) != 1:
            raise ValueError('Invalid environment value')
        result[key] = values[0]
    return result


def command(args, timeout=12, env=None):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                          env=env, check=False)


class Backend:
    def __init__(self, demo=False, env_path=Path('/etc/altserver-native.env')):
        self.demo = demo
        self.env_path = env_path
        self.events = deque(maxlen=120)
        self.lock = threading.Lock()
        self.cache = None
        self.cached_at = 0
        self.diagnostics = None
        self.job = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.event_lock = threading.Lock()
        self.log('info', 'console_started')

    def log(self, level, code, action=None, target=None):
        with self.event_lock:
            self.events.append(dict(time=now(), level=level, code=code, action=action, target=target))

    def snapshot(self):
        with self.lock:
            if self.cache and time.monotonic() - self.cached_at < 8:
                return dict(self.cache, diagnostics=self.diagnostics, job=self.job)
            services = []
            for name, unit in UNITS.items():
                if self.demo:
                    values = dict(ActiveState='active', SubState='running', NRestarts='0')
                else:
                    try:
                        result = command(['systemctl', 'show', unit, '-p', 'ActiveState',
                                          '-p', 'SubState', '-p', 'NRestarts'], timeout=4)
                        values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
                        if result.returncode:
                            values = {}
                    except (OSError, subprocess.TimeoutExpired):
                        values = {}
                state = values.get('ActiveState', 'unknown')
                restarts = values.get('NRestarts', '0') or '0'
                services.append(dict(id=name, state=state if state in ('active', 'inactive', 'failed', 'activating', 'deactivating') else 'unknown',
                                     restarts=int(restarts) if restarts.isdigit() else 0))
            device = 'unknown'
            version = 'unknown'
            if self.demo:
                device, version = 'connected', 'preview'
            else:
                try:
                    env = dict(os.environ, **load_environment(self.env_path))
                    result = command(['/usr/local/sbin/altserver-native-probe', 'network'], timeout=6, env=env)
                    device = 'connected' if result.returncode == 0 else 'not_detected'
                    result = command(['/opt/altserver-native/bin/AltServer', '--version'], timeout=4)
                    words = result.stdout.strip().split()
                    if result.returncode == 0 and len(words) == 2 and words[0] == 'AltServer-Linux':
                        version = words[1][:30]
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    device = 'unknown'
            self.cache = dict(observed_at=now(), services=services, device=device,
                              version=version, demo=self.demo)
            self.cached_at = time.monotonic()
            return dict(self.cache, diagnostics=self.diagnostics, job=self.job)

    def logs(self):
        with self.event_lock:
            events = list(self.events)
        # Do not forward raw stdout: it can contain Apple authentication headers.
        # Only fixed, identifier-free event categories are exposed.
        if not self.demo:
            path = Path('/opt/altserver-native/logs/altserver.out.log')
            try:
                with path.open('rb') as stream:
                    stream.seek(max(0, os.fstat(stream.fileno()).st_size - 32768))
                    lines = stream.read(32768).decode('utf-8', 'replace').splitlines()
                counts = {key: sum(marker in line for line in lines) for key, marker in {
                    'profile_installed': 'Installed profile:', 'profile_removed': 'Removed profile:',
                    'request_finished': 'Finished handling request', 'request_failed': 'Failed to handle request'}.items()}
            except OSError:
                counts = None
        else:
            counts = dict(profile_installed=4, profile_removed=4, request_finished=3, request_failed=0)
        return dict(events=events, recent_counts=counts)

    def start(self, action, target):
        if action not in ('diagnose', 'recover', 'restart') or (action == 'restart' and target not in ('altserver', 'netmuxd', 'anisette', 'discovery')):
            raise ValueError('Unknown operation')
        if action != 'restart' and target is not None:
            raise ValueError('Unexpected target')
        with self.lock:
            if self.job and self.job['state'] == 'running':
                return False
            self.job = dict(action=action, target=target, state='running', started_at=now())
            self.log('info', 'operation_started', action, target)
            self.executor.submit(self._operate, action, target)
            return True

    def _operate(self, action, target):
        passed = True
        try:
            if not self.demo and action != 'diagnose':
                args = ['systemctl', 'restart', UNITS[target]] if action == 'restart' else ['systemctl', 'start', 'altserver-native-healthcheck.service']
                passed = command(args, timeout=100).returncode == 0
            checks = []
            env = {} if self.demo else dict(os.environ, **load_environment(self.env_path))
            for name in ('anisette', 'query', 'altserver', 'network'):
                try:
                    ok = self.demo or command(['/usr/local/sbin/altserver-native-probe', name], timeout=20, env=env).returncode == 0
                    state = 'pass' if ok else ('waiting' if name == 'network' else 'fail')
                except (OSError, subprocess.TimeoutExpired):
                    state = 'unknown'
                checks.append(dict(id=name, state=state))
            with self.lock:
                self.diagnostics = dict(checked_at=now(), checks=checks)
        except Exception:
            # Never return command output or exception text to the browser.
            passed = False
        finally:
            with self.lock:
                self.job = dict(action=action, target=target, state='completed' if passed else 'failed', finished_at=now())
                self.cached_at = 0
                self.log('info' if passed else 'error', 'operation_completed' if passed else 'operation_failed', action, target)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, backend, key, static_dir, passkeys=None, owner=''):
        super().__init__(address, Handler)
        self.backend, self.key, self.static_dir = backend, key, static_dir
        self.passkeys, self.owner = passkeys, owner
        self.origin = passkeys.origin if passkeys else None
        self.sessions = {}
        self.auth_lock = threading.Lock()
        self.login_attempts = deque(maxlen=32)
        self.slots = threading.BoundedSemaphore(16)
        self.allowed_hosts = {f'{address[0]}:{self.server_port}'}
        if address[0] == '127.0.0.1':
            self.allowed_hosts.add(f'localhost:{self.server_port}')
        if passkeys:
            self.allowed_hosts = {urlsplit(passkeys.origin).netloc}

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'AltServerConsole'

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        pass

    def respond(self, status, value, kind='application/json; charset=utf-8', cookie=None):
        data = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(status)
        for name, value in {
            'Content-Type': kind, 'Content-Length': str(len(data)), 'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            'Connection': 'close',
        }.items():
            self.send_header(name, value)
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def host_valid(self):
        return (self.headers.get('Host') in self.server.allowed_hosts and
                (not self.server.passkeys or self.client_address[0] == '127.0.0.1'))

    def is_owner(self):
        return bool(self.server.owner and self.client_address[0] == '127.0.0.1' and
                    self.headers.get('Tailscale-User-Login') == self.server.owner)

    def issue_session(self):
        with self.server.auth_lock:
            stamp = time.monotonic()
            self.server.sessions = {k: v for k, v in self.server.sessions.items() if v['expires'] > stamp}
            if len(self.server.sessions) >= 32:
                self.server.sessions.pop(next(iter(self.server.sessions)))
            token = secrets.token_urlsafe(32)
            self.server.sessions[token] = dict(csrf=secrets.token_urlsafe(24), expires=stamp + 28800)
        secure = '; Secure' if self.server.passkeys else ''
        return self.respond(200, {'ok': True}, cookie=f'altserver_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}')

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            token = cookie['altserver_session'].value if 'altserver_session' in cookie else ''
        except Exception:
            return None
        with self.server.auth_lock:
            entry = self.server.sessions.get(token)
            if entry and entry['expires'] > time.monotonic():
                return entry
        return None

    def do_GET(self):
        if not self.host_valid():
            return self.respond(403, {'error': 'host'})
        if self.path in STATIC:
            filename, kind = STATIC[self.path]
            return self.respond(200, (self.server.static_dir / filename).read_bytes(), kind)
        if self.path == '/api/auth':
            keys = self.server.passkeys
            return self.respond(200, dict(passkeys=bool(keys), registered=bool(keys and keys.registered),
                                         can_register=bool(keys and not keys.registered and self.is_owner())))
        session = self.session()
        if not session:
            return self.respond(401, {'error': 'login_required'})
        if self.path == '/api/session':
            return self.respond(200, dict(csrf=session['csrf'], demo=self.server.backend.demo))
        if self.path == '/api/status':
            return self.respond(200, self.server.backend.snapshot())
        if self.path == '/api/logs':
            return self.respond(200, self.server.backend.logs())
        return self.respond(404, {'error': 'not_found'})

    def do_POST(self):
        origin = self.server.origin or 'http://' + self.headers.get('Host', '')
        if not self.host_valid() or self.headers.get('Origin') != origin:
            return self.respond(403, {'error': 'origin'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json' or self.headers.get('Transfer-Encoding'):
            return self.respond(415, {'error': 'content_type'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= (65536 if self.path.startswith('/api/passkey/') else 4096):
                return self.respond(413, {'error': 'body_size'})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, TimeoutError):
            return self.respond(400, {'error': 'invalid_json'})
        if self.path.startswith('/api/passkey/'):
            if not self.server.passkeys:
                return self.respond(404, {'error': 'unavailable'})
            if self.path not in ('/api/passkey/register/options', '/api/passkey/register/verify',
                                 '/api/passkey/login/options', '/api/passkey/login/verify'):
                return self.respond(404, {'error': 'not_found'})
            register = '/register/' in self.path
            owner = self.server.owner if self.is_owner() else ''
            with self.server.auth_lock:
                stamp = time.monotonic()
                if sum(stamp - t < 60 for t in self.server.login_attempts) >= 20:
                    return self.respond(429, {'error': 'rate_limit'})
                self.server.login_attempts.append(stamp)
            try:
                if self.path.endswith('/options'):
                    token, options = self.server.passkeys.options(register, owner)
                    return self.respond(200, options, cookie=f'altserver_ceremony={token}; HttpOnly; Secure; SameSite=Strict; Path=/api/passkey/; Max-Age=180')
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                token = cookie['altserver_ceremony'].value
                self.server.passkeys.finish(token, body, register, owner)
            except Exception:
                return self.respond(400, {'error': 'passkey_failed'})
            return self.issue_session()
        if self.path == '/api/login':
            if self.server.passkeys:
                return self.respond(403, {'error': 'passkey_required'})
            with self.server.auth_lock:
                stamp = time.monotonic()
                recent = [t for t in self.server.login_attempts if stamp - t < 60]
                if len(recent) >= 10:
                    return self.respond(429, {'error': 'rate_limit'})
                key = body.get('key')
                if not isinstance(key, str) or not secrets.compare_digest(key.encode(), self.server.key.encode()):
                    self.server.login_attempts.append(stamp)
                    return self.respond(401, {'error': 'invalid_key'})
                self.server.sessions = {k: v for k, v in self.server.sessions.items() if v['expires'] > stamp}
                if len(self.server.sessions) >= 32:
                    self.server.sessions.pop(next(iter(self.server.sessions)))
                token = secrets.token_urlsafe(32)
                self.server.sessions[token] = dict(csrf=secrets.token_urlsafe(24), expires=stamp + 28800)
            return self.respond(200, {'ok': True}, cookie=f'altserver_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
        session = self.session()
        if not session:
            return self.respond(401, {'error': 'login_required'})
        if not secrets.compare_digest(self.headers.get('X-CSRF-Token', '').encode(), session['csrf'].encode()):
            return self.respond(403, {'error': 'csrf'})
        if self.path == '/api/logout':
            with self.server.auth_lock:
                self.server.sessions = {k: v for k, v in self.server.sessions.items() if v is not session}
            return self.respond(200, {'ok': True}, cookie='altserver_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' + ('; Secure' if self.server.passkeys else ''))
        if self.path == '/api/action':
            try:
                accepted = self.server.backend.start(body.get('action'), body.get('target'))
            except (ValueError, TypeError):
                return self.respond(400, {'error': 'invalid_action'})
            return self.respond(202 if accepted else 409, {'accepted': accepted})
        return self.respond(404, {'error': 'not_found'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--state-dir', type=Path, default=Path('/var/lib/altserver-webui'))
    parser.add_argument('--env-file', type=Path, default=Path('/etc/altserver-native.env'))
    parser.add_argument('--demo', action='store_true', help='synthetic data; login key is demo')
    args = parser.parse_args()
    address = ipaddress.IPv4Address(args.listen)
    if address.is_unspecified or address.is_multicast or not (address.is_loopback or address.is_private or address in ipaddress.IPv4Network('100.64.0.0/10')):
        parser.error('Use a loopback, private LAN, or Tailscale IPv4 address')
    if args.demo and not address.is_loopback:
        parser.error('Demo mode must use loopback')
    if args.demo:
        key = 'demo'
    else:
        args.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = args.state_dir / 'access-key'
        if not path.exists():
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(secrets.token_urlsafe(32) + '\n')
        key = path.read_text().strip()
        if len(key) < 32:
            parser.error('Access key must contain at least 32 characters')
    backend = Backend(args.demo, args.env_file)
    origin, owner = os.environ.get('WEBUI_ORIGIN', ''), os.environ.get('WEBUI_OWNER', '')
    passkeys = None
    if origin:
        parsed = urlsplit(origin)
        if (args.demo or str(address) != '127.0.0.1' or parsed.scheme != 'https' or
                not parsed.hostname or not parsed.hostname.endswith('.ts.net') or parsed.path or
                parsed.query or parsed.fragment or parsed.username or not owner):
            parser.error('Passkeys require loopback, a Tailscale HTTPS origin and WEBUI_OWNER')
        from passkeys import Passkeys
        passkeys = Passkeys(args.state_dir / 'passkeys.json', origin, parsed.hostname)
    server = Server((str(address), args.port), backend, key, Path(__file__).parent / 'static', passkeys, owner)
    print(f'AltServer Console listening on http://{args.listen}:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        backend.executor.shutdown(wait=False)


if __name__ == '__main__':
    main()
