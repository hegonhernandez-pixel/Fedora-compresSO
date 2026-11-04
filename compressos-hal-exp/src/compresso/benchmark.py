#!/usr/bin/env python3
"""Run a bounded, non-privileged memory workload and report telemetry deltas.

This tool labels the currently selected profile; it never changes ZRAM, Zswap,
swap priorities, kernel parameters, or the active profile.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from .metrics import collect_metrics
except ImportError:  # Running as an installed standalone script.
    from metrics import collect_metrics


PROFILES = ("zram-fast", "zswap-first", "hybrid-exp")
REPETITIONS = 5
MAX_MEMORY_MIB = 128
WORKLOAD_SCRIPT = r"""
import json
import resource
import sys
import time

size = int(sys.argv[1]) * 1024 * 1024
hold = float(sys.argv[2])
buffer = bytearray(size)
for offset in range(0, size, 4096):
    buffer[offset] = 1
time.sleep(hold)
usage = resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps({
    "minor_faults": usage.ru_minflt,
    "major_faults": usage.ru_majflt,
    "max_rss_kb": usage.ru_maxrss,
}))
"""


def validate_options(profile, memory_mib, hold_seconds):
    if profile not in PROFILES:
        raise ValueError("profile must be one of: " + ", ".join(PROFILES))
    if isinstance(memory_mib, bool) or not isinstance(memory_mib, int) or not 1 <= memory_mib <= MAX_MEMORY_MIB:
        raise ValueError(f"memory_mib must be an integer from 1 to {MAX_MEMORY_MIB}")
    if isinstance(hold_seconds, bool) or not isinstance(hold_seconds, (int, float)) or not 1 <= hold_seconds <= 30:
        raise ValueError("hold_seconds must be between 1 and 30")
    return {"profile_label": profile, "requested_memory_mib": memory_mib,
            "hold_seconds": float(hold_seconds), "repetitions": REPETITIONS}


def safe_memory_mib(requested_mib, mem_available_kb):
    if isinstance(requested_mib, bool) or not isinstance(requested_mib, int) or requested_mib < 1:
        raise ValueError("requested workload must be a positive integer")
    if isinstance(mem_available_kb, bool) or not isinstance(mem_available_kb, int) or mem_available_kb <= 0:
        raise ValueError("MemAvailable is missing or invalid; refusing to start workload")
    ten_percent_available = mem_available_kb // 1024 // 10
    selected = min(requested_mib, MAX_MEMORY_MIB, ten_percent_available)
    if selected < 1:
        raise ValueError("less than 10 MiB of available memory; refusing to start workload")
    return selected


def counter_deltas(before, after):
    result = {}
    for key in ("pswpin", "pswpout", "pgfault", "pgmajfault"):
        left, right = before.get(key), after.get(key)
        if isinstance(left, int) and isinstance(right, int) and right >= left:
            result[key] = right - left
        else:
            result[key] = None
    return result


def psi_total_deltas(before, after):
    result = {}
    for group in ("some", "full"):
        try:
            left = int(before[group]["total"])
            right = int(after[group]["total"])
            result[group] = right - left if right >= left else None
        except (KeyError, TypeError, ValueError):
            result[group] = None
    return result


def _run_workload(memory_mib, hold_seconds):
    completed = subprocess.run(
        [sys.executable, "-c", WORKLOAD_SCRIPT, str(memory_mib), str(hold_seconds)],
        check=True, capture_output=True, text=True, timeout=hold_seconds + 15,
    )
    return json.loads(completed.stdout)


def run_benchmark(profile, *, memory_mib=32, hold_seconds=1,
                  proc_root="/proc", sys_root="/sys",
                  metrics_collector=None, workload_runner=None):
    options = validate_options(profile, memory_mib, hold_seconds)
    collector = metrics_collector or (
        lambda: collect_metrics(proc_root=proc_root, sys_root=sys_root)
    )
    runner = workload_runner or _run_workload
    samples = []
    selected_memory_mib = None

    for index in range(REPETITIONS):
        before = collector()
        available = before.get("memory_kb", {}).get("MemAvailable")
        current_memory_mib = safe_memory_mib(memory_mib, available)
        selected_memory_mib = current_memory_mib if selected_memory_mib is None else min(selected_memory_mib, current_memory_mib)
        started = time.monotonic()
        workload = runner(current_memory_mib, float(hold_seconds))
        elapsed = time.monotonic() - started
        after = collector()
        samples.append({
            "iteration": index + 1,
            "elapsed_seconds": round(elapsed, 6),
            "workload": workload,
            "vmstat_delta": counter_deltas(before.get("vmstat", {}), after.get("vmstat", {})),
            "psi_memory_total_delta_us": psi_total_deltas(
                before.get("psi_memory") or {}, after.get("psi_memory") or {}
            ),
        })

    return {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **options,
        "actual_memory_mib": selected_memory_mib,
        "samples": samples,
        "safety": {
            "changes_system_configuration": False,
            "changes_active_swap": False,
            "changes_kernel_parameters": False,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=PROFILES,
                        help="label of the profile already activated by the operator")
    parser.add_argument("--memory-mib", type=int, default=32)
    parser.add_argument("--hold-seconds", type=float, default=1)
    parser.add_argument("--output", help="optional JSON report path; stdout is used by default")
    args = parser.parse_args(argv)
    report = run_benchmark(args.profile, memory_mib=args.memory_mib,
                           hold_seconds=args.hold_seconds)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
        print(target)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
