#!/usr/bin/env python3
"""Bound BSD address copies in the pinned native netmuxd compatibility patch."""
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_bytes()
old = b'return p[0];'
if source.count(old) != 2:
    raise RuntimeError('Review native address copy lengths after a submodule update')
# usbmuxd_device_info_t has a fixed 200-byte buffer. Never trust sa_len to
# allocate/copy 0..255 bytes: connect() reads a full 16/28-byte sockaddr.
# This also supports the legacy IPv4 sa_len=10 without a short allocation.
source = source.replace(old, b'return 16;', 1).replace(old, b'return 28;', 1)
source = source.replace(b'struct sockaddr_storage saddr_storage;',
                        b'struct sockaddr_storage saddr_storage = {0};')
sys.stdout.buffer.write(source)
