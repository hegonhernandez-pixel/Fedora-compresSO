#!/usr/bin/env bash
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-./CompressOS-HAL-EXP}"
mkdir -p "$DEST"
for item in README.md LICENSE docs src tests config systemd scripts buildroot-external .github; do
 [[ -e "$SRC/$item" ]] && cp -a "$SRC/$item" "$DEST/"
done
find "$DEST/scripts" -type f -name '*.sh' -exec chmod 0755 {} +
chmod 0755 "$DEST/src/compresso/memoryd.py"
echo "Estructura creada en $DEST"