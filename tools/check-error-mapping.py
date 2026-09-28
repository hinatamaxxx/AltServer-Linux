#!/usr/bin/env python3
"""Check unknown native errors against the generated production headers."""
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory() as directory:
    executable = str(Path(directory) / 'test-errors')
    subprocess.run(['clang++', '-std=c++17', '-include', 'shims/windows_shim.h',
                    '-Ibuild/AltServer_patched', '-Ibuild/AltSign_patched', '-Ishims',
                    '-Ilibraries/libimobiledevice/include', '-Ilibraries/libplist/include',
                    'tests/error_mapping.cpp', 'build/objs/AltSign_patched/Error.cpp.o',
                    'build/objs/AltSign_patched/Device.cpp.o', 'build/libplist.a',
                    '-lcpprest', '-lssl', '-lcrypto', '-lpthread', '-lm', '-o', executable], check=True)
    subprocess.run([executable], check=True, timeout=15)
print('Production error mapping: success and unknown error cases passed')
