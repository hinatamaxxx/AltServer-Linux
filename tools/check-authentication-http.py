#!/usr/bin/env python3
"""Exercise generated production trusted-device/SMS 2FA without Apple or a phone."""
from collections import deque
import http.server
import os
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
import threading

ROOT = Path('build/AltSign_patched')
source = (ROOT / 'AppleAPI+Authentication.cpp').read_text()


def function(text, signature):
    match = re.search(re.escape(signature) + r'[\s\S]*?\n\}', text)
    if not match:
        raise ValueError('Review production function boundary: ' + signature)
    return match.group()


methods = '\n'.join(function(source, signature) for signature in (
    'pplx::task<bool> AppleAPI::RequestTrustedDeviceTwoFactorCode(',
    'pplx::task<bool> AppleAPI::RequestSMSTwoFactorCode(',
    'web::http::http_request AppleAPI::MakeTwoFactorCodeRequest('))
decompress = function((ROOT / 'AppleAPI.cpp').read_text(), 'bool decompress(')
user_agent = 'AuthKit/1 (Macintosh; OS X 26.5.2) (com.apple.dt.Xcode/26.0)'


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            body = plistlib.loads(self.rfile.read(length))
            if self.server.requests:
                assert body['securityCode.code'] == '123456'
        assert self.headers['User-Agent'] == user_agent
        assert self.headers['X-Apple-I-Client-Time'] == '1970-01-01T00:00:00Z'
        status, token = self.server.responses.popleft()
        self.server.requests += 1
        body = plistlib.dumps({'ec': 0}) if status == 200 else b'not a plist; fixture-token'
        self.send_response(status)
        self.send_header('Content-Length', str(len(body)))
        if token:
            self.send_header('X-Apple-PE-Token', 'fixture')
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_GET

    def log_message(self, *args):
        pass


cases = []
for mode in ('trusted', 'sms'):
    for status in (401, 503):
        cases.append((mode, [(status, False)], str(status), 0))
    cases.append((mode, [(200, False), (503, False)], '503', 1))
    cases.append((mode, [(200, False), (401, False)], 'wrong-code' if mode == 'sms' else '401', 1))
    cases.append((mode, [(200, False), (200, True)], '0', 1))
cases.append(('trusted', [(302, False)], '302', 0))
cases.append(('sms', [(200, False), (200, False)], 'wrong-code', 1))

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    # Change access for the test only; retain all production response templates.
    (root / 'exposed_AppleAPI.hpp').write_text((ROOT / 'AppleAPI.hpp').read_text().replace('private:', 'public:'))
    harness = Path('tests/authentication_http.cpp').read_text()
    (root / 'test.cpp').write_text(harness + '\n' + decompress + '\n' + methods)
    executable = root / 'test'
    subprocess.run(['clang++', '-std=c++17', '-include', 'shims/windows_shim.h',
                    '-I' + str(root), '-I' + str(ROOT), '-Isrc', '-Ishims', '-Ilibraries/libplist/include',
                    str(root / 'test.cpp'), 'build/objs/AltSign_patched/Error.cpp.o',
                    'build/objs/AltSign_patched/AnisetteData.cpp.o', 'build/libplist.a',
                    '-lcpprest', '-lboost_system', '-lssl', '-lcrypto', '-lz', '-lpthread',
                    '-o', str(executable)], check=True)
    subprocess.run([str(executable), 'http://127.0.0.1', 'dates', '0', '0'],
                   env=dict(os.environ, TZ='JST-9'), check=True, timeout=15)
    for mode, responses, code, prompts in cases:
        with Server(('127.0.0.1', 0), Handler) as server:
            server.responses = deque(responses)
            server.requests = 0
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                subprocess.run([str(executable), f'http://127.0.0.1:{server.server_port}',
                                mode, code, str(prompts)], check=True, timeout=15)
                assert not server.responses
                assert server.requests == len(responses)
            finally:
                server.shutdown()
                worker.join()
print(f'Production 2FA HTTP flows: {len(cases)} cases passed; no Apple service contacted')
