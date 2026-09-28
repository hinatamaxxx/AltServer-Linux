#!/usr/bin/env python3
"""Offline signing regression: synthetic Mach-O, disposable self-signed identity.

Exercises the same ldid object as AltServer. No Apple account or phone is used.
Checks CMS signature, full SHA-1/SHA-256 agility hashes and designated requirement.
"""
import hashlib
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile


def run(*args):
    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        sys.stderr.write(error.output.decode(errors='replace'))
        raise


def macho():
    # Minimal ARM64 image with room for LC_CODE_SIGNATURE in its first page.
    section = struct.pack('<16s16sQQIIIIIIII', b'__text', b'__TEXT',
                          0x100000200, 4, 512, 2, 0, 0, 0x80000400, 0, 0, 0)
    text = struct.pack('<II16sQQQQiiII', 0x19, 72 + len(section), b'__TEXT',
                       0x100000000, 4096, 0, 4096, 7, 5, 1, 0) + section
    link = struct.pack('<II16sQQQQiiII', 0x19, 72, b'__LINKEDIT',
                       0x100001000, 0, 4096, 0, 7, 1, 0, 0)
    version = struct.pack('<IIIIII', 0x32, 24, 2, 0xC0000, 0xC0000, 0)
    commands = text + link + version
    header = struct.pack('<IIIIIIII', 0xfeedfacf, 0x100000c, 0, 2, 3,
                         len(commands), 0x200085, 0)
    return (header + commands).ljust(512, b'\0') + b'\xc0\x03\x5f\xd6' + bytes(4096 - 516)


def children(data):
    """Decode definite-length DER TLVs (sufficient for this CMS fixture)."""
    result = []
    pos = 0
    while pos < len(data):
        tag, size = data[pos:pos + 2]
        pos += 2
        if size & 128:
            count = size & 127
            assert 0 < count <= 4
            size = int.from_bytes(data[pos:pos + count], 'big')
            pos += count
        value = data[pos:pos + size]
        assert len(value) == size
        pos += size
        result.append((tag, value))
    return result


def find_attribute(data, oid):
    found = []
    for tag, value in children(data):
        if tag & 32:
            nodes = children(value)
            if nodes and nodes[0] == (6, oid):
                found.append(nodes)
            found.extend(find_attribute(value, oid))
    return found


def verify(path, root):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 16)[0]
    position = 32
    signatures = []
    for _ in range(count):
        command, size = struct.unpack_from('<II', data, position)
        if command == 0x1d:
            offset, length = struct.unpack_from('<II', data, position + 8)
            signatures.append(data[offset:offset + length])
        position += size
    assert len(signatures) == 1
    blob = signatures[0]
    magic, length, count = struct.unpack_from('>III', blob)
    assert magic == 0xfade0cc0 and length <= len(blob)
    slots = {}
    for i in range(count):
        slot, offset = struct.unpack_from('>II', blob, 12 + i * 8)
        size = struct.unpack_from('>I', blob, offset + 4)[0]
        slots[slot] = blob[offset:offset + size]
    assert 0 in slots and 0x1000 in slots and 0x10000 in slots
    requirements = slots[2]
    assert struct.unpack_from('>I', requirements, 8)[0] > 0
    assert struct.unpack_from('>I', requirements, 12)[0] == 3  # designated
    cms = slots[0x10000][8:]
    (root / 'cms.der').write_bytes(cms)
    (root / 'cd.bin').write_bytes(slots[0])
    run('openssl', 'smime', '-verify', '-inform', 'DER', '-in', str(root / 'cms.der'),
        '-content', str(root / 'cd.bin'), '-noverify', '-out', str(root / 'verified.bin'))
    # 1.2.840.113635.100.9.2, containing SHA-1 and SHA-256 OID/digest pairs.
    attributes = find_attribute(cms, bytes.fromhex('2a864886f763640902'))
    assert len(attributes) == 1
    pairs = children(attributes[0][1][1])
    hashes = {}
    for tag, value in pairs:
        assert tag == 0x30
        oid, digest = children(value)
        assert oid[0] == 6 and digest[0] == 4
        hashes[oid[1]] = digest[1]
    assert hashes[bytes.fromhex('2b0e03021a')] == hashlib.sha1(slots[0]).digest()
    assert hashes[bytes.fromhex('608648016503040201')] == hashlib.sha256(slots[0x1000]).digest()


def main():
    executable = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        run('openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=AltServer Offline Test/OU=TESTTEAM',
            '-keyout', str(root / 'key.pem'), '-out', str(root / 'cert.pem'))
        identity = root / 'identity.p12'
        run('openssl', 'pkcs12', '-export', '-inkey', str(root / 'key.pem'),
            '-in', str(root / 'cert.pem'), '-out', str(identity), '-passout', 'pass:',
            '-keypbe', 'PBE-SHA1-3DES', '-certpbe', 'PBE-SHA1-3DES', '-macalg', 'sha1')
        binary = root / 'standalone'
        binary.write_bytes(macho())
        run(executable, '-S', '-K' + str(identity), '-Iorg.example.offline', str(binary))
        verify(binary, root)
        # Exercise DiskFolder/bundle signing, which has a different API and path rules.
        bundle = root / 'Offline.app'
        bundle.mkdir()
        (bundle / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable': 'Offline', 'CFBundleIdentifier': 'org.example.offline',
            'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1'}))
        (bundle / 'Offline').write_bytes(macho())
        (bundle / 'resource.txt').write_text('offline test')
        run(executable, '-S', '-K' + str(identity), str(bundle))
        verify(bundle / 'Offline', root)
        assert (bundle / '_CodeSignature' / 'CodeResources').is_file()
    print('Offline standalone and bundle signing: CMS, full agility hashes and requirements passed')


if __name__ == '__main__':
    main()
