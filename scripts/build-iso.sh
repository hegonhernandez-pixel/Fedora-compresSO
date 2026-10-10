#!/usr/bin/env bash
set -euo pipefail

RELEASE="40"
KS_FILE="kickstarts/fedora-gpu-live.ks"
OUTPUT_DIR="$(pwd)/out"

mkdir -p "${OUTPUT_DIR}"

echo "==> Iniciando construcción de Fedora GPU ISO (F${RELEASE})..."

# Ejecutar livemedia-creator dentro de un contenedor Fedora oficial
podman run --privileged --rm \
  -v "$(pwd)":/workspace:Z \
  -v "${OUTPUT_DIR}":/out:Z \
  -w /workspace \
  registry.fedoraproject.org/fedora:${RELEASE} \
  bash -c "
    dnf install -y lorax livecd-tools dnf-plugins-core
    livemedia-creator \
      --ks=${KS_FILE} \
      --no-virt \
      --resultdir=/out \
      --project='Fedora GPU Engine' \
      --make-iso \
      --volid='Fedora-GPU-F${RELEASE}' \
      --iso-name='Fedora-GPU-F${RELEASE}-x86_64.iso'
  "

echo "==> ISO construida con éxito en: ${OUTPUT_DIR}/"
