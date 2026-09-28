"""Compile the production bridge and exercise its real fork/exec/ctypes boundary."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('g++') and os.name == 'posix', 'Linux compiler required')
class BonjourBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        fake = cls.root / 'fake.c'
        fake.write_text(r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
int32_t DNSServiceRegister(void** ref, uint32_t flags, uint32_t iface,
    const char* name, const char* type, const char* domain, const char* host,
    uint16_t port, uint16_t len, const void* txt, void* cb, void* ctx) {
    const unsigned char wanted[] = {0xff, 0x80, 0, 0x27, 0x5c};
    if (flags != 0x80000000u || iface != 7 || !name || strcmp(name, "quote'\\\n名前") ||
        strcmp(type, "_altserver._tcp") || domain != NULL || !host || *host ||
        port != htons(12345) || len != sizeof(wanted) || memcmp(txt, wanted, len) || cb || ctx)
        return -65540;
    *ref = (void*)(uintptr_t)0x1234567887654321ULL;
    const char* mode = getenv("BRIDGE_TEST_MODE");
    if (mode && !strcmp(mode, "hang")) sleep(60);
    return mode && !strcmp(mode, "error") ? -65548 : 0;
}
''')
        harness = cls.root / 'main.cpp'
        harness.write_text(r'''
#include "dns_sd.h"
#include <cstdio>
#include <cstring>
#include <arpa/inet.h>
int main(int argc, char** argv) {
    DNSServiceRef ref = nullptr;
    const unsigned char txt[] = {0xff, 0x80, 0, 0x27, 0x5c};
    bool invalid = argc > 1 && !strcmp(argv[1], "invalid");
    int rc = DNSServiceRegister(&ref, 0x80000000u, 7, "quote'\\\n名前", "_altserver._tcp",
        nullptr, "", htons(12345), sizeof(txt), invalid ? nullptr : txt, nullptr, nullptr);
    printf("%d\n", rc);
    return 0;
}
''')
        subprocess.run(['gcc', '-shared', '-fPIC', str(fake), '-o', str(cls.root / 'libdns_sd.so')], check=True)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT / 'libraries/dnssd_loader'), str(harness),
                        str(ROOT / 'libraries/dnssd_loader/dnssd_loader.cpp'),
                        '-o', str(cls.root / 'test')], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self, mode='', args=(), path=None):
        env = dict(os.environ, LD_LIBRARY_PATH=str(self.root), BRIDGE_TEST_MODE=mode)
        if path is not None:
            env['PATH'] = path
        result = subprocess.run([str(self.root / 'test'), *args], env=env,
                                capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("quote", result.stdout + result.stderr)
        return int(result.stdout.strip())

    def test_binary_txt_quotes_utf8_null_and_empty(self):
        self.assertEqual(self.invoke(), 0)

    def test_api_error_reaches_parent(self):
        self.assertEqual(self.invoke('error'), -65548)

    def test_missing_python_is_not_success(self):
        self.assertEqual(self.invoke(path=str(self.root)), -65537)

    def test_hung_registration_is_not_success(self):
        self.assertEqual(self.invoke('hang'), -65537)

    def test_null_txt_is_rejected_before_fork(self):
        self.assertEqual(self.invoke(args=('invalid',)), -65540)
