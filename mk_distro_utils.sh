#!/usr/bin/env bash
# =======================================================
# DISTRO BUILDER UTILS (mk_distro_utils.sh)
# Automatiza la lectura de la especificación, creación del
# RootFS y traducción AOT de Fedora compresSO.
# =======================================================
set -e

SPEC_FILE="distro.spec"
BUILD_ROOT="/tmp/custom_rootfs"
ISO_OUTPUT="/tmp/Fedora_compresSO_Live.iso"

if [ ! -f "$SPEC_FILE" ]; then
    echo "[!] Error: No se encuentra el archivo de especificación $SPEC_FILE en el directorio actual."
    exit 1
fi

echo "[+] Leyendo especificaciones de $SPEC_FILE..."

# 1. Leer variables clave del archivo spec
DESKTOP_CHOICE=$(grep "Default_Desktop" $SPEC_FILE | head -n 1 | cut -d'=' -f2 | tr -d ' ')
RUNTIME_DRIVERS=$(grep "Runtime_Drivers" $SPEC_FILE | cut -d'=' -f2 | tr -d ' ')
CORE_UTILS=$(grep "Core_Utilities" $SPEC_FILE | cut -d'=' -f2 | tr -d ' ')
DESKTOP_PKGS=$(grep "Packages" $SPEC_FILE | tail -n 1 | cut -d'=' -f2 | tr -d ' ')
DISPLAY_MGR=$(grep "Display_Manager" $SPEC_FILE | head -n 1 | cut -d'=' -f2 | tr -d ' ')

ALL_PACKAGES="$RUNTIME_DRIVERS $CORE_UTILS $DESKTOP_PKGS $DISPLAY_MGR"

echo "[+] Entorno de escritorio seleccionado: $DESKTOP_CHOICE"
echo "[+] Paquetes a integrar en el RootFS:"
echo "    -> $ALL_PACKAGES"

# 2. Preparar el entorno RootFS temporal utilizando herramientas de Fedora (dnf)
echo "[+] Inicializando directorio raíz temporal en $BUILD_ROOT..."
sudo rm -rf "$BUILD_ROOT"
sudo mkdir -p "$BUILD_ROOT"

# Descarga e instalación de paquetes base en el chroot temporal
sudo dnf install --installroot="$BUILD_ROOT" --releasever=39 \
    --setopt=install_weak_deps=False -y $ALL_PACKAGES

# 3. Inyección de Instrucciones y Traducción AOT de Librerías
echo "[+] Ejecutando Traductor/Deduplicador AOT sobre el entorno..."
if [ -f "./src/aot_translator_engine" ]; then
    sudo ./src/aot_translator_engine --target-dir "$BUILD_ROOT/usr/lib64" \
                                   --inject-vram-hooks \
                                   --compress-ans
else
    echo "[!] Advertencia: Compilador AOT no encontrado en ./src/. Omitiendo fase de inyección de binarios por ahora."
fi

# 4. Habilitar servicios del sistema (LightDM)
echo "[+] Configurando servicios de inicio gráfico..."
sudo systemctl --root="$BUILD_ROOT" set-default graphical.target
sudo systemctl --root="$BUILD_ROOT" enable "$DISPLAY_MGR"

echo "========================================================"
echo " ¡RAÍZ DEL SISTEMA CONSTRUIDA Y TRADUCIDA CON ÉXITO!"
echo " Ubicación temporal del RootFS: $BUILD_ROOT"
echo "========================================================"
