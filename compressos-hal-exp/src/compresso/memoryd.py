#!/usr/bin/env python3
"""Experimental fail-closed ZRAM/Zswap configurator."""
import argparse,json,re,subprocess,sys
from pathlib import Path
DEFAULTS={"PROFILE":"zram-fast","DEVICE":"/dev/zram0","ALGORITHM":"lz4","DISKSIZE_PERCENT":"50","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","FALLBACK_ALGORITHMS":"lzo-rle,lzo","ALLOW_EXISTING_SWAP":"false","BACKING_SWAP":""}
PROFILES={"zram-fast","zswap-first","hybrid-exp"}
class MemoryErrorSafe(RuntimeError): pass
def validate(c):
 if c["PROFILE"] not in PROFILES: raise MemoryErrorSafe("PROFILE inválido")
 for k,lo,hi in (("DISKSIZE_PERCENT",10,100),("MEM_LIMIT_PERCENT",5,40),("ZSWAP_PERCENT",1,20),("SWAP_PRIORITY",1,32767)):
  if not c[k].isdigit() or not lo<=int(c[k])<=hi: raise MemoryErrorSafe(k+" fuera de rango")
 if not re.fullmatch(r"/dev/zram[0-9]+",c["DEVICE"]): raise MemoryErrorSafe("DEVICE inválido")
 if c["ALLOW_EXISTING_SWAP"] not in ("true","false"): raise MemoryErrorSafe("ALLOW_EXISTING_SWAP inválido")
 if not re.fullmatch(r"[a-z0-9_-]+",c["ALGORITHM"]): raise MemoryErrorSafe("ALGORITHM inválido")
 if c["PROFILE"]=="zswap-first" and not c["BACKING_SWAP"]: raise MemoryErrorSafe("zswap-first requiere BACKING_SWAP")
 if c["PROFILE"]=="hybrid-exp" and c["BACKING_SWAP"]: raise MemoryErrorSafe("hybrid-exp usa ZRAM como backend")
def load_config(path):
 c=DEFAULTS.copy(); seen=set(); p=Path(path)
 if p.exists():
  for n,line in enumerate(p.read_text().splitlines(),1):
   line=line.strip()
   if not line or line.startswith("#"): continue
   if "=" not in line: raise MemoryErrorSafe(f"línea {n}: KEY=VALUE esperado")
   k,v=(x.strip() for x in line.split("=",1))
   if k not in c or k in seen: raise MemoryErrorSafe(f"clave desconocida o duplicada: {k}")
   c[k]=v; seen.add(k)
 validate(c); return c
def configure(c,sys_root="/",proc_swaps="/proc/swaps",meminfo="/proc/meminfo",dry_run=False,runner=None):
 root=Path(sys_root); sp=lambda p:root/p.lstrip("/"); swaps=Path(proc_swaps); active=swaps.read_text() if swaps.exists() else ""
 dev=c["DEVICE"]
 if dev in active: raise MemoryErrorSafe(f"{dev} ya activo; no se reinicializa")
 enabled=sp("/sys/module/zswap/parameters/enabled"); pool=sp("/sys/module/zswap/parameters/max_pool_percent")
 def cmd(args):
  if not dry_run: (runner or (lambda a:subprocess.run(a,check=True,stdin=subprocess.DEVNULL)))(args)
 if c["PROFILE"]=="zswap-first":
  if not enabled.exists() or not pool.exists(): raise MemoryErrorSafe("Zswap/max_pool_percent no disponible")
  if not dry_run:
   if not Path(c["BACKING_SWAP"]).exists(): raise MemoryErrorSafe("BACKING_SWAP no existe")
   pool.write_text(c["ZSWAP_PERCENT"]); enabled.write_text("Y\n")
  cmd(["swapon","--priority",c["SWAP_PRIORITY"],c["BACKING_SWAP"]])
  return {"profile":c["PROFILE"],"zswap":"enabled","backend":c["BACKING_SWAP"]}
 z=sp("/sys/block/"+Path(dev).name); f={n:z/n for n in ("disksize","mem_limit","comp_algorithm","reset")}
 if not z.exists() or not all(p.exists() for p in f.values()): raise MemoryErrorSafe("interfaz ZRAM incompleta")
 total=None
 for line in Path(meminfo).read_text().splitlines():
  if line.startswith("MemTotal:"): total=int(line.split()[1])*1024; break
 if total is None: raise MemoryErrorSafe("MemTotal no disponible")
 algs=f["comp_algorithm"].read_text().replace("[","").replace("]","").split()
 selected=c["ALGORITHM"] if c["ALGORITHM"] in algs else next((a for a in c["FALLBACK_ALGORITHMS"].split(",") if a in algs),None)
 if not selected: raise MemoryErrorSafe("ningún compresor disponible")
 dsize=total*int(c["DISKSIZE_PERCENT"])//100; limit=total*int(c["MEM_LIMIT_PERCENT"])//100
 if c["PROFILE"]=="hybrid-exp" and (not enabled.exists() or not pool.exists()): raise MemoryErrorSafe("Zswap no disponible; híbrido cancelado")
 if not dry_run:
  f["reset"].write_text("1\n"); f["comp_algorithm"].write_text(selected); f["mem_limit"].write_text(str(limit)); f["disksize"].write_text(str(dsize))
  if c["PROFILE"]=="hybrid-exp": pool.write_text(c["ZSWAP_PERCENT"]); enabled.write_text("Y\n")
  elif enabled.exists(): enabled.write_text("N\n")
 cmd(["mkswap",dev]); cmd(["swapon","--priority",c["SWAP_PRIORITY"],dev])
 return {"profile":c["PROFILE"],"algorithm":selected,"disksize_bytes":dsize,"mem_limit_bytes":limit,"zswap":"enabled" if c["PROFILE"]=="hybrid-exp" else "disabled"}
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--config",default="/etc/compresso/memory.conf"); p.add_argument("--dry-run",action="store_true"); p.add_argument("--status",action="store_true"); a=p.parse_args(argv)
 try:
  c=load_config(a.config)
  if a.status: print(json.dumps({"zram":Path("/sys/block/zram0").exists(),"zswap":Path("/sys/module/zswap/parameters/enabled").exists(),"profile":c["PROFILE"]},indent=2)); return 0
  print(json.dumps(configure(c,dry_run=a.dry_run),indent=2)); return 0
 except (MemoryErrorSafe,OSError,subprocess.CalledProcessError) as e: print("compresso-memoryd: ERROR:",e,file=sys.stderr); return 4
if __name__=="__main__": raise SystemExit(main())