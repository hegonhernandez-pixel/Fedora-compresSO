import tempfile
import unittest
from pathlib import Path
from compresso.memoryd import load_config, validate_config, configure, MemoryErrorSafe

class ConfigTests(unittest.TestCase):
    def test_defaults_are_zram_fast(self):
        with tempfile.TemporaryDirectory() as d:
            c = load_config(Path(d) / "missing.conf")
        self.assertEqual(c["PROFILE"], "zram-fast")
        self.assertEqual(c["ALLOW_EXISTING_SWAP"], "false")

    def test_reject_unknown_key(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.write_text("PROFILE=zram-fast\nEVIL=1\n")
            with self.assertRaises(MemoryErrorSafe):
                load_config(p)

    def test_reject_duplicate_key(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.write_text("PROFILE=zram-fast\nPROFILE=hybrid-exp\n")
            with self.assertRaises(MemoryErrorSafe):
                load_config(p)

    def test_reject_bad_percent(self):
        c = {"PROFILE":"zram-fast","DISKSIZE_PERCENT":"101","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","DEVICE":"/dev/zram0","ALLOW_EXISTING_SWAP":"false","ALGORITHM":"lz4","BACKING_SWAP":""}
        with self.assertRaises(MemoryErrorSafe):
            validate_config(c)

    def test_zswap_requires_backing(self):
        c = {"PROFILE":"zswap-first","DISKSIZE_PERCENT":"50","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","DEVICE":"/dev/zram0","ALLOW_EXISTING_SWAP":"false","ALGORITHM":"lz4","BACKING_SWAP":""}
        with self.assertRaises(MemoryErrorSafe):
            validate_config(c)

class RuntimeTests(unittest.TestCase):
    def make_fake_tree(self, root):
        z = Path(root) / "sys/block/zram0"
        z.mkdir(parents=True)
        (z/"disksize").write_text("0")
        (z/"mem_limit").write_text("0")
        (z/"comp_algorithm").write_text("lzo [lz4] zstd")
        (z/"reset").write_text("0")
        return z

    def test_dry_run_calculates_sizes_without_mutating_sysfs(self):
        with tempfile.TemporaryDirectory() as d:
            z = self.make_fake_tree(d)
            mem = Path(d) / "meminfo"
            mem.write_text("MemTotal:       8388608 kB\n")
            swaps = Path(d) / "swaps"
            swaps.write_text("Filename Type Size Used Priority\n")
            cfg = {"PROFILE":"zram-fast","DEVICE":"/dev/zram0","ALGORITHM":"lz4","DISKSIZE_PERCENT":"50","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","FALLBACK_ALGORITHMS":"lzo-rle,lzo","ALLOW_EXISTING_SWAP":"false","BACKING_SWAP":""}
            calls = []
            result = configure(cfg, sys_root=d, proc_swaps=str(swaps), meminfo=str(mem), dry_run=True, runner=lambda a: calls.append(a))
            self.assertEqual(result["disksize_bytes"], 4*1024*1024*1024)
            self.assertEqual(result["mem_limit_bytes"], int(8*1024*1024*1024*.2))
            self.assertEqual((z/"disksize").read_text(), "0")
            self.assertEqual(calls, [])

    def test_refuses_to_reset_active_zram(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_fake_tree(d)
            mem = Path(d) / "meminfo"
            mem.write_text("MemTotal: 4096000 kB\n")
            swaps = Path(d) / "swaps"
            swaps.write_text("Filename Type Size Used Priority\n/dev/zram0 partition 100 0 100\n")
            cfg = {"PROFILE":"zram-fast","DEVICE":"/dev/zram0","ALGORITHM":"lz4","DISKSIZE_PERCENT":"50","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","FALLBACK_ALGORITHMS":"lzo-rle,lzo","ALLOW_EXISTING_SWAP":"false","BACKING_SWAP":""}
            with self.assertRaises(MemoryErrorSafe):
                configure(cfg, sys_root=d, proc_swaps=str(swaps), meminfo=str(mem), dry_run=True)

if __name__ == "__main__":
    unittest.main()
