Fedora compresSO — Especificación de Arquitectura Corregida y Manifiesto de Compilación (V2)
Fecha de actualización: 10 de octubre de 2026
Estado de auditoría: Cierre de riesgos críticos (FCS-001 al FCS-008 resueltos)


1. Resolución de Riesgos Críticos y Arquitectura de Arranque
FCS-001 — Rol de Vulkan en el Arranque Temprano (Corregido)
Principio: El kernel y el initramfs estándar de Linux controlan el proceso inicial de arranque (/sbin/init y montaje de sistemas de ficheros virtuales).
Ajuste: Se retira la dependencia obligatoria de Vulkan para montar el almacenamiento raíz. Vulkan se inicializa de forma diferida (lazy loading) únicamente tras la transición al espacio de usuario en fase de servicios systemd (sysinit.target), evitando un punto único de fallo (SPOF) si el hardware gráfico no está disponible.
Ruta alternativa (Circuit Breaker): Si falla la inicialización de la instancia Vulkan o el controlador gráfico (amdgpu / i915 / xe), el demonio de descompresión conmuta automáticamente a CPU utilizando instrucciones vectoriales (AVX-512) y LZ4/ANS por software.
FCS-002 — Reproducibilidad del Kernel (6.x-custom-vram)
Base de compilación: Kernel Linux base derivado de Red Hat Enterprise Linux / Fedora Minimal (kernel-core-6.x.custom).
Parches aplicados:
Integración del controlador de memoria virtual extendida (ZONE_VRAM_ZRAM).
Parches de redirección P2P PCIe para transferencia directa NVMe ➔ VRAM (Host-Visible Coherent Memory).
Control de versiones: Todo artefacto de kernel generado debe incluir el hash exacto del commit del repositorio y el fichero de configuración .config empaquetado junto al bzImage. Se mantiene siempre una entrada de respaldo (kernel-core-fedora-fallback) en GRUB.
FCS-003 & FCS-006 — Manifiesto Estricto del Initramfs y Controladores
Se separan taxativamente las dependencias de compilación y de ejecución en el initramfs mediante dracut:

Paquetes esenciales de ejecución (Initramfs Core):
kernel-core, dracut-core, btrfs-progs, zram-generator, xz, cpio, grub2-efi.
Controladores gráficos (Carga diferida en espacio de usuario):
mesa-vulkan-drivers, libdrm, vulkan-loader. (Los vulkan-headers se eliminan por completo del initramfs de producción al tratarse de herramientas exclusivamente de desarrollo).
FCS-004 — Parámetros de Compresión y Métricas
Algoritmos soportados:
Nivel de compresión estática en almacenamiento (NVMe): XZ (Preset 6e) / ANS optimizado para bloques de diccionarios de patrones de 4MB a 8MB.
Compresión dinámica en RAM: ZRAM con algoritmo zstd (nivel 3) para optimización de memoria libre.
Métricas de validación: Tiempo de arranque en frío (systemd-analyze), uso pico de RAM en initramfs (< 180 MB) y tasa de transferencia por bus PCIe.
FCS-005 & FCS-008 — Recuperación, Pruebas y Automatización
Seguridad de Arranque: Verificación obligatoria de integridad de ficheros del kernel e initramfs antes de actualizar la tabla de arranque de GRUB. Si el sistema detecta un fallo de kernel panic en el primer arranque, el gestor de arranque revierte automáticamente a la partición de rescate.
Matriz de Pruebas Automatizadas: Compilación mediante script de integración continua que ejecuta pruebas de arranque en QEMU/KVM antes de empaquetar la ISO final.


2. Especificación Técnica Actualizada (distro.spec V2)
[Core_System]

Base_OS = RedHat_Minimal

Kernel_Version = 6.x-custom-vram-release-20261010

Initramfs_Engine = Standard_Dracut_Lazy_Vulkan

Fallback_Kernel = enabled

[Core_Libraries_Execution]

Storage_Drivers = btrfs, ext4, nvme, ahci

Core_Utilities = zram-generator, btrfs-progs, xz, cpio, grub2-efi, libdrm

Graphics_Runtime = mesa-vulkan-drivers, vulkan-loader

[Desktop_Environment]

Default_Desktop = xfce4

Components = xfce4-session, xfce4-panel, xfwm4, xfce4-terminal, thunar, lightdm, lightdm-gtk-greeter

[Emulation_Layers]

Enable_Proton = true

Enable_LXD_Containers = true

Packages = lxd, wine-core, dxvk-native


3. Plan de Ejecución Inmediata
Paso 1: Generar el initramfs depurado excluyendo las cabeceras de desarrollo de Vulkan (vulkan-headers).
Paso 2: Compilar el kernel 6.x-custom-vram fijando la configuración .config reproducible.
Paso 3: Validar la entrada de recuperación en GRUB2 y realizar la prueba de arranque en máquina virtual con simulación de fallo gráfico (verificación del Circuit Breaker a CPU).
