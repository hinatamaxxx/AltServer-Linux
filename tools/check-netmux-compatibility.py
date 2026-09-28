#!/usr/bin/env python3
"""Read-only wire-format check for this fork's native address support (v0.1.3+).

Does not read pairing records, change device registration, or print identities.
An empty DeviceList is inconclusive (exit 2), never a compatibility pass.
"""
import argparse
import json
import plistlib
import socket
import struct

MAX_FRAME = 4 * 1024 * 1024


def receive(sock, size):
    result = bytearray()
    while len(result) < size:
        chunk = sock.recv(size - len(result))
        if not chunk:
            raise ValueError("truncated response")
        result.extend(chunk)
    return bytes(result)


def classify(address):
    # The pinned libusbmuxd accepts data only below its 200-byte buffer size.
    if not isinstance(address, bytes) or not 8 <= len(address) < 200:
        return "invalid"
    # The released legacy v0.1.4 uses sa_len=10 for IPv4, although the
    # conventional BSD sockaddr_in is 16 bytes. Report it separately.
    if address[1] == 2 and 8 <= address[0] <= len(address):
        return "legacy-bsd-ipv4" if address[0] < 16 else "bsd-ipv4"
    if address[1] == 30 and 28 <= address[0] <= len(address):
        return "bsd-ipv6"
    if address[:2] == b"\x02\x00" and len(address) >= 16:
        return "native-linux-ipv4"
    if address[:2] == b"\x0a\x00" and len(address) >= 28:
        return "native-linux-ipv6"
    return "unknown-incompatible"


def inspect(host, port):
    body = plistlib.dumps({"MessageType": "ListDevices", "ProgName": "compatibility-check",
                          "ClientVersionString": "compatibility-check", "kLibUSBMuxVersion": 3})
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(struct.pack("<IIII", len(body) + 16, 1, 8, 1) + body)
        length, version, kind, tag = struct.unpack("<IIII", receive(sock, 16))
        if not 16 < length <= MAX_FRAME or (version, kind, tag) != (1, 8, 1):
            raise ValueError("invalid response header")
        response = plistlib.loads(receive(sock, length - 16))
    if not isinstance(response, dict) or not isinstance(response.get("DeviceList"), list):
        raise ValueError("invalid device list")
    formats = []
    for device in response["DeviceList"]:
        if not isinstance(device, dict) or not isinstance(device.get("Properties"), dict):
            raise ValueError("invalid device properties")
        properties = device["Properties"]
        if properties.get("ConnectionType") == "Network":
            formats.append(classify(properties.get("NetworkAddress")))
    return formats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=27015)
    args = parser.parse_args()
    try:
        formats = inspect(args.host, args.port)
        compatible = bool(formats) and all(f in ("legacy-bsd-ipv4", "bsd-ipv4", "bsd-ipv6",
                                                 "native-linux-ipv4", "native-linux-ipv6") for f in formats)
        print(json.dumps({"scope": "address-format-only", "network_devices": len(formats),
                          "formats": formats, "compatible_with_native_altserver": compatible}))
        return 0 if compatible else (1 if formats else 2)
    except (OSError, ValueError, plistlib.InvalidFileException) as exc:
        print(json.dumps({"error": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
