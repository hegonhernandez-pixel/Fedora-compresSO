import json
import tempfile
import unittest
from pathlib import Path
from compresso.metrics import collect_metrics, write_snapshot


class MetricsTests(unittest.TestCase):
    def make_tree(self, root):
        proc = Path(root) / "proc"
        sys = Path(root) / "sys"
        (proc / "pressure").mkdir(parents=True)
        (proc / "meminfo").write_text(
            "MemTotal: 8192000 kB\nMemAvailable: 4096000 kB\n"
            "SwapTotal: 1024000 kB\nSwapFree: 768000 kB\n"
        )
        (proc / "vmstat").write_text(
            "pswpin 12\npswpout 34\npgmajfault 56\npgfault 789\n"
        )
        (proc / "pressure" / "memory").write_text(
            "some avg10=0.10 avg60=0.20 avg300=0.30 total=400\n"
            "full avg10=0.01 avg60=0.02 avg300=0.03 total=40\n"
        )
        (proc / "swaps").write_text(
            "Filename Type Size Used Priority\n/dev/zram0 partition 512000 10 100\n"
        )
        zram = sys / "block" / "zram0"
        zram.mkdir(parents=True)
        (zram / "mm_stat").write_text("100 200 300 4 5 6 7 8 9\n")
        (zram / "io_stat").write_text("1 2 3 4\n")
        zswap = sys / "module" / "zswap" / "parameters"
        zswap.mkdir(parents=True)
        (zswap / "enabled").write_text("Y\n")
        (zswap / "max_pool_percent").write_text("7\n")
        return proc, sys

    def test_collects_memory_vmstat_psi_zram_and_zswap_as_json_data(self):
        with tempfile.TemporaryDirectory() as d:
            proc, sys = self.make_tree(d)
            data = collect_metrics(proc_root=proc, sys_root=sys, timestamp="2026-11-04T12:00:00Z")
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["memory_kb"]["MemTotal"], 8192000)
        self.assertEqual(data["vmstat"]["pswpout"], 34)
        self.assertEqual(data["psi_memory"]["some"]["avg10"], "0.10")
        self.assertEqual(data["zram"]["zram0"]["mm_stat"], [100, 200, 300, 4, 5, 6, 7, 8, 9])
        self.assertEqual(data["zswap"]["enabled"], "Y")
        self.assertEqual(data["active_swaps"][0]["filename"], "/dev/zram0")

    def test_missing_optional_kernel_interfaces_are_reported_as_null(self):
        with tempfile.TemporaryDirectory() as d:
            proc = Path(d) / "proc"
            proc.mkdir()
            (proc / "meminfo").write_text("MemTotal: 1024 kB\n")
            (proc / "vmstat").write_text("pswpin 0\n")
            (proc / "swaps").write_text("Filename Type Size Used Priority\n")
            data = collect_metrics(proc_root=proc, sys_root=Path(d) / "sys", timestamp="fixed")
        self.assertEqual(data["zram"], {})
        self.assertIsNone(data["zswap"]["enabled"])
        self.assertIsNone(data["psi_memory"])

    def test_writes_valid_json_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            proc, sys = self.make_tree(d)
            output = Path(d) / "out" / "metrics.json"
            write_snapshot(output, proc_root=proc, sys_root=sys, timestamp="fixed")
            loaded = json.loads(output.read_text())
        self.assertEqual(loaded["timestamp"], "fixed")
        self.assertEqual(loaded["vmstat"]["pgmajfault"], 56)


    def test_meminfo_field_names_are_normalized(self):
        with tempfile.TemporaryDirectory() as d:
            proc = Path(d) / "proc"
            proc.mkdir()
            (proc / "meminfo").write_text("MemTotal: 2048 kB\nMemAvailable: 1024 kB\n")
            (proc / "vmstat").write_text("")
            (proc / "swaps").write_text("Filename Type Size Used Priority\n")
            data = collect_metrics(proc_root=proc, sys_root=Path(d) / "sys", timestamp="fixed")
        self.assertEqual(data["memory_kb"], {"MemTotal": 2048, "MemAvailable": 1024})


if __name__ == "__main__":
    unittest.main()
