#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ "$EUID" -eq 0 ]] || { echo "Ejecuta con sudo: $0" >&2; exit 1; }
. /etc/os-release
[[ "${ID:-}" == "linuxmint" || "${ID_LIKE:-}" == *ubuntu* ]] || { echo "Este instalador está destinado a Linux Mint/Ubuntu." >&2; exit 2; }
apt-get update
apt-get install -y python3 systemd util-linux
install -d -m 0755 /usr/libexec/compresso /usr/local/bin /etc/compresso /usr/share/doc/compresso-hal /etc/modules-load.d
install -m 0755 "$ROOT/src/compresso/memoryd.py" /usr/libexec/compresso/memoryd.py
install -m 0644 "$ROOT/src/compresso/metrics.py" /usr/libexec/compresso/metrics.py
install -m 0755 "$ROOT/src/compresso/benchmark.py" /usr/libexec/compresso/benchmark.py
install -m 0755 "$ROOT/src/compresso/supervisor.py" /usr/libexec/compresso/supervisor.py
install -m 0755 "$ROOT/scripts/compressoctl" /usr/local/bin/compressoctl
install -m 0644 "$ROOT/config/memory.conf" /etc/compresso/memory.conf
printf 'zram\n' > /etc/modules-load.d/compresso-zram.conf
install -m 0755 "$ROOT/scripts/metrics.sh" /usr/libexec/compresso/metrics.sh
install -m 0755 "$ROOT/scripts/healthcheck.sh" /usr/libexec/compresso/healthcheck.sh
install -m 0644 "$ROOT/systemd/compresso-memoryd.service" /etc/systemd/system/
install -m 0644 "$ROOT/systemd/compresso-metricsd.service" /etc/systemd/system/
install -m 0644 "$ROOT/systemd/compresso-supervisord.service" /etc/systemd/system/
cp "$ROOT/README.md" /usr/share/doc/compresso-hal/README.md
systemctl daemon-reload
echo "Instalado sin activar servicios. Revisa /etc/compresso/memory.conf."
echo "Ejecuta python3 /usr/libexec/compresso/memoryd.py --dry-run antes de activar."
echo "Métricas de solo lectura: compressoctl metrics"
echo "Diagnóstico de solo lectura: compressoctl doctor"
echo "Coordina cualquier zram-generator/zram-tools existente antes de activar."
