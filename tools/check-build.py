#!/usr/bin/env python3
"""Run independent native regressions and retain every failing check in CI."""
import subprocess
import sys

checks = [
    ['tools/check-signing.py', '/tmp/test-ldid'],
    ['tools/check-gsa-client.py'],
    ['tools/check-authentication-http.py'],
    ['tools/check-request-framing.py'],
    ['tools/check-native-netmux.py'],
    ['tools/check-error-mapping.py'],
]
failures = []
for command in checks:
    print('Running ' + command[0], flush=True)
    try:
        result = subprocess.run([sys.executable, *command], timeout=180)
        if result.returncode:
            failures.append(command[0])
    except subprocess.TimeoutExpired:
        failures.append(command[0] + ' (timeout)')
if failures:
    raise SystemExit('Failed checks: ' + ', '.join(failures))
print('All native build checks passed')
