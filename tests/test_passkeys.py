"""Verify real WebAuthn signatures with a synthetic P-256 authenticator."""
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import tempfile
import unittest

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

spec = importlib.util.spec_from_file_location('passkeys', Path(__file__).resolve().parents[1] / 'web/passkeys.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
encode, decode = module.encode, module.decode
ORIGIN = 'https://example.tailtest.ts.net'
RP = 'example.tailtest.ts.net'


class PasskeyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = module.Passkeys(Path(self.temp.name) / 'passkeys.json', ORIGIN, RP)
        self.private = ec.generate_private_key(ec.SECP256R1())
        self.id = secrets.token_bytes(32)

    def tearDown(self):
        self.temp.cleanup()

    def credential(self, options, register=True, origin=ORIGIN, rp=RP, uv=True, counter=1):
        client = json.dumps({'type': 'webauthn.create' if register else 'webauthn.get',
                             'challenge': options['challenge'], 'origin': origin}).encode()
        flags = (0x41 if register else 0x01) | (4 if uv else 0)
        auth = hashlib.sha256(rp.encode()).digest() + bytes([flags]) + counter.to_bytes(4, 'big')
        response = {'clientDataJSON': encode(client)}
        if register:
            public = self.private.public_key().public_numbers()
            cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: public.x.to_bytes(32, 'big'), -3: public.y.to_bytes(32, 'big')})
            auth += bytes(16) + len(self.id).to_bytes(2, 'big') + self.id + cose
            response['attestationObject'] = encode(cbor2.dumps({'fmt': 'none', 'attStmt': {}, 'authData': auth}))
        else:
            response.update(authenticatorData=encode(auth), userHandle=self.store.data['user'],
                            signature=encode(self.private.sign(auth + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))))
        return {'id': encode(self.id), 'rawId': encode(self.id), 'type': 'public-key', 'response': response}

    def enroll(self):
        token, options = self.store.options(True, 'owner')
        self.store.finish(token, self.credential(options, counter=0), True, 'owner')

    def test_registration_persistence_and_signed_login(self):
        self.enroll()
        self.store = module.Passkeys(self.store.path, ORIGIN, RP)
        self.assertTrue(self.store.registered)
        token, options = self.store.options(False, '')
        credential = self.credential(options, register=False)
        self.store.finish(token, credential, False, '')
        self.assertEqual(self.store.data['credentials'][0]['count'], 1)
        with self.assertRaises(ValueError):
            self.store.finish(token, credential, False, '')

    def test_registration_rejects_wrong_origin_rp_and_missing_verification(self):
        for kwargs in ({'origin': 'https://evil.invalid'}, {'rp': 'evil.invalid'}, {'uv': False}):
            token, options = self.store.options(True, 'owner')
            with self.assertRaises(Exception):
                self.store.finish(token, self.credential(options, **kwargs), True, 'owner')
            self.assertFalse(self.store.registered)

    def test_owner_and_one_time_enrollment(self):
        with self.assertRaises(ValueError):
            self.store.options(True, '')
        token, options = self.store.options(True, 'owner')
        with self.assertRaises(ValueError):
            self.store.finish(token, self.credential(options), True, 'other')
        self.enroll()
        with self.assertRaises(ValueError):
            self.store.options(True, 'owner')

    def test_assertion_requires_correct_signature_uv_and_challenge(self):
        self.enroll()
        for kind in ('signature', 'challenge', 'uv', 'origin'):
            token, options = self.store.options(False, '')
            if kind == 'challenge':
                options['challenge'] = encode(secrets.token_bytes(32))
            credential = self.credential(options, register=False, uv=kind != 'uv',
                                         origin='https://evil.invalid' if kind == 'origin' else ORIGIN)
            if kind == 'signature':
                credential['response']['signature'] = encode(b'invalid')
            with self.assertRaises(Exception):
                self.store.finish(token, credential, False, '')

    def test_expired_challenge_and_counter_replay(self):
        self.enroll()
        token, options = self.store.options(False, '')
        self.store.pending[token]['expires'] = 0
        with self.assertRaises(ValueError):
            self.store.finish(token, self.credential(options, register=False), False, '')
        token, options = self.store.options(False, '')
        self.store.finish(token, self.credential(options, register=False), False, '')
        token, options = self.store.options(False, '')
        with self.assertRaises(Exception):
            self.store.finish(token, self.credential(options, register=False), False, '')

    def test_origin_cannot_change_after_enrollment(self):
        self.enroll()
        with self.assertRaises(ValueError):
            module.Passkeys(self.store.path, 'https://other.tailtest.ts.net', 'other.tailtest.ts.net')
