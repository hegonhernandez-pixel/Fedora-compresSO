#!/bin/sh
set -eu
if systemctl is-active --quiet compresso-memoryd.service; then echo "memoryd: configured"; else echo "memoryd: inactive"; fi
if [ -d /sys/block/zram0 ]; then echo "zram0: present"; else echo "zram0: unavailable"; fi
if [ -r /sys/module/zswap/parameters/enabled ]; then printf 'zswap: '; cat /sys/module/zswap/parameters/enabled; else echo "zswap: unavailable"; fi