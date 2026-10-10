# =======================================================
# CONFIGURACIÓN DE CONSTRUCCIÓN DE LA DISTRIBUCIÓN (distro.spec)
# =======================================================

[Core_System]
Base_OS = Fedora_39_Minimal
Kernel_Version = 6.8.0-custom-vram
Initramfs_Engine = Vulkan_Early_Boot_Safe

[Core_Libraries]
# Runtime de Ejecución (Exclusivo para Initramfs / RootFS)
Runtime_Drivers = mesa-vulkan-drivers, libdrm, vulkan-loader
# Herramientas de Sistema
Core_Utilities = zram-generator, btrfs-progs, xz, cpio, grub2-efi

[Desktop_Environments]
Default_Desktop = xfce
Version = 4.18
Display_Manager = lightdm
Packages = xfce4-session, xfce4-panel, xfwm4, xfce4-terminal, thunar, lightdm-gtk-greeter

[Emulation_Layers]
Enable_Proton = true
Enable_LXD_Containers = true
Packages = lxd, wine-core, dxvk-native
