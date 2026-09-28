#!/usr/bin/env python3
"""Generate the executable version from the installer/release source of truth."""
from pathlib import Path
import re

version = (Path(__file__).resolve().parents[1] / 'VERSION').read_text().strip()
if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', version):
    raise ValueError('VERSION must be vMAJOR.MINOR.PATCH')
print('#pragma once\n#define ALTSERVER_VERSION "' + version + '"')
