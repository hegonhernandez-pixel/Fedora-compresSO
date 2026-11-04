# Buildroot external tree — experimental scaffold

This tree is a packaging scaffold, not a complete defconfig or Mint ISO builder. Pin an exact Buildroot release and kernel before enabling it. Validate package paths and Kconfig against that release.

Buildroot produces an independent Linux image; it does not build Linux Mint. The Mint target uses native Debian/Ubuntu packaging and its own live-image workflow.