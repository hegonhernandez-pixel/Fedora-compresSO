# EXP-003 — Daemon boundaries and input/output rules

**Status:** Contract proposal for EXP phase.

## Process separation

| Service | Responsibility | May write | Must not do |
|---|---|---|---|
| `compresso-memoryd` | Configure ZRAM/Zswap and activate swap | Approved memory sysfs nodes; swap activation during startup | GPU work, telemetry policy, arbitrary shell commands |
| `compresso-metricsd` | Collect memory/pressure counters | Its own output under `/run/compresso/` | Write to `/sys`, change swap, kill processes |
| `compresso-supervisord` | Service lifecycle and health state | Service state/log metadata | Change kernel memory settings |
| `compresso-shaderd` | Optional Vulkan shader workloads | Its own bounded buffers and result files | Change swap, reserve VRAM at boot, block root mount |

## Input contract

- Configuration: root-owned `/etc/compresso/memory.conf`, plain `KEY=VALUE` pairs.
- Accepted profile names: `zram-fast`, `zswap-first`, `hybrid-exp`.
- Numeric values must be decimal integers in documented ranges; reject negatives, overflow, duplicate keys and unknown keys.
- No `eval`, dynamic sourcing of untrusted files, command strings, arbitrary paths or user-supplied sysfs paths.
- Hardware facts are read from kernel interfaces, not trusted from configuration.
- Only the memory service runs with the privilege needed to configure swap. Metrics and shader workers run unprivileged where practical.

## Output contract

- Structured status: `/run/compresso/memory-status.json` (atomic temp-file + rename).
- Metrics: `/run/compresso/metrics.json` (read-only snapshots).
- Logs: journald/syslog with service name, profile, kernel version, active compressor, limits, return code and timestamp.
- Exit codes: 0 success; 2 invalid configuration; 3 unsupported kernel feature; 4 resource/setup failure; 5 unsafe existing state.
- No credentials or private user data in logs.

## Ownership and ordering

Only `compresso-memoryd` owns writes to:
- `/sys/block/zram0/comp_algorithm`
- `/sys/block/zram0/mem_limit`
- `/sys/block/zram0/disksize`
- `/sys/block/zram0/reset` (only while inactive and during explicit controlled initialization)
- `/sys/module/zswap/parameters/*` (only approved parameters, before swap activation)

All other services are read-only for these paths. A systemd unit must order memory setup before the relevant swap target and must not race with another ZRAM generator.

## Failure and recovery rules

- Do not reset ZRAM if `/proc/swaps` shows it active.
- Do not run `swapoff` automatically under memory pressure.
- If ZRAM is unsupported, report degraded mode and continue boot without it.
- If the requested compressor is unavailable, use only an explicitly configured fallback list and report the selected algorithm.
- If hybrid Zswap controls are missing, fail closed to the documented ZRAM-only profile; never claim hybrid mode is active.
- Use bounded retries only for transient device appearance; no infinite restart loop.
- A failed shader process must not restart or stop memory services.

## EXP files expected to change

- `buildroot-external/Config.in`, `buildroot-external/external.desc`, `buildroot-external/external.mk`
- `buildroot-external/package/compresso-memoryd/Config.in`
- `buildroot-external/package/compresso-memoryd/compresso-memoryd.mk`
- `buildroot-external/board/compresso/rootfs-overlay/etc/compresso/memory.conf`
- `buildroot-external/board/compresso/rootfs-overlay/usr/libexec/compresso-memoryd`
- `buildroot-external/board/compresso/rootfs-overlay/usr/lib/systemd/system/compresso-memoryd.service`
- `buildroot-external/board/compresso/rootfs-overlay/usr/lib/systemd/system/compresso-metricsd.service`
- `buildroot-external/board/compresso/rootfs-overlay/usr/lib/systemd/system/compresso-supervisord.service`
- `buildroot-external/board/compresso/rootfs-overlay/usr/lib/systemd/system/compresso-shaderd.service`
- `buildroot-external/configs/compresso_x86_64_defconfig`
- `buildroot-external/linux/compresso_kernel.fragment`
- `tests/memory/test-memoryd.sh`, `tests/memory/fixtures/`
- `.github/workflows/buildroot-exp.yml`

This list is a forecast, not a claim that these files already exist or have been implemented.
