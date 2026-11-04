#!/bin/sh
set -eu
OUT=/run/compresso
mkdir -p "$OUT"
TMP="$OUT/metrics.txt.tmp"
{
 date -Is
 grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo || true
 grep -E '^(pswpin|pswpout|pgmajfault) ' /proc/vmstat || true
 for f in /proc/pressure/memory /sys/block/zram0/mm_stat /sys/block/zram0/io_stat; do
  if [ -r "$f" ]; then printf '\n[%s]\n' "$f"; cat "$f"; fi
 done
} > "$TMP"
chmod 0640 "$TMP"
mv "$TMP" "$OUT/metrics.txt"