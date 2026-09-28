import importlib.util
import copy
import io
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup', ROOT / 'scripts/setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def release_fixture(self):
        return dict(tag_name='v9.8.7', draft=False, prerelease=False, assets=[dict(
            name=setup.NETMUX_ASSET, digest='sha256:' + 'a' * 64,
            browser_download_url='https://github.com/jkcoxson/netmuxd/releases/download/v9.8.7/' + setup.NETMUX_ASSET)])

    def test_latest_netmux_release_selects_future_version(self):
        with patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(self.release_fixture()).encode())) as fetch:
            release = setup.latest_netmux_release()
        self.assertEqual(release['version'], 'v9.8.7')
        self.assertEqual(release['sha256'], 'a' * 64)
        self.assertEqual(fetch.call_args.args[0].full_url, setup.NETMUX_LATEST)
        self.assertIn('/v9.8.7/', release['url'])

    def test_latest_netmux_requires_matching_asset_and_digest(self):
        base = self.release_fixture()
        cases = []
        for key, value in [('draft', True), ('prerelease', True), ('tag_name', ''), ('assets', []),
                           ('assets', base['assets'] * 2), ('assets', None)]:
            item = copy.deepcopy(base); item[key] = value; cases.append(item)
        for key, value in [('digest', None), ('digest', 'sha256:broken'), ('digest', 'md5:' + 'a' * 64),
                           ('browser_download_url', 'https://example.org/netmuxd.tar.gz'),
                           ('browser_download_url', base['assets'][0]['browser_download_url'].replace('v9.8.7', 'v9.8.6')),
                           ('name', 'netmuxd-aarch64-unknown-linux-gnu.tar.gz')]:
            item = copy.deepcopy(base); item['assets'][0][key] = value; cases.append(item)
        for item in cases + [[], None]:
            with self.subTest(metadata=item), patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(item).encode())):
                with self.assertRaises(ValueError): setup.latest_netmux_release()

    def test_latest_netmux_api_failure_does_not_fall_back(self):
        with patch.object(setup.urllib.request, 'urlopen', side_effect=HTTPError(setup.NETMUX_LATEST, 403, 'rate limited', {}, None)) as fetch:
            with self.assertRaises(HTTPError): setup.latest_netmux_release()
            self.assertEqual(fetch.call_count, 1)
        for body in (b'not-json', b' ' * (1024 * 1024 + 1)):
            with patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(body)):
                with self.assertRaises(ValueError): setup.latest_netmux_release()

    def test_prepare_verifies_and_records_resolved_netmux_release(self):
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); dist = root / 'dist'; dist.mkdir()
                (dist / 'AltServer-x86_64').write_bytes(b'altserver fixture')
                digest = hashlib.sha256(b'altserver fixture').hexdigest()
                (dist / 'SHA256SUMS').write_text(digest + '  AltServer-x86_64\n')
                archive = root / 'fixture.tar.gz'
                with tarfile.open(archive, 'w:gz') as tar:
                    info = tarfile.TarInfo('netmuxd'); info.size = len(b'netmux fixture')
                    tar.addfile(info, io.BytesIO(b'netmux fixture'))
                release = dict(version='v9.8.7', url='https://github.com/jkcoxson/netmuxd/releases/download/v9.8.7/' + setup.NETMUX_ASSET,
                               sha256='0' * 64 if corrupt else hashlib.sha256(archive.read_bytes()).hexdigest())
                def download(url, dest):
                    self.assertEqual(url, release['url']); dest.write_bytes(archive.read_bytes())
                home = root / 'install'
                with patch.object(setup, 'ROOT', root), patch.object(setup, 'HOME', home), \
                     patch.object(setup, 'ENV', root / 'absent.env'), patch.object(setup, 'run'), \
                     patch.object(setup, 'verify_binary_version'), patch.object(setup, 'latest_netmux_release', return_value=release), \
                     patch.object(setup, 'download', side_effect=download), \
                     patch.object(setup, 'output', return_value=json.dumps([dict(RepoDigests=[setup.ANISETTE_IMAGE])])):
                    if corrupt:
                        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'): setup.prepare()
                        self.assertFalse(home.exists())
                    else:
                        setup.prepare()
                        self.assertEqual((home / 'bin/netmuxd').read_bytes(), b'netmux fixture')
                        self.assertEqual(json.loads((home / 'setup-state.json').read_text())['netmuxd'], release)

    def test_binary_version_must_match_setup(self):
        with patch.object(setup.subprocess, 'check_output', return_value=f'AltServer-Linux {setup.TAG}\n'):
            setup.verify_binary_version(Path('fixture'))
        for actual in ('AltServer-Linux v0.1.3', 'Usage: AltServer', ''):
            with patch.object(setup.subprocess, 'check_output', return_value=actual):
                with self.assertRaises(ValueError):
                    setup.verify_binary_version(Path('fixture'))

    def test_interrupted_configuration_can_resume_without_device_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            env = home / 'config'
            env.write_bytes(b'fixture configuration')
            state = dict(version=setup.TAG, phase='configuring', configuration_sha256=hashlib.sha256(env.read_bytes()).hexdigest())
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
            (home / 'setup-state.json').write_text(json.dumps(dict(version=setup.TAG, phase='prepared')))
            with patch.object(setup, 'HOME', home), patch.object(setup, 'ENV', home / 'absent'), \
                 patch.object(setup, 'run') as run:
                setup.prepare()
                run.assert_not_called()

    def test_old_preparation_cannot_activate_new_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / 'bin').mkdir()
            for name in ('bin/AltServer', 'bin/netmuxd', 'anisette-image'):
                (home / name).write_text('old fixture')
            state = dict(version='v0.1.2', phase='prepared')
            (home / 'setup-state.json').write_text(json.dumps(state))
            with patch.object(setup, 'HOME', home), patch.object(setup, 'ENV', home / 'absent'), \
                 patch.object(setup, 'run') as run, patch.object(setup, 'output') as output:
                for action in (setup.prepare, setup.configure, lambda: setup.activate(state)):
                    with self.assertRaises(ValueError):
                        action()
                run.assert_not_called()
                output.assert_not_called()
            self.assertEqual((home / 'bin/AltServer').read_text(), 'old fixture')

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
