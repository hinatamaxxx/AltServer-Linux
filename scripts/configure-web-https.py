#!/usr/bin/env python3
"""Configure owner-only initial enrollment behind Tailscale Serve."""
import json
import os
from pathlib import Path
import shlex
import subprocess

status = json.loads(subprocess.check_output(['tailscale', 'status', '--json']))
node = status['Self']
domain = node['DNSName'].rstrip('.')
owner = status['User'][str(node['UserID'])]['LoginName']
if not domain.endswith('.ts.net') or not owner or '\n' in owner:
    raise SystemExit('A user-owned Tailscale node with a DNS name is required')
existing = json.loads(subprocess.check_output(['tailscale', 'serve', 'status', '--json']))
web = existing.get('Web', {}).get(domain + ':443', {})
if web and web.get('Handlers') != {'/': {'Proxy': 'http://127.0.0.1:8787'}}:
    raise SystemExit('Port 443 already serves another app; existing configuration preserved')
try:
    subprocess.run(['tailscale', 'serve', '--bg', '--https=443', 'http://127.0.0.1:8787'], check=True, timeout=25)
except subprocess.TimeoutExpired:
    raise SystemExit('Enable HTTPS using the Tailscale URL above, then rerun. Leave Funnel disabled.')
path = Path('/etc/altserver-webui.env')
temporary = path.with_suffix('.tmp')
fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write('WEBUI_LISTEN=127.0.0.1\nWEBUI_PORT=8787\n')
    stream.write('WEBUI_ORIGIN=https://' + domain + '\nWEBUI_OWNER=' + shlex.quote(owner) + '\n')
os.replace(temporary, path)
print('Passkey enrollment: https://' + domain)
