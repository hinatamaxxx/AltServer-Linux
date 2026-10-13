import importlib.machinery
import importlib.util
import os
from pathlib import Path
import plistlib
import socket
import struct
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "scripts/runtime" / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


probe = load("altserver-native-probe")
trust = load("altserver-apple-trust")
MAC = ":".join(["ab"] * 6)
UDID = "test-device"


class ProbeTests(unittest.TestCase):
    def test_anisette_protocol_rejects_missing_fields_and_nine_hour_skew(self):
        data = dict.fromkeys(("machineID", "oneTimePassword", "localUserID", "deviceUniqueIdentifier",
                              "deviceSerialNumber", "deviceDescription", "locale", "timeZone"), "fixture")
        data.update(routingInfo="1", date="2026-09-15T15:00:00Z")
        response = dict(identifier="AnisetteDataResponse", version=1, anisetteData=data)
        now = datetime(2026, 9, 15, 15, 0, tzinfo=timezone.utc)
        self.assertTrue(probe.valid_anisette_response(response, now))
        data["date"] = "2026-09-15T06:00:00Z"
        self.assertFalse(probe.valid_anisette_response(response, now))
        data["date"] = "2026-09-15T15:00:00Z"
        data.pop("locale")
        self.assertFalse(probe.valid_anisette_response(response, now))

    def test_fragmented_header_and_body(self):
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            body = plistlib.dumps({"DeviceList": []})
            packet = struct.pack("<IIII", 16 + len(body), 1, 8, 1) + body

            def serve():
                with server.accept()[0] as peer:
                    header = probe.recv_exact(peer, 16)
                    probe.recv_exact(peer, struct.unpack("<I", header[:4])[0] - 16)
                    for byte in packet:
                        peer.sendall(bytes([byte]))

            thread = threading.Thread(target=serve)
            thread.start()
            self.assertEqual(probe.mux_request({"MessageType": "ListDevices"}, server.getsockname()),
                             {"DeviceList": []})
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

    def test_truncated_packet(self):
        fake = unittest.mock.Mock()
        fake.recv.side_effect = [b"abc", b""]
        with self.assertRaises(OSError):
            probe.recv_exact(fake, 16)

    def test_rejects_oversized_packet(self):
        fake = unittest.mock.MagicMock()
        fake.__enter__.return_value = fake
        fake.recv.return_value = struct.pack("<IIII", probe.MAX_PACKET + 1, 1, 8, 1)
        with patch.object(socket, "create_connection", return_value=fake), self.assertRaises(ValueError):
            probe.mux_request({})

    def test_discovery_ignores_other_phone_and_synthetic_feedback(self):
        encoded = MAC.replace(":", r"\058")
        records = "\n".join([
            "=;eth0;IPv4;other@other;_apple-mobdev2._tcp;local;other.local;203.0.113.2;62078;",
            f"=;eth0;IPv4;{encoded}\\064{UDID};_apple-mobdev2._tcp;local;iphone-alt.local;203.0.113.3;62078;",
            f"=;eth0;IPv4;{encoded}\\064real;_apple-mobdev2._tcp;local;phone.local;203.0.113.4;32498;",
        ])
        self.assertEqual(probe.candidates("", records, MAC, UDID, ""), ["203.0.113.4"])

    def test_neighbor_mac_is_exact(self):
        lines = f"203.0.113.5 dev eth0 lladdr {MAC} REACHABLE\n203.0.113.6 dev eth0 lladdr {MAC}00 REACHABLE"
        self.assertEqual(probe.candidates(lines, "", MAC, UDID, ""), ["203.0.113.5"])

    def test_fallback_does_not_trust_an_open_port(self):
        env = {"IPHONE_UDID": UDID, "IPHONE_WIFI_MAC": MAC, "IPHONE_FALLBACK_IP": "203.0.113.8"}
        with patch.dict(os.environ, env), patch.object(probe, "output", return_value=""), \
                patch.object(probe, "port_open", return_value=True), \
                patch.object(probe, "device_identity", return_value=False):
            self.assertIsNone(probe.discover())


class TrustTests(unittest.TestCase):
    def test_reads_quoted_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config"
            config.write_text("# comment\nANISETTE_URL=http://127.0.0.1:6972/\n"
                              "ICLOUD_ANISETTE_APPLE_DIR='/opt/altserver-native/icloud-local/apple'\nEMPTY=''\n")
            values = trust.configuration(str(config))
        self.assertEqual(values["ANISETTE_URL"], "http://127.0.0.1:6972/")
        self.assertEqual(values["ICLOUD_ANISETTE_APPLE_DIR"], "/opt/altserver-native/icloud-local/apple")
        self.assertEqual(values["EMPTY"], "")

    def test_session_data_without_xml_prolog(self):
        try:
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ImportError:
            self.skipTest("cryptography unavailable")
        import hashlib
        import hmac
        session = b"synthetic-session-key"
        body = b'<plist version="1.0"><dict><key>adsid</key><string>fixture</string></dict></plist>'
        key = hmac.new(session, b"extra data key:", hashlib.sha256).digest()
        iv = hmac.new(session, b"extra data iv:", hashlib.sha256).digest()[:16]
        padder = padding.PKCS7(128).padder()
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        encrypted = encryptor.update(padder.update(body) + padder.finalize()) + encryptor.finalize()
        self.assertEqual(trust.decrypt_spd(session, encrypted), {"adsid": "fixture"})

    def test_refuses_non_interactive_use(self):
        with patch("sys.stdin") as stdin:
            stdin.isatty.return_value = False
            with self.assertRaises(SystemExit):
                trust.main()


@unittest.skipUnless(os.name == "posix", "requires POSIX shell")
class IcloudRunTests(unittest.TestCase):
    def run_script(self, directory, apple):
        (directory / "config").write_text(
            f"ICLOUD_ANISETTE_IMAGE=sha256:{'a' * 64}\nICLOUD_ANISETTE_STATE_DIR={directory / 'state'}\n"
            f"ICLOUD_ANISETTE_APPLE_DIR={apple}\n")
        docker = directory / "docker"
        docker.write_text('#!/bin/sh\necho "$*" >>"$CALLS"\n')
        docker.chmod(0o755)
        script = (ROOT / "scripts/runtime/altserver-icloud-anisette-run").read_text()
        (directory / "run").write_text(script.replace("/usr/bin/docker", str(docker)))
        env = dict(os.environ, ENV_FILE=str(directory / "config"), CALLS=str(directory / "calls"))
        return subprocess.run(["sh", str(directory / "run")], env=env, capture_output=True, text=True)

    def test_waits_for_apple_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            result = self.run_script(directory, directory / "missing")
            self.assertEqual(result.returncode, 1)
            self.assertIn("--import-apple-runtime", result.stderr)
            self.assertFalse((directory / "calls").exists())

    def test_runs_pinned_image_with_private_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            apple = directory / "apple"
            apple.mkdir()
            (apple / "AppleIncRootCertificate.cer").write_bytes(b"fixture")
            result = self.run_script(directory, apple)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = (directory / "calls").read_text().splitlines()[-1]
            self.assertIn("-p 127.0.0.1:6972:6969", run)
            self.assertIn(f"{apple}:/apple:ro", run)
            self.assertIn("--cap-drop ALL", run)
            self.assertTrue(run.endswith("sha256:" + "a" * 64))
            self.assertEqual((directory / "state").stat().st_mode & 0o777, 0o700)


@unittest.skipUnless(os.name == "posix", "requires POSIX shell")
class HealthTests(unittest.TestCase):
    def test_direct_netmux_failure_restarts_only_netmuxd(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "config").write_text("NETMUXD_REGISTER_MODE=api\n")
            (directory / "probe").write_text('#!/bin/sh\ncase "$1" in anisette|altserver) exit 0;; *) exit 1;; esac\n')
            (directory / "systemctl").write_text('#!/bin/sh\nif [ "$1" = restart ]; then echo "$2" >>"$CALLS"; fi\nexit 0\n')
            (directory / "logger").write_text('#!/bin/sh\nexit 0\n')
            for name in ("probe", "systemctl", "logger"):
                (directory / name).chmod(0o755)
            env = dict(os.environ, ENV_FILE=str(directory / "config"),
                       ALTSERVER_PROBE=str(directory / "probe"), CALLS=str(directory / "calls"),
                       ALTSERVER_HEALTH_STATE_DIR=str(directory / "health"),
                       PATH=str(directory) + os.pathsep + os.environ["PATH"])
            for _ in range(5):
                result = subprocess.run(["sh", str(ROOT / "scripts/runtime/altserver-native-healthcheck")],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual((directory / "calls").read_text(), "altserver-native-netmuxd.service\n")

    def test_offline_phone_does_not_hide_server_failure_and_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "config").write_text("")
            (directory / "probe").write_text('#!/bin/sh\ncase "$1" in anisette|query) exit 0;; *) exit 1;; esac\n')
            (directory / "systemctl").write_text('#!/bin/sh\nif [ "$1" = restart ]; then echo "$2" >>"$CALLS"; fi\nexit 0\n')
            (directory / "logger").write_text('#!/bin/sh\nexit 0\n')
            for name in ("probe", "systemctl", "logger"):
                (directory / name).chmod(0o755)
            env = dict(os.environ, ENV_FILE=str(directory / "config"),
                       ALTSERVER_PROBE=str(directory / "probe"), CALLS=str(directory / "calls"),
                       ALTSERVER_HEALTH_STATE_DIR=str(directory / "health"),
                       PATH=str(directory) + os.pathsep + os.environ["PATH"])
            for _ in range(5):
                result = subprocess.run(["sh", str(ROOT / "scripts/runtime/altserver-native-healthcheck")],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("\nhealthy\n", result.stdout)
            self.assertEqual((directory / "calls").read_text(), "altserver-native.service\n")


if __name__ == "__main__":
    unittest.main()
