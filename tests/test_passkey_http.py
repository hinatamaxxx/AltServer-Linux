"""Trusted-proxy boundary and bootstrap authorization over the real HTTP server."""
import json
import unittest
import test_web_ui
import test_passkeys


class PasskeyHTTPTests(unittest.TestCase):
    request = test_web_ui.WebTests.request

    def setUp(self):
        test_web_ui.WebTests.setUp(self)
        self.fixture = test_passkeys.PasskeyTests()
        self.fixture.setUp()
        self.server.passkeys = self.fixture.store
        self.server.origin = test_passkeys.ORIGIN
        self.server.owner = 'owner'
        self.server.allowed_hosts = {test_passkeys.RP}
        self.headers = {'Host': test_passkeys.RP, 'Origin': test_passkeys.ORIGIN}

    def tearDown(self):
        test_web_ui.WebTests.tearDown(self)
        self.fixture.tearDown()

    def test_bootstrap_requires_owner_and_password_login_is_disabled(self):
        self.assertEqual(self.request('/api/login', {'key':'test-access-key'}, self.headers)[0], 403)
        state = json.loads(self.request('/api/auth', headers=self.headers)[2])
        self.assertFalse(state['can_register'])
        self.assertEqual(self.request('/api/passkey/register/options', {}, self.headers)[0], 400)
        headers = dict(self.headers, **{'Tailscale-User-Login':'owner'})
        state = json.loads(self.request('/api/auth', headers=headers)[2])
        self.assertTrue(state['can_register'])
        code, response_headers, options = self.request('/api/passkey/register/options', {}, headers)
        self.assertEqual(code, 200)
        self.assertIn('Secure', response_headers['Set-Cookie'])
        self.cookie = response_headers['Set-Cookie'].split(';')[0]
        credential = self.fixture.credential(json.loads(options), counter=0)
        code, response_headers, _ = self.request('/api/passkey/register/verify', credential, headers)
        self.assertEqual(code, 200)
        self.assertIn('Secure', response_headers['Set-Cookie'])
        self.cookie = response_headers['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('/api/session', headers=headers)[0], 200)
        self.assertEqual(self.request('/api/passkey/register/options', {}, headers)[0], 400)

    def test_incorrect_origin_and_replay_never_create_session(self):
        headers = dict(self.headers, **{'Tailscale-User-Login':'owner'})
        self.assertEqual(self.request('/api/passkey/register/options', {}, dict(headers, Origin='https://evil.invalid'))[0], 403)
        code, response_headers, options = self.request('/api/passkey/register/options', {}, headers)
        self.cookie = response_headers['Set-Cookie'].split(';')[0]
        credential = self.fixture.credential(json.loads(options), origin='https://evil.invalid')
        self.assertEqual(self.request('/api/passkey/register/verify', credential, headers)[0], 400)
        self.assertFalse(self.server.sessions)
        credential = self.fixture.credential(json.loads(options))
        self.assertEqual(self.request('/api/passkey/register/verify', credential, headers)[0], 400)
        self.assertFalse(self.server.sessions)
