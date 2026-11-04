# CompressOS-HAL EXP

Experimental Linux Mint XFCE integration for ZRAM, Zswap and hybrid profiles. Target platform: Linux Mint 22.3 XFCE (Ubuntu 24.04 base); compatibility must still be confirmed on a real Mint 22.3 installation. This package does **not** build or remaster a Linux Mint ISO. Install official Linux Mint XFCE first, then install this package on that system. Buildroot is an auxiliary packaging path for standalone components, not a Mint ISO builder.

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

## Read-only supervisor and control CLI

After installing the package, `compressoctl` provides read-only inspection commands:

```bash
compressoctl status
compressoctl doctor
compressoctl metrics
compressoctl benchmark --profile zram-fast --memory-mib 32 --output /var/tmp/zram-fast.json
```

The supervisor compares the configured profile with active swap devices and observed ZRAM/Zswap kernel state. Exit codes: 0 healthy, 1 warning, 2 critical/error. The `compresso-supervisord.service` health check uses this inspector and does not repair or mutate system state.

There are deliberately no `enable`, `disable`, `swapoff` or profile-switch commands in this CLI. Profile changes remain a manual configuration/reboot operation until a separate, guarded live-transition design has been validated. Do not run multiple ZRAM managers simultaneously.

## Bounded profile benchmark

The benchmark runs five identical, short memory-allocation samples and records elapsed time, child-process page faults, swap I/O counter deltas and memory PSI total deltas. It does not activate, deactivate or switch profiles. Set the desired profile in `/etc/compresso/memory.conf`, reboot, verify the active profile and swap layout, then run one report per profile. Use the same workload size for comparable trials.

The workload is capped at 128 MiB and at 10% of currently available memory (whichever is smaller); it refuses to run if `MemAvailable` is missing or too low. It is a controlled allocation/page-touch test, not a claim of gaming or application performance.

```bash
sudo python3 /usr/libexec/compresso/benchmark.py --profile zram-fast --memory-mib 32 --output /var/tmp/compresso-zram-fast.json
```

Repeat after manually configuring and rebooting into `zswap-first` and `hybrid-exp`, using the corresponding `--profile` label and a separate output filename. Do not change profiles while the machine is under load. Compare the five samples and the telemetry deltas; do not infer a performance winner from a single run.

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
