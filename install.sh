#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  case "${1:-}" in
    --help|-h) echo 'Usage: sudo sh install.sh [--prepare|--configure]'; exit 0 ;;
  esac
  [ "$(id -u)" = 0 ] || { echo 'Run with sudo' >&2; exit 1; }
  . /etc/os-release
  case "$ID:$VERSION_ID" in
    debian:12|debian:13) ;;
    *) echo 'Debian 12/13 is required' >&2; exit 1 ;;
  esac
  [ "$(uname -m)" = x86_64 ] && [ -d /run/systemd/system ] || {
    echo 'An amd64 systemd host is required' >&2; exit 1;
  }
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3 ca-certificates
fi
exec python3 "$root/scripts/setup.py" "$@"
