#!/usr/bin/env bash
# =======================================================
# DISTRO BUILDER (scripts/mk_distro_utils.sh)
# Fedora compresSO: GPU-Accelerated Live ISO Builder
# =======================================================
set -euo pipefail

SPEC_FILE="spec/distro.spec"
BUILD_ROOT="/tmp/fedora_gpu_rootfs"
ISO_DIR="/tmp/iso_staging"
OUTPUT_DIR="$(pwd)/out"
ISO_NAME="Fedora_compresSO_Live-x86_64.iso"

if [ ! -f "$SPEC_FILE" ]; then
    echo "[!] Error: No se encuentra $SPEC_FILE."
    exit 1
fi

echo "[+] Limpiando áreas de montaje..."
rm -rf "$BUILD_ROOT" "$ISO_DIR" "$OUTPUT_DIR"
mkdir -p "$BUILD_ROOT" "$ISO_DIR/LiveOS" "$ISO_DIR/isolinux" "$OUTPUT_DIR"

echo "[+] Inicializando descarga de paquetes Fedora 40 para el RootFS..."
dnf install --installroot="$BUILD_ROOT" --releasever=40 \
    --setopt=install_weak_deps=False -y \
    @core kernel kernel-modules mesa-vulkan-drivers libdrm amdgpu-firmware vulkan-loader \
    enlightenment lightdm retroarch alsa-utils alsa-lib \
    firefox nautilus gnome-disk-utility btrfs-progs zram-generator squashfs-tools grub2-efi xorriso

# 1. Configurar LightDM con auto-login a Enlightenment
echo "[+] Configurando LightDM auto-login..."
LIGHTDM_CONF="$BUILD_ROOT/etc/lightdm/lightdm.conf"
mkdir -p "$(dirname "$LIGHTDM_CONF")"
cat << 'EOF' > "$LIGHTDM_CONF"
[Seat:*]
autologin-user=liveuser
autologin-user-session=enlightenment
EOF

# Crear usuario live
chroot "$BUILD_ROOT" useradd -m -G wheel -s /bin/bash liveuser || true
chroot "$BUILD_ROOT" passwd -d liveuser || true

# 2. Configurar ZRAM para deduplicación/compresión
cat << 'EOF' > "$BUILD_ROOT/etc/systemd/zram-generator.conf"
[zram0]
zram-size = min(ram / 2, 4096)
compression-algorithm = lz4
EOF

# 3. Inyección del parche/shim ld.so (si existe en el repo)
if [ -f "./glibc-patch/ld.so.c" ]; then
    echo "[+] Integrando parche de ld.so en el entorno..."
    mkdir -p "$BUILD_ROOT/usr/share/compresso/"
    cp ./glibc-patch/ld.so.c "$BUILD_ROOT/usr/share/compresso/"
fi

# 4. Inyección del Compute Shader SPIR-V en el RootFS
if [ -f "./shaders/ans_decompress.comp" ]; then
    echo "[+] Registrando Compute Shaders en /usr/share/vulkan/shaders..."
    mkdir -p "$BUILD_ROOT/usr/share/vulkan/shaders"
    cp ./shaders/ans_decompress.comp "$BUILD_ROOT/usr/share/vulkan/shaders/"
fi

# 5. Generar imagen SquashFS del RootFS
echo "[+] Comprimiendo RootFS en squashfs (LiveOS/squashfs.img)..."
mksquashfs "$BUILD_ROOT" "$ISO_DIR/LiveOS/squashfs.img" -comp xz -b 1048576

# 6. Copiar Kernel e Initramfs al directorio de arranque de la ISO
cp "$BUILD_ROOT"/boot/vmlinuz-* "$ISO_DIR/isolinux/vmlinuz"
cp "$BUILD_ROOT"/boot/initramfs-*.img "$ISO_DIR/isolinux/initrd.img"

# 7. Configuración de GRUB2 para booteo en memoria
mkdir -p "$ISO_DIR/boot/grub2"
cat << 'EOF' > "$ISO_DIR/boot/grub2/grub.cfg"
set default="0"
set timeout=5

menuentry "Fedora compresSO (Enlightenment + GPU Engine Live)" {
    linux /isolinux/vmlinuz root=live:CDLABEL=COMPRESSO rd.live.image quiet radeon.modeset=1 amdgpu.modeset=1
    initrd /isolinux/initrd.img
}
EOF

# 8. Empaquetado final con xorriso (BIOS + UEFI compatible)
echo "[+] Generando ISO híbrida con xorriso..."
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "COMPRESSO" \
    -output "$OUTPUT_DIR/$ISO_NAME" \
    -graft-points \
    /="$ISO_DIR"

echo "[✓] ISO generada con éxito: $OUTPUT_DIR/$ISO_NAME"
