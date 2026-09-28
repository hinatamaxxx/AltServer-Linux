#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
test -s dist/AltServer-x86_64
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
bundle="$stage/AltServer-Linux"
mkdir -p "$bundle/dist"
cp -R install.sh scripts config docs LICENSE LICENSE.autorecover README.md README.en.md "$bundle/"
cp dist/AltServer-x86_64 "$bundle/dist/"
(cd "$bundle/dist" && sha256sum AltServer-x86_64 >SHA256SUMS)
tar -C "$stage" -czf dist/AltServer-Linux-amd64-setup.tar.gz AltServer-Linux
(cd dist && sha256sum AltServer-x86_64 AltServer-Linux-amd64-setup.tar.gz >SHA256SUMS)
