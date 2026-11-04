#!/usr/bin/env python3
"""Read-only runtime health checks for CompressOS-HAL."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _enabled(value):
    return str(value or "").strip().lower() in ("y", "yes", "1", "true", "on")


def inspect_health(config, metrics):
    """Compare the selected profile with observed kernel state; never mutate it."""
    issues = []
    profile = config.get("PROFILE")
    device = config.get("DEVICE", "/dev/zram0")
    active = {
        item.get("filename")
        for item in metrics.get("active_swaps", [])
        if isinstance(item, dict) and item.get("filename")
    }
    zram = metrics.get("zram") or {}
    zswap_enabled = _enabled((metrics.get("zswap") or {}).get("enabled"))
    zram_active = sorted(path for path in active if Path(path).name.startswith("zram"))

    def add(severity, code, message):
        issues.append({"severity": severity, "code": code, "message": message})

    if not active:
        add("critical", "no_active_swap", "No hay ningún dispositivo swap activo.")
    if not isinstance(metrics.get("memory_kb"), dict) or "MemTotal" not in metrics["memory_kb"]:
        add("warning", "memory_telemetry_missing", "No se pudo leer MemTotal desde la telemetría.")

    if profile not in ("zram-fast", "zswap-first", "hybrid-exp"):
        add("critical", "unknown_profile", "El perfil configurado no es reconocido.")
    elif profile in ("zram-fast", "hybrid-exp"):
        devname = Path(device).name
        if devname not in zram:
            add("critical", "configured_zram_missing", f"No se detecta {device} en sysfs.")
        if device not in active:
            add("critical", "configured_zram_not_active", f"{device} no aparece activo en /proc/swaps.")
        if profile == "zram-fast" and zswap_enabled:
            add("warning", "zswap_should_be_disabled", "El perfil zram-fast espera Zswap desactivado.")
        if profile == "hybrid-exp" and not zswap_enabled:
            add("critical", "hybrid_zswap_disabled", "El perfil híbrido requiere Zswap habilitado.")
    elif profile == "zswap-first":
        backing = config.get("BACKING_SWAP", "")
        if not backing:
            add("critical", "backing_swap_not_configured", "zswap-first requiere BACKING_SWAP.")
        elif backing not in active:
            add("critical", "backing_swap_not_active", f"El backend {backing} no aparece activo en /proc/swaps.")
        if not zswap_enabled:
            add("critical", "zswap_disabled", "El perfil zswap-first requiere Zswap habilitado.")
        if zram_active:
            add("warning", "unexpected_zram_swap", "Hay swap ZRAM activo mientras el perfil es zswap-first.")

    if len(zram_active) > 1:
        add("warning", "multiple_zram_swaps", "Hay más de un dispositivo ZRAM activo: " + ", ".join(zram_active))

    rank = {"healthy": 0, "warning": 1, "critical": 2}
    status = "healthy" if not issues else max(
        (item["severity"] for item in issues), key=lambda severity: rank[severity]
    )
    return {
        "schema_version": 1,
        "status": status,
        "profile": profile,
        "active_swaps": sorted(active),
        "zswap_enabled": zswap_enabled,
        "issues": issues,
        "safety": {"read_only": True, "changes_active_swap": False,
                   "changes_kernel_parameters": False, "automatic_recovery": False},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="/etc/compresso/memory.conf")
    parser.add_argument("--proc-root", default="/proc")
    parser.add_argument("--sys-root", default="/sys")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    try:
        try:
            from .memoryd import load_config
            from .metrics import collect_metrics
        except ImportError:
            from memoryd import load_config
            from metrics import collect_metrics
        config = load_config(args.config)
        metrics = collect_metrics(proc_root=args.proc_root, sys_root=args.sys_root)
        report = inspect_health(config, metrics)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"CompressOS-HAL: {report['status'].upper()} (perfil: {report['profile']})")
            for issue in report["issues"]:
                print(f"[{issue['severity'].upper()}] {issue['code']}: {issue['message']}")
            if not report["issues"]:
                print("No se detectaron incompatibilidades en el estado observado.")
            print("Comprobación de solo lectura; no se modificó swap ni el kernel.")
        return {"healthy": 0, "warning": 1, "critical": 2}[report["status"]]
    except (OSError, ValueError, KeyError) as exc:
        print(f"compresso-supervisor: ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
