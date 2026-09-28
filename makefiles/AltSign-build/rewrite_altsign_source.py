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
# Authentication is asynchronous. gmtime() shares process-global storage and
# can mix timestamps from concurrent requests; keep each conversion on-stack.
date_counts = {'AnisetteData.cpp': 2, 'AppleAPI.cpp': 2, 'AppleAPI+Authentication.cpp': 4}
for filename, expected in date_counts.items():
    if F.endswith(filename):
        if content.count(b'struct tm* tm;') != expected or content.count(b'gmtime(&time)') != expected:
            raise RuntimeError('Review UTC date conversion after an upstream update: ' + filename)
        content = content.replace(b'struct tm* tm;', b'struct tm dateStorage;\n\tstruct tm* tm;')
        content = content.replace(b'gmtime(&time)', b'gmtime_r(&time, &dateStorage)')

content = content.replace(b'winsock2.h', b'WinSock2.h')
content = content.replace(b'#include <windows.h>', b'')

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

if F.endswith('AppleAPI+Authentication.cpp'):
    content = content.replace(b'\r\n', b'\n')
    for old in (b'U("akd/1.0 CFNetwork/978.0.7 Darwin/18.7.0")', b'U("Xcode")'):
        if content.count(old) != 1:
            raise RuntimeError('Review authentication User-Agent after an upstream update')
        content = content.replace(old, b'altserver::auth::userAgent')
    # Official AltSign checks HTTP status before asking for a code or parsing
    # its response. Keep the original SMS incorrect-code/PE-token check.
    boundaries = (
        (b'AppleAPI::RequestTrustedDeviceTwoFactorCode(', b'AppleAPI::RequestSMSTwoFactorCode(',
         (b'requireSuccess', b'requireSuccess')),
        (b'AppleAPI::RequestSMSTwoFactorCode(', b'AppleAPI::FetchAccount(',
         (b'requireSuccess', b'requireServerAvailable')),
    )
    for start, end, guards in boundaries:
        if content.count(start) != 1 or content.count(end) != 1:
            raise RuntimeError('Review 2FA function boundaries after an upstream update')
        begin, finish = content.index(start), content.index(end)
        part = content[begin:finish]
        marker = b'return response.content_ready();'
        if part.count(marker) != len(guards):
            raise RuntimeError('Review 2FA response handlers after an upstream update')
        segments = part.split(marker)
        part = segments[0]
        for guard, segment in zip(guards, segments[1:]):
            part += b'altserver::auth::' + guard + b'(response.status_code());\n' + marker + segment
        content = content[:begin] + part + content[finish:]
    # The upstream debug macro prints decrypted authentication data and tokens.
    # Removing its evaluation also avoids dereferencing those values for logs.
    content, count = re.subn(br'^#define odslog\(msg\).*$', b'#define odslog(msg) do {} while (0)', content, flags=re.M)
    if count != 1:
        raise RuntimeError('Review authentication logging after an upstream update')
    content = b'#include "AuthenticationPolicy.h"\n' + content

sys.stdout.buffer.write(content)
