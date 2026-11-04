#!/usr/bin/env python3
"""Experimental, fail-closed ZRAM/Zswap configurator for CompressOS-HAL."""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path

DEFAULTS = {
    "PROFILE": "zram-fast", "DEVICE": "/dev/zram0", "ALGORITHM": "lz4",
    "DISKSIZE_PERCENT": "50", "MEM_LIMIT_PERCENT": "20", "ZSWAP_PERCENT": "5",
    "SWAP_PRIORITY": "100", "FALLBACK_ALGORITHMS": "lzo-rle,lzo",
    "ALLOW_EXISTING_SWAP": "false", "BACKING_SWAP": "",
}
PROFILES = {"zram-fast", "zswap-first", "hybrid-exp"}

class MemoryErrorSafe(RuntimeError):
    pass

def load_config(path):
    cfg = DEFAULTS.copy()
    p = Path(path)
    if not p.exists():
        validate_config(cfg)
        return cfg
    seen_keys = set()
    for no, raw in enumerate(p.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise MemoryErrorSafe(f"línea {no}: se esperaba KEY=VALUE")
        key, value = (part.strip() for part in line.split("=", 1))
        if not re.fullmatch(r"^[A-Z][A-Z0-9_]*$", key) or key not in cfg:
            raise MemoryErrorSafe(f"clave desconocida/inválida: {key}")
        if key in seen_keys:
            raise MemoryErrorSafe(f"clave duplicada: {key}")
        cfg[key] = value
        seen_keys.add(key)
    validate_config(cfg)
    return cfg

def validate_config(c):
    if c["PROFILE"] not in PROFILES:
        raise MemoryErrorSafe("PROFILE debe ser zram-fast, zswap-first o hybrid-exp")
    for k, lo, hi in (("DISKSIZE_PERCENT", 10, 100), ("MEM_LIMIT_PERCENT", 5, 40), ("ZSWAP_PERCENT", 1, 20), ("SWAP_PRIORITY", 1, 32767)):
        if not c[k].isdigit() or not lo <= int(c[k]) <= hi:
            raise MemoryErrorSafe(f"{k} fuera de rango [{lo}, {hi}]")
    if not re.fullmatch(r"/dev/zram[0-9]+", c["DEVICE"]):
        raise MemoryErrorSafe("DEVICE debe ser un dispositivo /dev/zramN")
    if c["ALLOW_EXISTING_SWAP"] not in ("true", "false"):
        raise MemoryErrorSafe("ALLOW_EXISTING_SWAP debe ser true o false")
    if not re.fullmatch(r"[a-z0-9_-]+", c["ALGORITHM"]):
        raise MemoryErrorSafe("ALGORITHM inválido")
    if c["PROFILE"] == "zswap-first" and not c["BACKING_SWAP"]:
        raise MemoryErrorSafe("zswap-first requiere BACKING_SWAP explícito")
    if c["PROFILE"] == "hybrid-exp" and c["BACKING_SWAP"]:
        raise MemoryErrorSafe("hybrid-exp usa ZRAM como backend; BACKING_SWAP debe quedar vacío")

def _active_swap_paths(text):
    """Return active swap paths from /proc/swaps, ignoring its header."""
    paths = set()
    for line in text.splitlines()[1:]:
        fields = line.split()
        if fields:
            paths.add(fields[0])
    return paths


def configure(cfg, *, sys_root="/", proc_swaps="/proc/swaps", meminfo="/proc/meminfo", dry_run=False, runner=None):
    profile = cfg["PROFILE"]
    root = Path(sys_root)
    def sp(p):
        return root / p.lstrip("/")
    swaps = Path(proc_swaps)
    active_text = swaps.read_text() if swaps.exists() else ""
    active_paths = _active_swap_paths(active_text)
    zdev = cfg["DEVICE"]
    if zdev in active_paths:
        raise MemoryErrorSafe(f"{zdev} ya aparece activo; no se reinicializa ni se ejecuta swapoff")

    enabled = sp("/sys/module/zswap/parameters/enabled")
    pool = sp("/sys/module/zswap/parameters/max_pool_percent")

    def run_cmd(argv):
        if not dry_run:
            if runner:
                runner(argv)
            else:
                subprocess.run(argv, check=True, stdin=subprocess.DEVNULL)

    if profile == "zswap-first":
        if not enabled.exists() or not pool.exists():
            raise MemoryErrorSafe("Zswap o max_pool_percent no disponible")
        if not dry_run:
            if not Path(cfg["BACKING_SWAP"]).exists():
                raise MemoryErrorSafe("BACKING_SWAP no existe")
            pool.write_text(cfg["ZSWAP_PERCENT"])
            enabled.write_text("Y\n")
        if cfg["BACKING_SWAP"] not in active_paths:
            run_cmd(["swapon", "--priority", cfg["SWAP_PRIORITY"], cfg["BACKING_SWAP"]])
        return {"profile": profile, "zswap": "enabled", "zswap_pool_percent": int(cfg["ZSWAP_PERCENT"]), "backend": cfg["BACKING_SWAP"]}

    devname = Path(zdev).name
    zbase = sp(f"/sys/block/{devname}")
    if not zbase.exists():
        raise MemoryErrorSafe(f"{zdev} no existe; cargue/active el módulo zram primero")
    files = {name: zbase / name for name in ("disksize", "mem_limit", "comp_algorithm", "reset")}
    if not all(path.exists() for path in files.values()):
        raise MemoryErrorSafe("interfaz sysfs ZRAM incompleta")

    total_kb = None
    for line in Path(meminfo).read_text().splitlines():
        if line.startswith("MemTotal:"):
            total_kb = int(line.split()[1])
            break
    if total_kb is None:
        raise MemoryErrorSafe("no se pudo leer MemTotal")
    total_bytes = total_kb * 1024
    disksize = total_bytes * int(cfg["DISKSIZE_PERCENT"]) // 100
    mem_limit = total_bytes * int(cfg["MEM_LIMIT_PERCENT"]) // 100

    algorithms = files["comp_algorithm"].read_text().replace("[", "").replace("]", "").split()
    selected = cfg["ALGORITHM"] if cfg["ALGORITHM"] in algorithms else None
    if not selected:
        for candidate in cfg["FALLBACK_ALGORITHMS"].split(","):
            if candidate in algorithms:
                selected = candidate
                break
    if not selected:
        raise MemoryErrorSafe("ningún algoritmo solicitado/fallback está disponible")

    if profile == "hybrid-exp" and (not enabled.exists() or not pool.exists()):
        raise MemoryErrorSafe("Zswap o max_pool_percent no disponible; híbrido cancelado")

    if not dry_run:
        files["reset"].write_text("1\n")
        files["comp_algorithm"].write_text(selected)
        if files["mem_limit"].exists():
            files["mem_limit"].write_text(str(mem_limit))
        files["disksize"].write_text(str(disksize))
        if profile == "hybrid-exp":
            pool.write_text(cfg["ZSWAP_PERCENT"])
            enabled.write_text("Y\n")
        elif profile == "zram-fast" and enabled.exists():
            enabled.write_text("N\n")

    run_cmd(["mkswap", zdev])
    run_cmd(["swapon", "--priority", cfg["SWAP_PRIORITY"], zdev])
    return {"profile": profile, "zram_device": zdev, "algorithm": selected, "disksize_bytes": disksize, "mem_limit_bytes": mem_limit, "zswap": "enabled" if profile == "hybrid-exp" else ("disabled" if profile == "zram-fast" else "not-applicable")}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="/etc/compresso/memory.conf")
    parser.add_argument("--dry-run", action="store_true", help="validar y mostrar el plan sin modificar sysfs ni activar swap")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.status:
            print(json.dumps({"zram": Path("/sys/block/zram0").exists(), "zswap": Path("/sys/module/zswap/parameters/enabled").exists(), "profile": cfg["PROFILE"]}, indent=2))
            return 0
        print(json.dumps(configure(cfg, dry_run=args.dry_run), indent=2))
        return 0
    except (MemoryErrorSafe, OSError, subprocess.CalledProcessError) as exc:
        print(f"compresso-memoryd: ERROR: {exc}", file=sys.stderr)
        return 4

if __name__ == "__main__":
    raise SystemExit(main())
