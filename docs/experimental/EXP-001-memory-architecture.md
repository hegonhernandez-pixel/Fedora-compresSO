# EXP-001 — Fast-ZRAM + Zswap memory architecture

**Status:** Experimental design; not enabled by default  
**Target:** Buildroot-based CompressOS-HAL image  
**Branch:** exp/fast-zram-zswap-daemons

## Goals

- Provide a reproducible ZRAM swap device using the in-kernel `zram` driver.
- Evaluate Zswap as an optional compressed front cache for a backing swap device.
- Keep boot independent from optional memory tuning and GPU functionality.
- Make one component the sole writer of swap-related sysfs controls.
- Record kernel configuration, compressor availability, sizing inputs and runtime statistics.

## Non-goals

- No new compression algorithm is claimed.
- No kernel patch, syscall interception, VRAM-backed RAM, DMA-to-VRAM or DirectStorage implementation is included.
- No claim of lower latency or higher throughput is made until measured.
- No automatic runtime profile switching in EXP-1.

## Data path

### Profile A — zram-fast (baseline candidate)

`reclaim -> swap subsystem -> /dev/zram0 -> zram compressor -> RAM`

Zswap is explicitly disabled. This is the first profile to validate because it avoids a second compressed cache and gives a clean ZRAM baseline.

### Profile B — zswap-first (comparison)

`reclaim -> zswap compressed pool -> backing swap device`

Use a persistent swap partition/file only if the image's deployment model provides one. This profile measures Zswap independently from ZRAM.

### Profile C — hybrid-exp (controlled experiment)

`reclaim -> zswap pool -> /dev/zram0 -> zram compressor -> RAM`

Zswap writeback can send evicted pages to ZRAM, which may compress them again. This can increase CPU work and transient memory pressure. It is an experiment, not the default or presumed fastest profile.

## Kernel prerequisites

The target kernel must expose and validate the relevant options/features:

- `CONFIG_ZRAM`
- `CONFIG_ZSMALLOC`
- `CONFIG_ZSWAP`
- `CONFIG_ZPOOL`
- A compressor supported by the selected kernel build (test `lz4`, `lzo-rle`, and `zstd` where available).
- `CONFIG_PSI` recommended for pressure monitoring.
- `CONFIG_SWAP` and the required block/swap support.

Record the exact kernel version, source commit, .config and available sysfs attributes. Do not assume every kernel has identical attributes.

## Ownership

- `compresso-memoryd`: sole writer of ZRAM/Zswap settings and swap activation.
- `compresso-metricsd`: read-only collection of `/proc` and `/sys` statistics.
- `compresso-supervisord`: starts/stops independent services and records failure state; it must not write memory sysfs.
- `compresso-shaderd`: optional GPU work only; no dependency from boot-critical memory services.

## Safe startup order

1. Mount proc, sysfs and devtmpfs.
2. Load/check kernel modules and confirm swap support.
3. Read and validate the selected profile.
4. Set Zswap parameters before enabling swap, if the profile uses Zswap.
5. Configure ZRAM algorithm, memory limit and virtual disk size before `mkswap`.
6. Run `mkswap`, then activate swap with an explicit priority.
7. Verify `/proc/swaps` and capture initial counters.
8. If any required operation fails, do not activate a partially configured device; log the error and continue boot with ordinary RAM and any independently configured fallback swap.

Never reset an active ZRAM device. Never run `swapoff` as an automatic recovery action under memory pressure.

## EXP acceptance gates

- The ISO boots with ZRAM/Zswap unavailable.
- ZRAM-only can be enabled, used under controlled memory pressure, and cleanly reported.
- Zswap-only is measured separately.
- Hybrid mode is opt-in and compared against both baselines.
- No OOM kill, data loss, boot regression or unbounded memory growth is accepted.
- Every benchmark records machine, RAM, CPU, kernel, compressor, profile, workload and raw measurements.
