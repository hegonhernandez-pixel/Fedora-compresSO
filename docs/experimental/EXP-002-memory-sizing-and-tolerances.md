# EXP-002 — Memory sizing, calculations and tolerances

**Status:** Initial conservative test envelope; tune only from measurements.

## Symbols

- (R): physical RAM in bytes, read from `MemTotal` in `/proc/meminfo`.
- (G): (2^{30}) bytes (GiB).
- (D_z): ZRAM virtual disk capacity.
- (M_z): ZRAM physical-memory usage limit.
- (P_s): Zswap compressed-pool limit as a percentage of physical RAM.

## Initial formulas

For systems with at least 4 GiB RAM:

- (D_z = min(0.50R, 8G))
- (M_z = min(0.20R, 4G))
- Hybrid-only (P_s = 5%) of RAM
- Conservative combined pool envelope: (M_z + 0.05R leq 0.25R), before allocator metadata and transient overhead.

For systems below 4 GiB RAM:

- Start with ZRAM-only.
- (D_z = min(0.50R, 4G))
- (M_z = 0.15R)
- Zswap remains disabled until a separate low-memory test proves it beneficial.

These are upper bounds for an experiment, not guaranteed memory savings. ZRAM's `disksize` is virtual capacity; it does not allocate that amount of physical RAM at startup. `mem_limit` constrains ZRAM's memory use where supported.

## Worked examples

| Physical RAM | ZRAM virtual capacity (D_z) | ZRAM memory cap (M_z) | Zswap cap in hybrid |
|---:|---:|---:|---:|
| 2 GiB | 1 GiB | 0.30 GiB | Off |
| 4 GiB | 2 GiB | 0.80 GiB | 0.20 GiB |
| 8 GiB | 4 GiB | 1.60 GiB | 0.40 GiB |
| 16 GiB | 8 GiB | 3.20 GiB | 0.80 GiB |
| 32 GiB | 8 GiB | 4 GiB | 1.60 GiB |

Example for 8 GiB RAM: (R=8192) MiB, (D_z=4096) MiB, (M_z=1638) MiB, and (P_s=5%) (410 MiB). The nominal combined pool ceiling is about 2048 MiB (25% RAM). Round down to whole MiB in implementation.

## Compressor selection

- First candidate for the low-latency profile: `lz4`, only if listed by `/sys/block/zram0/comp_algorithm`.
- Comparison candidates: `lzo-rle` and `zstd`, only if the running kernel exposes them.
- Never silently claim a requested algorithm was selected. Read back the active algorithm and log it.
- Do not choose a compressor from its name alone; benchmark throughput, CPU time, memory ratio and tail latency on target hardware.

## Metrics and calculations

From ZRAM `mm_stat`, record at minimum original bytes, compressed bytes, allocator bytes and memory limit (field availability depends on kernel).

- Compression ratio: (C = original_bytes / compressed_bytes), when compressed bytes are nonzero.
- Effective storage ratio: (E = original_bytes / mem_used_total), when allocator bytes are nonzero.
- Approximate bytes saved: (S = original_bytes - mem_used_total). This is an accounting estimate, not a promise of reclaimable RAM.
- Record swap-in/out deltas from `/proc/vmstat`, major faults, memory PSI, CPU task-clock and workload completion time.

Do not compare unlike workloads or report a ratio without its numerator, denominator and time window.

## Proposed EXP rollback tolerances

These are engineering guardrails to validate and adjust, not universal Linux performance laws:

- Any OOM kill attributable to the profile: immediate test failure and revert to ZRAM-only or swap-off only after safe recovery.
- Workload p95 latency worsens by more than 15% versus the same-machine baseline in two consecutive runs: reject the profile.
- CPU task-clock rises by more than 10% without a measurable reduction in storage I/O or workload time: reject the profile.
- Sustained memory PSI `full avg10` above 2% for 60 seconds under the reference workload: flag for rollback investigation.
- Repeated swap-in/swap-out oscillation or a >50% increase in major faults versus baseline: reject pending diagnosis.
- Any boot failure, kernel warning attributable to the change, data corruption or failed swap activation: hard failure.

## Benchmark protocol

Run at least 5 repetitions per profile after one warm-up. Report median and p95, plus min/max. Keep kernel, firmware, CPU governor, background services, workload and RAM configuration fixed. Test ZRAM-only, Zswap-only and hybrid separately. Preserve raw logs.

Do not publish a performance claim until results are reproducible on at least one named target and the limitation is stated.
