import importlib.util
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup', ROOT / 'scripts/setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def test_interrupted_configuration_can_resume_without_device_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            env = home / 'config'
            env.write_bytes(b'fixture configuration')
            state = dict(phase='configuring', configuration_sha256=hashlib.sha256(env.read_bytes()).hexdigest())
            (home / 'setup-state.json').write_text(json.dumps(state))
            with patch.object(setup, 'HOME', home), patch.object(setup, 'ENV', env), \
                 patch.object(setup, 'activate') as activate, patch.object(setup, 'output') as output:
                setup.configure()
                activate.assert_called_once_with(state)
                output.assert_not_called()
            env.write_bytes(b'changed by user')
            with patch.object(setup, 'HOME', home), patch.object(setup, 'ENV', env), \
                 patch.object(setup, 'activate') as activate:
                with self.assertRaises(ValueError):
                    setup.configure()
                activate.assert_not_called()

    def test_repeat_preparation_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / 'bin').mkdir()
            for name in ('bin/AltServer', 'bin/netmuxd', 'anisette-image'):
                (home / name).write_text('fixture')
            (home / 'setup-state.json').write_text(json.dumps(dict(phase='prepared')))
            with patch.object(setup, 'HOME', home), patch.object(setup, 'ENV', home / 'absent'), \
                 patch.object(setup, 'run') as run:
                setup.prepare()
                run.assert_not_called()

    def test_shell_metacharacters_and_invalid_addresses_rejected(self):
        udid = '0' * 40
        mac = ':'.join(['ab'] * 6)
        valid = setup.validated_device('192.0.2.1', udid, mac, '')
        self.assertEqual(valid['IPHONE_FALLBACK_IP'], '')
        for values in [('192.0.2.1', '$(id)', mac, ''),
                       ('192.0.2.1', udid, mac + '\ncommand', ''),
                       ('127.0.0.1', udid, mac, ''),
                       ('192.0.2.1', udid, mac, '224.0.0.1')]:
            with self.assertRaises(ValueError):
                setup.validated_device(*values)

    def test_checksum_mismatch_cannot_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'binary'
            file.write_bytes(b'fixture')
            setup.verify(file, hashlib.sha256(b'fixture').hexdigest())
            with self.assertRaises(ValueError):
                setup.verify(file, '0' * 64)

    def test_existing_installation_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / 'existing.env'
            env.write_text('existing configuration')
            with patch.object(setup, 'ENV', env), patch.object(setup, 'run') as run:
                for fn in (setup.prepare, setup.configure):
                    with self.assertRaises(ValueError):
                        fn()
                run.assert_not_called()
            self.assertEqual(env.read_text(), 'existing configuration')

    @unittest.skipUnless(os.name == 'posix', 'POSIX permissions')
    def test_atomic_private_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'config'
            setup.atomic_write(file, b'first')
            setup.atomic_write(file, b'second')
            self.assertEqual(file.read_bytes(), b'second')
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
