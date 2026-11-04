# CompressOS-HAL Buildroot external tree (EXP)

This directory is the reserved integration point for the Buildroot migration. It is intentionally a design placeholder until the project pins an exact Buildroot release and Linux kernel version.

Do not run a production build from this placeholder. The external-tree metadata, package recipes, defconfig and kernel fragment will be added in the implementation subphase after the target image decision is confirmed.

See:
- [Buildroot migration](../docs/experimental/BUILDROOT-MIGRATION.md)
- [Memory architecture](../docs/experimental/EXP-001-memory-architecture.md)
- [Daemon I/O contract](../docs/experimental/EXP-003-daemon-io-contract.md)
