import os
import subprocess
import sys
import unittest
from pathlib import Path

from compresso.benchmark import (
    counter_deltas,
    psi_total_deltas,
    run_benchmark,
    safe_memory_mib,
    validate_options,
)


class BenchmarkTests(unittest.TestCase):
    def test_rejects_unknown_profile_and_unsafe_workload_values(self):
        with self.assertRaises(ValueError):
            validate_options("unknown", 32, 1)
        with self.assertRaises(ValueError):
            validate_options("zram-fast", 0, 1)
        with self.assertRaises(ValueError):
            validate_options("zram-fast", 32, 31)

    def test_workload_is_capped_by_requested_size_available_ram_and_hard_limit(self):
        self.assertEqual(safe_memory_mib(256, 4 * 1024 * 1024), 128)
        self.assertEqual(safe_memory_mib(256, 1024 * 1024), 102)
        self.assertEqual(safe_memory_mib(64, 200 * 1024), 20)
        with self.assertRaises(ValueError):
            safe_memory_mib(32, 512)

    def test_counter_deltas_ignore_missing_and_reset_counters(self):
        self.assertEqual(
            counter_deltas({"pswpin": 10, "pgfault": 20}, {"pswpin": 15, "pgfault": 3}),
            {"pswpin": 5, "pswpout": None, "pgfault": None, "pgmajfault": None},
        )

    def test_psi_total_deltas_are_reported_in_microseconds(self):
        before = {"some": {"total": "100"}, "full": {"total": "10"}}
        after = {"some": {"total": "350"}, "full": {"total": "10"}}
        self.assertEqual(psi_total_deltas(before, after), {"some": 250, "full": 0})

    def test_installed_style_script_imports_sibling_metrics_without_pythonpath(self):
        script = Path(__file__).resolve().parents[1] / "src" / "compresso" / "benchmark.py"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--profile", completed.stdout)

    def test_benchmark_runs_five_samples_without_changing_profile_or_swap(self):
        snapshot = {
            "memory_kb": {"MemAvailable": 1024 * 1024},
            "vmstat": {"pswpin": 10, "pswpout": 20, "pgfault": 30, "pgmajfault": 4},
            "psi_memory": {"some": {"total": "100"}, "full": {"total": "10"}},
        }
        calls = {"metrics": 0, "workload": 0}

        def collect():
            calls["metrics"] += 1
            return snapshot

        def workload(memory_mib, hold_seconds):
            calls["workload"] += 1
            return {"minor_faults": 12, "major_faults": 1, "max_rss_kb": 4096}

        result = run_benchmark(
            "zram-fast", memory_mib=32, hold_seconds=1,
            metrics_collector=collect, workload_runner=workload,
        )
        self.assertEqual(len(result["samples"]), 5)
        self.assertEqual(result["profile_label"], "zram-fast")
        self.assertEqual(calls, {"metrics": 10, "workload": 5})
        self.assertEqual(result["samples"][0]["workload"]["major_faults"], 1)


if __name__ == "__main__":
    unittest.main()
