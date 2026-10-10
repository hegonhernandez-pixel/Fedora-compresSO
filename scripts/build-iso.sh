#!/usr/bin/env bash
set -euo pipefail

RELEASE="40"
KS_FILE="/workspace/kickstarts/fedora-gpu-live.ks"

echo "==> Iniciando construcción en contenedor..."

# Asegurarse de que el directorio out NO exista previamente dentro del contenedor
podman run --privileged --rm \
  -v "$(pwd)":/workspace:Z \
  -w /workspace \
  registry.fedoraproject.org/fedora:${RELEASE} \
  bash -c "
    set -euo pipefail
    
    # 1. Instalar lorax, anaconda y herramientas necesarias para --no-virt
    dnf install -y lorax anaconda anaconda-install-env-deps livecd-tools dnf-plugins-core
    
    # 2. Asegurarse de que /workspace/out no exista antes de llamar a livemedia-creator
    rm -rf /workspace/out
    
    # 3. Compilar la ISO
    livemedia-creator \
      --ks=${KS_FILE} \
      --no-virt \
      --resultdir=/workspace/out \
      --project='Fedora compresSO Engine' \
      --make-iso \
      --volid='Fedora-compresSO' \
      --iso-name='Fedora-compresSO-x86_64.iso'
  "

echo "==> Construcción finalizada con éxito."
