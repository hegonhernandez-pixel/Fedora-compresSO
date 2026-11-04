# Linux Mint XFCE integration

Target is Linux Mint XFCE. “Mint 24” is not a valid Mint release identifier; record the actual release using /etc/linuxmint/info and /etc/os-release.

This package installs services into an existing Mint system; it does not regenerate the official Mint ISO. Buildroot packages standalone components for independent Linux images, not Mint XFCE.

Validation:
1. Boot official Mint XFCE in a disposable VM.
2. Record release, kernel, RAM, CPU and VM configuration.
3. Install but do not activate this package.
4. Inspect systemctl list-unit-files and /proc/swaps.
5. Identify/coordinate zram-tools, zramswap or systemd-zram-generator before enabling this daemon.
6. Run python3 /usr/libexec/compresso/memoryd.py --dry-run.
7. Test one profile at a time; preserve journal, /proc/swaps, /proc/vmstat, ZRAM mm_stat, PSI and workload metrics.
8. Consider custom live image work only after documenting a Mint-compatible workflow and licensing.

Do not activate on a host with unsaved work before VM validation.