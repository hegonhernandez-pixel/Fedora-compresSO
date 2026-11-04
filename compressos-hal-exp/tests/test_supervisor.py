import unittest

from compresso.supervisor import inspect_health


def snapshot(active, zram_devices=("zram0",), zswap_enabled="N"):
    return {
        "active_swaps": [{"filename": item} for item in active],
        "zram": {name: {"disksize_bytes": 1024} for name in zram_devices},
        "zswap": {"enabled": zswap_enabled},
    }


class SupervisorTests(unittest.TestCase):
    def test_zram_fast_is_healthy_when_configured_device_is_active_and_zswap_off(self):
        report = inspect_health({"PROFILE": "zram-fast", "DEVICE": "/dev/zram0"},
                                 snapshot(["/dev/zram0"]))
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["issues"], [])

    def test_missing_configured_zram_swap_is_critical(self):
        report = inspect_health({"PROFILE": "zram-fast", "DEVICE": "/dev/zram0"},
                                 snapshot(["/dev/sda2"]))
        self.assertEqual(report["status"], "critical")
        self.assertIn("configured_zram_not_active", [x["code"] for x in report["issues"]])

    def test_zswap_first_requires_enabled_zswap_and_backing_swap(self):
        cfg = {"PROFILE": "zswap-first", "DEVICE": "/dev/zram0", "BACKING_SWAP": "/swapfile"}
        report = inspect_health(cfg, snapshot(["/swapfile"], zswap_enabled="Y"))
        self.assertEqual(report["status"], "healthy")
        bad = inspect_health(cfg, snapshot(["/swapfile"], zswap_enabled="N"))
        self.assertEqual(bad["status"], "critical")

    def test_hybrid_requires_both_zram_and_zswap(self):
        cfg = {"PROFILE": "hybrid-exp", "DEVICE": "/dev/zram0"}
        report = inspect_health(cfg, snapshot(["/dev/zram0"], zswap_enabled="Y"))
        self.assertEqual(report["status"], "healthy")
        bad = inspect_health(cfg, snapshot(["/dev/zram0"], zswap_enabled="N"))
        self.assertEqual(bad["status"], "critical")

    def test_zswap_fast_warns_if_zswap_remains_enabled(self):
        report = inspect_health({"PROFILE": "zram-fast", "DEVICE": "/dev/zram0"},
                                 snapshot(["/dev/zram0"], zswap_enabled="Y"))
        self.assertEqual(report["status"], "warning")
        self.assertIn("zswap_should_be_disabled", [x["code"] for x in report["issues"]])

    def test_multiple_zram_swap_devices_are_reported_as_warning(self):
        report = inspect_health({"PROFILE": "zram-fast", "DEVICE": "/dev/zram0"},
                                 snapshot(["/dev/zram0", "/dev/zram1"]))
        self.assertEqual(report["status"], "warning")
        self.assertIn("multiple_zram_swaps", [x["code"] for x in report["issues"]])

    def test_no_swap_active_is_critical(self):
        report = inspect_health({"PROFILE": "zram-fast", "DEVICE": "/dev/zram0"},
                                 snapshot([]))
        self.assertEqual(report["status"], "critical")
        self.assertIn("no_active_swap", [x["code"] for x in report["issues"]])


if __name__ == "__main__":
    unittest.main()
