#!/usr/bin/env python3
"""Read-only JSON telemetry for CompressOS-HAL."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _read_text(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def _key_values(path):
    text = _read_text(path)
    values = {}
    if text is None:
        return values
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            try:
                values[fields[0].rstrip(":")] = int(fields[1])
            except ValueError:
                continue
    return values


def _pressure(path):
    text = _read_text(path)
    if text is None:
        return None
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        group = fields[0]
        metrics = {}
        for field in fields[1:]:
            if "=" in field:
                key, value = field.split("=", 1)
                metrics[key] = value
        result[group] = metrics
    return result


def _swap_entries(path):
    text = _read_text(path)
    if text is None:
        return []
    entries = []
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 5:
            try:
                entries.append({
                    "filename": fields[0], "type": fields[1],
                    "size_kb": int(fields[2]), "used_kb": int(fields[3]),
                    "priority": int(fields[4]),
                })
            except ValueError:
                continue
    return entries


def _integer_list(path):
    text = _read_text(path)
    if text is None:
        return None
    try:
        return [int(value) for value in text.split()]
    except ValueError:
        return text.split()


def collect_metrics(*, proc_root="/proc", sys_root="/sys", timestamp=None):
    """Collect a snapshot without writing to kernel interfaces or changing swap."""
    proc = Path(proc_root)
    sys = Path(sys_root)
    meminfo = _key_values(proc / "meminfo")
    vmstat = _key_values(proc / "vmstat")
    memory_keys = ("MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached",
                   "SwapTotal", "SwapFree", "Shmem", "Slab")
    memory = {key: meminfo[key] for key in memory_keys if key in meminfo}

    zram = {}
    block_root = sys / "block"
    if block_root.is_dir():
        for device in sorted(block_root.glob("zram[0-9]*")):
            if not device.is_dir():
                continue
            entry = {}
            for name in ("mm_stat", "io_stat", "bd_stat"):
                values = _integer_list(device / name)
                if values is not None:
                    entry[name] = values
            algorithm = _read_text(device / "comp_algorithm")
            if algorithm is not None:
                entry["comp_algorithm"] = algorithm
            disksize = _read_text(device / "disksize")
            if disksize is not None:
                try:
                    entry["disksize_bytes"] = int(disksize)
                except ValueError:
                    entry["disksize_bytes"] = disksize
            zram[device.name] = entry

    zswap_base = sys / "module" / "zswap" / "parameters"
    zswap = {
        "enabled": _read_text(zswap_base / "enabled"),
        "max_pool_percent": _read_text(zswap_base / "max_pool_percent"),
        "compressor": _read_text(zswap_base / "compressor"),
        "zpool": _read_text(zswap_base / "zpool"),
    }
    return {
        "schema_version": 1,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "memory_kb": memory,
        "vmstat": {key: vmstat[key] for key in ("pswpin", "pswpout", "pgfault", "pgmajfault") if key in vmstat},
        "psi_memory": _pressure(proc / "pressure" / "memory"),
        "active_swaps": _swap_entries(proc / "swaps"),
        "zram": zram,
        "zswap": zswap,
    }


def write_snapshot(output, *, proc_root="/proc", sys_root="/sys", timestamp=None):
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(collect_metrics(proc_root=proc_root, sys_root=sys_root, timestamp=timestamp),
                         indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, target)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/run/compresso/metrics.json")
    parser.add_argument("--proc-root", default="/proc")
    parser.add_argument("--sys-root", default="/sys")
    parser.add_argument("--stdout", action="store_true", help="print JSON instead of writing a file")
    args = parser.parse_args(argv)
    if args.stdout:
        print(json.dumps(collect_metrics(proc_root=args.proc_root, sys_root=args.sys_root), indent=2))
    else:
        print(write_snapshot(args.output, proc_root=args.proc_root, sys_root=args.sys_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
