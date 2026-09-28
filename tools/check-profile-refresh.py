#!/usr/bin/env python3
"""Exercise the compiled refresh method with a stateful fake iOS profile store."""
from pathlib import Path
import re
import subprocess
import tempfile

source = Path('build/AltServer_patched/DeviceManager.cpp').read_text()
method = re.search(r'pplx::task<void> DeviceManager::InstallProvisioningProfiles\(.*?\n\}', source, re.S)
assert method, 'Production profile refresh method is missing'
harness = Path('tests/profile_refresh.cpp').read_text().replace('// PRODUCTION_REFRESH_METHOD', method.group())
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'test.cpp').write_text(harness)
    subprocess.run(['clang++', '-std=c++17', str(root / 'test.cpp'), '-o', str(root / 'test'),
                    '-lcpprest', '-lboost_system', '-lssl', '-lcrypto', '-lpthread'], check=True)
    subprocess.run([str(root / 'test')], check=True, timeout=20)
