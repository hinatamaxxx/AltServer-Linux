"""Exercise the real HTTP boundary, not just handler internals."""
import http.client
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('webserver', ROOT / 'web/server.py')
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class WebTests(unittest.TestCase):
    def setUp(self):
        self.backend = web.Backend(demo=True)
        self.server = web.Server(('127.0.0.1', 0), self.backend, 'test-access-key', ROOT / 'web/static')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cookie = ''
        self.csrf = ''

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.backend.executor.shutdown()
        self.thread.join()

    def request(self, path, body=None, headers=None):
        host = '127.0.0.1:' + str(self.server.server_port)
        connection = http.client.HTTPConnection(host, timeout=5)
        values = {'Host': host, 'Origin': 'http://' + host, 'Cookie': self.cookie,
                  'Content-Type': 'application/json', 'X-CSRF-Token': self.csrf}
        values.update(headers or {})
        connection.request('GET' if body is None else 'POST', path,
                           None if body is None else json.dumps(body), values)
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def login(self):
        code, headers, _ = self.request('/api/login', {'key': 'test-access-key'})
        self.assertEqual(code, 200)
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.cookie = headers['Set-Cookie'].split(';')[0]
        self.csrf = json.loads(self.request('/api/session')[2])['csrf']

    def test_authentication_logout_and_expiry(self):
        self.assertEqual(self.request('/api/status')[0], 401)
        self.assertEqual(self.request('/api/login', {'key': 'wrong'})[0], 401)
        self.login()
        self.assertEqual(self.request('/api/status')[0], 200)
        self.assertEqual(self.request('/api/logout', {})[0], 200)
        self.assertEqual(self.request('/api/status')[0], 401)
        self.login()
        next(iter(self.server.sessions.values()))['expires'] = 0
        self.assertEqual(self.request('/api/logs')[0], 401)

    def test_origin_host_csrf_and_action_allowlist(self):
        self.login()
        for header in ({'Origin': 'http://attacker.invalid'}, {'Host': 'attacker.invalid'},
                       {'X-CSRF-Token': ''}, {'X-CSRF-Token': '\u00e9'}):
            self.assertEqual(self.request('/api/action', {'action': 'recover'}, header)[0], 403)
        with patch.object(self.backend.executor, 'submit') as submit:
            for body in ({'action': 'shell'}, {'action': 'restart', 'target': 'ssh'},
                         {'action': 'restart', 'target': ['altserver']},
                         {'action': 'diagnose', 'target': 'altserver'}):
                self.assertEqual(self.request('/api/action', body)[0], 400)
            submit.assert_not_called()
            self.assertEqual(self.request('/api/action', {'action': 'restart', 'target': 'altserver'})[0], 202)
            self.assertEqual(self.request('/api/action', {'action': 'recover'})[0], 409)
            submit.assert_called_once_with(self.backend._operate, 'restart', 'altserver')

    def test_login_rate_limit(self):
        for _ in range(10):
            self.assertEqual(self.request('/api/login', {'key': 'bad'})[0], 401)
        self.assertEqual(self.request('/api/login', {'key': 'test-access-key'})[0], 429)

    def test_static_security_and_no_path_traversal(self):
        for path in ('/', '/app.js', '/style.css'):
            code, headers, data = self.request(path)
            self.assertEqual(code, 200)
            self.assertTrue(data)
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertEqual(headers['Cache-Control'], 'no-store')
        self.login()
        for path in ('/../server.py', '/access-key', '/api/status?debug=true'):
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request('/api/action', {'x': 'a' * 4096})[0], 413)

    def test_sensitive_output_not_exposed(self):
        backend = web.Backend(env_path=Path('/synthetic-env'))
        try:
            secret = 'SECRET_SENTINEL_DO_NOT_EXPOSE'
            result = subprocess.CompletedProcess([], 1, secret, secret)
            with patch.object(web, 'command', return_value=result), patch.object(web, 'load_environment', return_value={'PRIVATE': secret}):
                snapshot = backend.snapshot()
                self.assertEqual(snapshot['version'], 'unknown')
                backend._operate('restart', 'altserver')
            with patch.object(Path, 'open', side_effect=PermissionError(secret)):
                payload = json.dumps([snapshot, backend.logs(), backend.job, backend.diagnostics])
            self.assertNotIn(secret, payload)
            self.assertEqual(backend.job['state'], 'failed')
        finally:
            backend.executor.shutdown()

    def test_failed_probe_is_not_a_pass_and_commands_are_fixed(self):
        backend = web.Backend()
        try:
            with patch.object(web, 'load_environment', return_value={}), patch.object(web, 'command') as run:
                run.return_value = subprocess.CompletedProcess([], 1, '', '')
                backend._operate('diagnose', None)
                self.assertEqual([c['state'] for c in backend.diagnostics['checks']], ['fail', 'fail', 'fail', 'waiting'])
                self.assertTrue(all(c.args[0][0] == '/usr/local/sbin/altserver-native-probe' for c in run.call_args_list))
                run.side_effect = subprocess.TimeoutExpired('systemctl', 100)
                backend._operate('restart', 'netmuxd')
                self.assertEqual(backend.job['state'], 'failed')
                self.assertEqual(run.call_args.args[0], ['systemctl', 'restart', web.UNITS['netmuxd']])
        finally:
            backend.executor.shutdown()

    def test_raw_log_credentials_never_leave_backend(self):
        backend = web.Backend()
        try:
            with tempfile.TemporaryFile('w+b') as stream:
                stream.write(b'SECRET_SENTINEL_DO_NOT_EXPOSE\nInstalled profile: PRIVATE_PROFILE\nFinished handling request\n')
                stream.flush()
                with patch.object(Path, 'open', return_value=stream):
                    logs = backend.logs()
            self.assertEqual(logs['recent_counts']['profile_installed'], 1)
            self.assertEqual(logs['recent_counts']['request_finished'], 1)
            self.assertNotIn('SECRET_SENTINEL', json.dumps(logs))
            self.assertNotIn('PRIVATE_PROFILE', json.dumps(logs))
        finally:
            backend.executor.shutdown()


if __name__ == '__main__':
    unittest.main()
