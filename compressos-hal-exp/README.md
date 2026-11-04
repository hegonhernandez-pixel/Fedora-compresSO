# CompressOS-HAL EXP

Experimental Linux Mint XFCE integration for ZRAM, Zswap and hybrid profiles. This package does not build a Mint ISO; Buildroot is an auxiliary packaging path for standalone components.

Safety: default profile is zram-fast; installation does not enable services. Inspect /proc/swaps and existing zram-generator/zram-tools before activation. zswap-first requires an existing BACKING_SWAP. hybrid-exp may double-compress pages. Never reset active ZRAM or automatically run swapoff under pressure.

Install: sudo ./scripts/install-mint.sh; review /etc/compresso/memory.conf; run python3 /usr/libexec/compresso/memoryd.py --dry-run; only then explicitly enable compresso-memoryd.service. Test with ./scripts/test.sh. No production or cross-platform validation is claimed.