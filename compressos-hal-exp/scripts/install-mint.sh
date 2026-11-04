#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo" >&2; exit 1; }
. /etc/os-release
[[ ${ID:-} == linuxmint || ${ID_LIKE:-} == *ubuntu* ]] || { echo "Requiere Linux Mint/Ubuntu"; exit 2; }
apt-get update
apt-get install -y python3 systemd util-linux
install -d -m 0755 /usr/libexec/compresso /etc/compresso /usr/share/doc/compresso-hal /etc/modules-load.d
install -m 0755 "$ROOT/src/compresso/memoryd.py" /usr/libexec/compresso/memoryd.py
install -m 0644 "$ROOT/config/memory.conf" /etc/compresso/memory.conf
printf 'zram\n' > /etc/modules-load.d/compresso-zram.conf
install -m 0644 "$ROOT/systemd/compresso-memoryd.service" /etc/systemd/system/
cp "$ROOT/README.md" /usr/share/doc/compresso-hal/README.md
systemctl daemon-reload
echo "Instalado, NO activado. Revisa la configuración y ejecuta --dry-run."