# EXP implementation plan and affected files

## Current package
- src/compresso/memoryd.py: sole writer for swap profile setup.
- config/memory.conf: strict configuration input.
- systemd/compresso-memoryd.service: privileged oneshot service.
- scripts/install-mint.sh and uninstall-mint.sh: Mint integration.
- tests/test_memoryd.py: configuration safety tests.
- buildroot-external/: initial external-tree/package scaffolding.
- .github/workflows/tests.yml: CI entrypoint.

## Next changes
- Add fake-sysfs integration fixtures for Zswap-only and hybrid writes.
- Add read-only metricsd and health reporting; neither may write sysfs.
- Pin Buildroot release and validate paths/Kconfig against that release.
- Add a Mint live-image workflow only after choosing a Mint-compatible customization method.
- Add Vulkan runtime only after CPU reference tests, SPIR-V validation, bounded buffers and output-equivalence tests.

## Safety
The daemon refuses an already active ZRAM device. It does not hot-switch profiles, create swapfiles, call swapoff, or monitor memory pressure. Activation is separate from installation.