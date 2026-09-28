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

# Official Windows creates a client per request. Linux uses cpprest's native
# backend rather than WinHTTP; certificate validation must remain enabled.
if F.endswith('AppleAPI.cpp'):
    old = b'config.set_validate_certificates(false);'
    if content.count(old) != 1:
        raise RuntimeError('Review GSA TLS configuration after an AltSign update')
    content = content.replace(old, b'config.set_validate_certificates(true);')
    content = content.replace(b'#include <winhttp.h>', b'')
    content, count = re.subn(br'\s*config\.set_nativehandle_options\(\[\]\(web::http::client::native_handle handle\)[\s\S]+?\n\s*\}\);', b'', content)
    if count != 1:
        raise RuntimeError('Review WinHTTP GSA adapter after an AltSign update')

sys.stdout.buffer.write(content)
