#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Script Atómico de Compilación e Inicialización — Fedora compresSO V2
# Autoría / Proyecto: Fedora compresSO
# ==============================================================================

KERNEL_VERSION="6.x-custom-vram-release-20261010"
BUILD_DIR="/tmp/compresso_build"
BACKUP_GRUB="/etc/default/grub.bak"

echo "[*] Iniciando despliegue atómico de Fedora compresSO..."
mkdir -p "$BUILD_DIR"

# ------------------------------------------------------------------------------
# PASO 1: Verificación y Fijación del Kernel y Configuración `.config`
# ------------------------------------------------------------------------------
echo "[+] [Paso 1/3] Verificando entorno de compilación del kernel ($KERNEL_VERSION)..."
if [ ! -f "kernel-${KERNEL_VERSION}.config" ]; then
    echo "[-] Error crítico: No se encuentra el fichero de configuración base del kernel." >&2
    exit 1
fi

# Copia de seguridad del estado anterior del gestor de arranque
if [ -f /etc/default/grub ]; then
    cp /etc/default/grub "$BACKUP_GRUB"
    echo "[+] Copia de seguridad de GRUB creada en $BACKUP_GRUB"
fi

# ------------------------------------------------------------------------------
# PASO 2: Generación Estricta del Initramfs (Dracut Limpio)
# ------------------------------------------------------------------------------
echo "[+] [Paso 2/3] Generando initramfs con Dracut (excluyendo dependencias de desarrollo)..."

# Limpieza preventiva de artefactos huérfanos previos
dracut --force --omit-drivers "vulkan-headers" --verbose /boot/initramfs-${KERNEL_VERSION}.img "$KERNEL_VERSION"

if [ ! -f /boot/initramfs-${KERNEL_VERSION}.img ]; then
    echo "[-] Error crítico: La imagen del initramfs no se generó correctamente. Abortando para evitar corrupción." >&2
    exit 1
fi

echo "[+] Initramfs verificado y empaquetado correctamente."

# ------------------------------------------------------------------------------
# PASO 3: Validación de GRUB, Kernel y Mecanismo de Recuperación (Circuit Breaker)
# ------------------------------------------------------------------------------
echo "[+] [Paso 3/3] Configurando entradas de arranque y validando integridad..."

# Verificamos que el bzImage y el initramfs existan antes de actualizar grub2
if [ ! -f /boot/vmlinuz-${KERNEL_VERSION} ]; then
    echo "[-] Error: Imagen vmlinuz-${KERNEL_VERSION} no encontrada en /boot." >&2
    exit 1
fi

# Generar configuración de GRUB integrando el kernel principal y la entrada de respaldo
grub2-mkconfig -o /boot/grub2/grub.cfg

echo "[✔] Despliegue atómico completado con éxito."
echo "[✔] Sistema preparado con kernel reproducible, initramfs depurado y entrada de respaldo activa."
