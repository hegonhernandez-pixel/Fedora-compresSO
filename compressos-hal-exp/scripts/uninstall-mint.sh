#!/bin/bash
set -euo pipefail
[[ "$EUID" -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
systemctl disable --now compresso-memoryd.service compresso-metricsd.service compresso-supervisord.service 2>/dev/null || true
rm -f /etc/modules-load.d/compresso-zram.conf
rm -f /etc/systemd/system/compresso-memoryd.service /etc/systemd/system/compresso-metricsd.service /etc/systemd/system/compresso-supervisord.service
rm -rf /usr/libexec/compresso /usr/share/doc/compresso-hal
# Preserve user configuration; never issue swapoff automatically.
systemctl daemon-reload
echo "Services removed. /etc/compresso/memory.conf is preserved; no swapoff was run."
