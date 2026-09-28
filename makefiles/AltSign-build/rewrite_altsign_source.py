#!/usr/bin/python3

import re
import sys

F = sys.argv[1]

with open(F, 'rb') as f:
    content = f.read()

content = re.sub(br'L("([^"\\]|\\.)*")', br'U(\1)', content)
content = content.replace(b'std::wstring', b'std::string')
content = content.replace(b'boost/filesystem.hpp', b'filesystem')
content = content.replace(b'boost::filesystem', b'std::filesystem')

content = content.replace(b'"%FT%T%z"', b'"%Y-%m-%dT%H:%M:%SZ"')
content = content.replace(b'localtime(', b'gmtime(')

content = content.replace(b'winsock2.h', b'WinSock2.h')

# The pinned fork creates a new GSA connection for each request, but inherits
# upstream's disabled certificate verification. Keep TLS verification enabled.
if F.endswith('AppleAPI.cpp'):
    old = b'config.set_validate_certificates(false);'
    if content.count(old) != 2:
        raise RuntimeError('Review GSA TLS configuration after an AltSign update')
    content = content.replace(old, b'config.set_validate_certificates(true);')

sys.stdout.buffer.write(content)
