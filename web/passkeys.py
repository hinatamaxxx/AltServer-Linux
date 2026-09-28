"""WebAuthn ceremonies; private keys and biometric data stay on the device."""
import base64
import json
import os
from pathlib import Path
import secrets
import threading
import time

from webauthn import (generate_registration_options, generate_authentication_options,
                      verify_registration_response, verify_authentication_response, options_to_json)
from webauthn.helpers.structs import (AuthenticatorSelectionCriteria,
                                    ResidentKeyRequirement, UserVerificationRequirement,
                                    PublicKeyCredentialDescriptor)


def encode(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def decode(value):
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


class Passkeys:
    def __init__(self, path, origin, rp_id):
        self.path, self.origin, self.rp_id = Path(path), origin, rp_id
        self.lock = threading.RLock()
        self.pending = {}
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {
            'user': encode(secrets.token_bytes(32)), 'credentials': []}
        if self.data.get('origin', origin) != origin:
            raise ValueError('Passkeys are bound to a different origin')

    @property
    def registered(self):
        with self.lock:
            return bool(self.data['credentials'])

    def save(self):
        self.data['origin'] = self.origin
        temporary = self.path.with_suffix('.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(self.data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)

    def options(self, register, owner):
        with self.lock:
            stamp = time.monotonic()
            self.pending = {k: v for k, v in self.pending.items() if v['expires'] > stamp}
            if len(self.pending) >= 32:
                raise ValueError('Too many ceremonies')
            if register:
                if self.registered or not owner:
                    raise ValueError('Enrollment unavailable')
                value = generate_registration_options(
                    rp_id=self.rp_id, rp_name='AltServer Console', user_name='Administrator',
                    user_id=decode(self.data['user']),
                    authenticator_selection=AuthenticatorSelectionCriteria(
                        resident_key=ResidentKeyRequirement.REQUIRED,
                        user_verification=UserVerificationRequirement.REQUIRED))
            else:
                if not self.registered:
                    raise ValueError('Not enrolled')
                value = generate_authentication_options(
                    rp_id=self.rp_id, user_verification=UserVerificationRequirement.REQUIRED,
                    allow_credentials=[PublicKeyCredentialDescriptor(id=decode(c['id']))
                                       for c in self.data['credentials']])
            token = secrets.token_urlsafe(32)
            self.pending[token] = dict(challenge=value.challenge, register=register,
                                       owner=owner, expires=stamp + 180)
            return token, json.loads(options_to_json(value))

    def finish(self, token, credential, register, owner):
        with self.lock:
            entry = self.pending.pop(token, None)
            if not entry or entry['expires'] <= time.monotonic() or entry['register'] != register:
                raise ValueError('Expired ceremony')
            if register:
                if self.registered or not owner or entry['owner'] != owner:
                    raise ValueError('Enrollment unavailable')
                result = verify_registration_response(
                    credential=credential, expected_challenge=entry['challenge'],
                    expected_rp_id=self.rp_id, expected_origin=self.origin,
                    require_user_verification=True)
                record = dict(id=encode(result.credential_id),
                              public_key=encode(result.credential_public_key), count=result.sign_count)
                self.data['credentials'].append(record)
                try:
                    self.save()
                except Exception:
                    self.data['credentials'].remove(record)
                    raise
            else:
                record = next((c for c in self.data['credentials'] if c['id'] == credential.get('id')), None)
                if not record:
                    raise ValueError('Unknown credential')
                user = credential.get('response', {}).get('userHandle')
                if user and decode(user) != decode(self.data['user']):
                    raise ValueError('Wrong user')
                result = verify_authentication_response(
                    credential=credential, expected_challenge=entry['challenge'],
                    expected_rp_id=self.rp_id, expected_origin=self.origin,
                    credential_public_key=decode(record['public_key']),
                    credential_current_sign_count=record['count'], require_user_verification=True)
                record['count'] = result.new_sign_count
                self.save()
