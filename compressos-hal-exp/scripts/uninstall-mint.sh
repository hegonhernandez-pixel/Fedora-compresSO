#!/bin/bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo" >&2; exit 1; }
systemctl disable --now compresso-memoryd.service 2>/dev/null || true
rm -f /etc/modules-load.d/compresso-zram.conf /etc/systemd/system/compresso-memoryd.service
rm -rf /usr/libexec/compresso /usr/share/doc/compresso-hal
systemctl daemon-reload
echo "Servicio retirado; configuración preservada. No se ejecutó swapoff."