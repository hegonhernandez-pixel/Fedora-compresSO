# CompressOS-HAL EXP

Experimental Linux Mint XFCE integration for ZRAM, Zswap and hybrid profiles. This package does **not** build or remaster a Linux Mint ISO. Install official Linux Mint XFCE first, then install this package on that system. Buildroot is an auxiliary packaging path for standalone components, not a Mint ISO builder.

## Safety status

- Default profile: `zram-fast`.
- Installation does not enable or start any service.
- Inspect `/proc/swaps` and existing `zram-generator`/`zram-tools` configuration before activation; do not run two ZRAM managers.
- `zswap-first` requires an explicitly configured, existing `BACKING_SWAP`.
- `hybrid-exp` is experimental and may double-compress pages.
- The daemon refuses to reset a ZRAM device already active in `/proc/swaps`.
- No command in this package automatically runs `swapoff`.

## Install on an existing Linux Mint XFCE system

```bash
unzip CompressOS-HAL-EXP.zip
cd CompressOS-HAL-EXP
chmod +x scripts/*.sh
./scripts/test.sh
sudo ./scripts/install-mint.sh
```

Review `/etc/compresso/memory.conf`. Keep `PROFILE=zram-fast` for the first trial. Check the plan without applying it:

```bash
sudo python3 /usr/libexec/compresso/memoryd.py --dry-run
cat /proc/swaps
```

The installer does not enable the service. Only after reviewing the configuration and confirming there is no competing ZRAM manager, start it manually:

```bash
sudo systemctl start compresso-memoryd.service
sudo systemctl status compresso-memoryd.service --no-pager
cat /proc/swaps
```

To activate it automatically on subsequent boots, enable it after a successful manual test:

```bash
sudo systemctl enable compresso-memoryd.service
```

To prevent future automatic activation:

```bash
sudo systemctl disable compresso-memoryd.service
```

**Important distinction:** disabling or stopping this oneshot systemd service does not deactivate a swap device that it already configured. Do not assume `systemctl stop` is an undo operation. This experimental release intentionally does not automate `swapoff`; removing active swap can cause memory pressure or an out-of-memory event. For a clean rollback, disable the service and reboot after saving your work. Do not run `swapoff` while the device is in use or when you do not have sufficient available RAM and another working swap area.

## Read-only metrics

Print a JSON snapshot without changing kernel state:

```bash
sudo python3 /usr/libexec/compresso/metrics.py --stdout
```

Write the snapshot to the default location:

```bash
sudo systemctl start compresso-metricsd.service
sudo cat /run/compresso/metrics.json
```

The collector reads `/proc` and `/sys` only. Missing kernel interfaces are represented as null or omitted fields; they are not treated as fatal.

## Check status and diagnostics

```bash
sudo python3 /usr/libexec/compresso/memoryd.py --status
sudo /usr/libexec/compresso/healthcheck.sh
cat /proc/swaps
```

## Tests

From the source checkout:

```bash
./scripts/test.sh
```

This runs unit tests, Python compilation, and shell syntax checks. CI is configured in `.github/workflows/compresso-hal-exp-tests.yml`.

## Current limitations

- This is an experimental integration for an already-installed Mint system, not a custom Mint ISO.
- No real Mint VM or hardware validation is claimed.
- No safe live swap deactivation command is implemented.
- The benchmark engine, supervisor behavior, Buildroot validation and Mint ISO remastering remain future work.
- Vulkan shader runtime is not implemented.
