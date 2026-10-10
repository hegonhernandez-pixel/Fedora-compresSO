# fedora-gpu-live.ks - Fedora compresSO Live Engine
version=F40

lang en_US.UTF-8
keyboard us
timezone UTC
selinux --disabled
firewall --enabled --service=mdns
network --bootproto=dhcp --device=link --activate

# Repositorios Oficiales Fedora 40
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-40&arch=x86_64
repo --name=fedora --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-40&arch=x86_64
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f40&arch=x86_64

# Repositorios RPM Fusion (Códecs, Drivers, Emuladores)
repo --name=rpmfusion-free --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=free-fedora-40&arch=x86_64
repo --name=rpmfusion-free-updates --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=free-fedora-updates-released-40&arch=x86_64
repo --name=rpmfusion-nonfree --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=nonfree-fedora-40&arch=x86_64
repo --name=rpmfusion-nonfree-updates --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=nonfree-fedora-updates-released-40&arch=x86_64

%packages
@core
@base-x
kernel
kernel-modules
kernel-modules-extra

# Drivers gráficos y soporte Vulkan/Compute
mesa-dri-drivers
mesa-vulkan-drivers
vulkan-loader
vulkan-tools
libdrm
pciutils

# Entorno Ligero: Enlightenment + LightDM
enlightenment
terminology
lightdm
lightdm-gtk

# Utilidades solicitadas
nautilus
alsa-utils
alsa-lib
retroarch

# Herramientas de compresión y memoria
zram-generator
btrfs-progs
squashfs-tools
%end

%post
# Configuración gráfica predeterminada
systemctl set-default graphical.target
systemctl enable lightdm.service

# Configuración básica de ZRAM para compresión en memoria
cat << 'EOF' > /etc/systemd/zram-generator.conf
[zram0]
zram-size = min(ram / 2, 4096)
compression-algorithm = lz4
EOF
%end
