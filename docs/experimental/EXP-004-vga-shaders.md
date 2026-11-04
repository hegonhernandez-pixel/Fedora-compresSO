# EXP-004 — VGA / GPU shader integration

**Status:** Experimental plan; not part of the boot-critical path.

## Terminology

“VGA shader” is not a standard Linux kernel subsystem. This experiment interprets it as a GPU compute/graphics shader path using Vulkan (and, if needed, a separate OpenGL path). It does not mean modifying a VGA BIOS or making a GPU responsible for kernel memory management.

## Required separation

1. Kernel DRM/KMS driver initializes display output.
2. Mesa userspace driver and Vulkan loader provide the userspace API.
3. `vulkaninfo` verifies device and API availability.
4. Shader source is compiled to SPIR-V with `glslangValidator`.
5. `spirv-val` validates the SPIR-V module.
6. `compresso-shaderd` dispatches only a bounded, explicitly selected workload.
7. CPU implementation remains the required fallback.

GPU detection, Vulkan initialization or shader compilation failure must never prevent root filesystem mount, login or memory setup.

## Shader prototype audit

The shader prototype previously present in project notes is not a working decompressor yet:
- The symbol decoder and dictionary format are not a specified compression format.
- Shared dictionary bounds are not proven against the declared 1024 entries.
- The code must validate all source and destination buffer ranges.
- The game-mode early return is not a scheduling or preemption mechanism.
- No host-side Vulkan pipeline, descriptor layout, synchronization, memory ownership or output validation has been supplied.

Do not install or dispatch that shader as a production component.

## EXP validation

- Record GPU vendor, device, driver, Mesa and Vulkan versions.
- Verify a CPU-only boot and display path.
- Compile and validate a trivial known shader before any decompression shader.
- Compare GPU output byte-for-byte against a trusted CPU implementation on fixed test vectors.
- Test unsupported GPU, missing Vulkan loader, shader compile error, device loss and memory pressure.
- Bound VRAM allocation and execution time; shader worker is optional and restart-isolated.

## Linux Mint / Buildroot distinction

Buildroot can generate an x86/x86-64 Live CD ISO when its kernel and ISO9660 image options are configured. It does not rebuild a Linux Mint desktop ISO. If Linux Mint is the intended installed desktop, test the GPU tools and shader runtime on that Mint installation separately; the custom Buildroot image remains a separate artifact.
