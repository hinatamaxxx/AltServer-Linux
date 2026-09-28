#!/usr/bin/env python3
"""Exercise the built executable without credentials or a physical device."""
from pathlib import Path
import subprocess
import sys

binary = str(Path(sys.argv[1]).resolve())
for args, expected, message in [
    (['--help'], 0, 'Usage:'),
    (['-h'], 0, 'Usage:'),
    (['--unknown-option'], 1, 'Usage:'),
    (['missing.ipa'], 1, 'requires -u, -a and -p'),
    (['-u', 'test', '-a', 'fixture', 'missing.ipa'], 1, 'requires -u, -a and -p'),
    (['-p', 'fixture', '-u', 'test', '-a', 'fixture', '/nonexistent/file.ipa'], 1, 'Cannot read the IPA'),
]:
    result = subprocess.run([binary, *args], capture_output=True, text=True, timeout=15)
    assert result.returncode == expected, (args, result.returncode, result.stderr)
    assert message in result.stdout + result.stderr, (args, result.stdout, result.stderr)
print('6 executable CLI regression cases passed')
