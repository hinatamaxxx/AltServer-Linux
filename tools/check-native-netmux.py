#!/usr/bin/env python3
"""Exercise native addresses through real libusbmuxd/libimobiledevice code."""
import os
from pathlib import Path
import plistlib
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import re


def exact(sock, count):
    result = bytearray()
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise ValueError('truncated synthetic request')
        result.extend(chunk)
    return bytes(result)


class Mux(socketserver.ThreadingTCPServer):
    daemon_threads = True


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        length, version, kind, tag = struct.unpack('<IIII', exact(self.request, 16))
        request = plistlib.loads(exact(self.request, length - 16))
        assert request['MessageType'] == 'ListDevices'
        response = plistlib.dumps({'DeviceList': [{'DeviceID': 1, 'Properties': {
            'DeviceID': 1, 'SerialNumber': '0' * 40, 'ConnectionType': 'Network',
            'NetworkAddress': self.server.address}}]})
        self.request.sendall(struct.pack('<IIII', len(response) + 16, version, kind, tag) + response)


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    executable = root / 'test-native'
    subprocess.run(['gcc', '-Ilibraries/libimobiledevice/include', '-Ilibraries/libplist/include',
                    'tests/native_netmux.c',
                    'build/libimobiledevice.a', 'build/libplist.a', '-lssl', '-lcrypto',
                    '-lpthread', '-lm', '-luuid', '-o', str(executable)], check=True)
    # Exercise the exact generated copy-size helper for every BSD sa_len value.
    source = Path('build/idevice_native.c').read_text()
    helper = re.search(r'static size_t idevice_sockaddr_len\(.*?\n\}', source, re.S).group()
    (root / 'sizes.c').write_text('#include <stddef.h>\n#include <assert.h>\n' + helper + '''
int main(void) {
    unsigned char data[200] = {0};
    for (int i = 0; i < 256; ++i) {
        data[0] = i; data[1] = 2; assert(idevice_sockaddr_len(data) == 16);
        data[1] = 30; assert(idevice_sockaddr_len(data) == 28);
    }
    data[0] = 2; data[1] = 0; assert(idevice_sockaddr_len(data) == 16);
    data[0] = 10; assert(idevice_sockaddr_len(data) == 28);
    data[0] = 77; assert(idevice_sockaddr_len(data) == 200);
}
''')
    subprocess.run(['gcc', str(root / 'sizes.c'), '-o', str(root / 'sizes')], check=True)
    subprocess.run([str(root / 'sizes')], check=True)
    cases = []
    ipv4 = bytes(2) + socket.inet_aton('127.0.0.1') + bytes(8)
    for prefix, padding in [(b'\x02\0', 0), (b'\x02\0', 112), (b'\x02\0', 136),
                            (b'\x10\x02', 0), (b'\x0a\x02', 0), (b'\xff\x02', 0)]:
        cases.append((socket.AF_INET, prefix + ipv4 + bytes(padding), True))
    ipv6 = bytes(6) + socket.inet_pton(socket.AF_INET6, '::1') + bytes(4)
    cases.extend((socket.AF_INET6, prefix + ipv6, True) for prefix in (b'\x0a\0', b'\x1c\x1e'))
    cases.append((socket.AF_INET, b'\x4d\0' + ipv4, False))
    for family, address, success in cases:
        with socket.socket(family, socket.SOCK_STREAM) as device, Mux(('127.0.0.1', 0), Handler) as mux:
            device.bind(('127.0.0.1' if family == socket.AF_INET else '::1', 0))
            device.listen()
            device.settimeout(5)
            mux.address = address
            worker = threading.Thread(target=mux.serve_forever, daemon=True)
            worker.start()
            try:
                env = dict(os.environ, USBMUXD_SOCKET_ADDRESS=f'127.0.0.1:{mux.server_address[1]}')
                subprocess.run([str(executable), str(device.getsockname()[1]), str(int(success))],
                               env=env, check=True, timeout=15)
                if success:
                    connection, _ = device.accept()
                    connection.close()
            finally:
                mux.shutdown()
                worker.join()
print('Native netmux: 9 direct-library cases and 512 BSD copy-length bounds passed')
