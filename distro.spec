#version 450

// Tamaño del grupo de trabajo: 256 hilos ejecutando en paralelo por bloque[cite: 1, 3]
layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

// Búfer de entrada con datos supercomprimidos[cite: 3]
layout(std430, binding = 0) readonly buffer CompressedStorage {
    uint compressed_stream[];
};

// Búfer de salida mapeado en VRAM (Host-Visible)[cite: 3]
layout(std430, binding = 1) writeonly buffer DecompressedStorage {
    uint decompressed_stream[];
};

// Parámetros de control de balanceo y diccionarios[cite: 3]
layout(push_constant) uniform SchedulingConfig {
    uint block_size;
    uint dictionary_size;
    uint is_game_mode;
} config;

shared uint local_dictionary[1024];

uint decode_pattern(uint symbol) {
    uint pattern_key = symbol & 0x03FF;
    uint raw_value = local_dictionary[pattern_key];
    return raw_value ^ (symbol >> 10);
}

void main() {
    uint local_id  = gl_LocalInvocationID.x;
    uint group_id  = gl_WorkGroupID.x;
    uint global_id = gl_GlobalInvocationID.x;

    // Fallback dinámico si la GPU está ocupada por juegos/gráficos pesados
    if (config.is_game_mode == 1 && config.block_size < 4194304) {
        return; 
    }

    for (uint i = local_id; i < config.dictionary_size; i += 256) {
        local_dictionary[i] = compressed_stream[i];
    }
    memoryBarrierShared();
    barrier();

    uint stream_offset = config.dictionary_size + global_id;
    if (stream_offset < config.block_size) {
        uint encoded_symbol = compressed_stream[stream_offset];
        decompressed_stream[global_id] = decode_pattern(encoded_symbol);
    }
}
```[cite: 3]

---

## 4. Orquestación y Receta de Construcción (`distro.spec`)
Para empaquetar todo el sistema base de Red Hat/Fedora con entornos ligeros (como XFCE) y el motor Vulkan integrado desde el arranque:

```ini
[Core_System]
Base_OS = RedHat_Minimal
Kernel_Version = 6.x-custom-vram
Initramfs_Engine = Vulkan_Early_Boot

[Core_Libraries]
Graphics_Drivers = mesa-vulkan-drivers, libdrm, vulkan-loader, vulkan-headers
Core_Utilities = zram-generator, btrfs-progs, xz, cpio, grub2-efi

[Desktop_Environments]
Default_Desktop = xfce
Available_Desktops = xfce, lxqt

[XFCE_Packages]
Base = xfce4-session, xfce4-panel, xfwm4, xfce4-terminal, thunar
Display_Manager = lightdm, lightdm-gtk-greeter

[Emulation_Layers]
Enable_Proton = true
Enable_LXD_Containers = true
Packages = lxd, wine-core, dxvk-native
```[cite: 1]
