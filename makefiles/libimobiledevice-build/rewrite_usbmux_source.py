#!/usr/bin/env python3
"""Validate address bytes once, before official libimobiledevice consumes them."""
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_bytes().replace(b'\r\n', b'\n')
old = b'''if (netaddr && addr_len > 0 && addr_len < sizeof(devinfo->conn_data)) {
\t\t\t\t\t\tmemcpy(devinfo->conn_data, netaddr, addr_len);
\t\t\t\t\t}'''
if source.count(old) != 1:
    raise RuntimeError('Review libusbmuxd NetworkAddress decoding after an upstream update')
source = source.replace(old, b'''altserver_decode_network_address(devinfo->conn_data,
                        sizeof(devinfo->conn_data), netaddr, addr_len);''')
sys.stdout.buffer.write(b'#include "NativeNetworkAddress.h"\n' + source)
