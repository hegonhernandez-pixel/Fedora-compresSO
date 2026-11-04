# Buildroot migration — project decision and integration boundary

**Status:** Proposed migration, EXP phase.

The existing repository is a Fedora-oriented prototype: Kickstart files, Fedora package names, Lorax/live-media scripts and a Fedora container workflow are present. These cannot be reused as if they were Buildroot configuration. The repository history also contains inconsistent Fedora 39/40 declarations and incomplete/duplicated build scripts; preserve them for reference until the new build is proven.

## Proposed layout

```text
buildroot-external/
├── Config.in
├── external.desc
├── external.mk
├── configs/
│   └── compresso_x86_64_defconfig
├── board/compresso/
│   ├── linux/
│   │   └── compresso_kernel.fragment
│   └── rootfs-overlay/
│       ├── etc/compresso/
│       └── usr/
│           ├── libexec/
│           └── lib/systemd/system/
└── package/
    ├── compresso-memoryd/
    ├── compresso-metricsd/
    └── compresso-shaderd/
```

The initial implementation must pin an exact Buildroot release/commit and exact Linux kernel version. The defconfig must be generated and checked with that pinned Buildroot tree; do not guess Kconfig symbols across releases.

## ISO build

Use Buildroot's x86/x86-64 ISO9660 filesystem image support and its documented bootloader choice. Buildroot's manual states that ISO image support is available for x86/x86-64 when Buildroot builds the kernel. Validate the result in QEMU before publishing an artifact.

## Existing Fedora files

Do not delete or silently rewrite:
- `.github/workflows/build-iso.yml`
- `kickstarts/fedora-gpu-live.ks`
- `scripts/build-iso.sh`
- `scripts/mk_distro_utils.sh`
- `build_and_deploy_vram_os.sh`
- `distro.spec`

The Buildroot workflow should be a separate workflow and should not publish over Fedora artifacts.

## Mint naming correction

The official Linux Mint release list currently identifies the 22.x series (including 22.3), not a Linux Mint 24 release. Confirm whether “Mint 24” means Linux Mint 22.x based on Ubuntu 24.04, or whether Mint is only the host/test environment. Do not label a custom Buildroot ISO as Linux Mint.

## Migration acceptance

- Buildroot release and kernel commit are pinned.
- External tree passes `make BR2_EXTERNAL=... compresso_x86_64_defconfig` and `make olddefconfig`.
- Root filesystem and ISO build from a clean checkout.
- ISO boots in QEMU in BIOS/UEFI modes as configured.
- Memory profile defaults to safe ZRAM-only or disabled mode.
- Existing Fedora workflow remains unchanged until Buildroot CI is green.
