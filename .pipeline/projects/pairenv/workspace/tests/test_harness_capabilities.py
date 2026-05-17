"""test_harness_capabilities.py — Tests for pipeline harness capabilities.

Tests the health check and quick test infrastructure at the workspace root level.
"""

import json
import os
import pathlib
import sys
import unittest

# Ensure workspace root is on the path (for health_check, quick_test, sweep_all)
WORKSPACE_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Ensure src is on the path (for pairenv package)
sys.path.insert(0, str(WORKSPACE_ROOT / "src"))


class TestHealthCheck(unittest.TestCase):
    """Verify health check module is importable and functional."""

    def test_health_check_import(self):
        """Health check module should be importable."""
        import health_check
        self.assertTrue(hasattr(health_check, "run_health_check"))
        self.assertTrue(hasattr(health_check, "Finding"))

    def test_run_health_check_returns_list(self):
        """run_health_check should return a list of findings."""
        import health_check
        result = health_check.run_health_check()
        self.assertIsInstance(result, list)

    def test_finding_class(self):
        """Finding class should have expected attributes."""
        from health_check import Finding
        f = Finding("test", "test_check", "warning", "test message", fixable=True)
        self.assertEqual(f.slug, "test")
        self.assertEqual(f.check, "test_check")
        self.assertEqual(f.severity, "warning")
        self.assertEqual(f.message, "test message")
        self.assertTrue(f.fixable)
        self.assertFalse(f.fixed)
        d = f.to_dict()
        self.assertEqual(d["slug"], "test")


class TestQuickTest(unittest.TestCase):
    """Verify quick_test module is importable and functional."""

    def test_quick_test_import(self):
        """Quick test module should be importable."""
        import quick_test
        # quick_test is a script with check() function and results list
        self.assertTrue(hasattr(quick_test, "check"))
        self.assertTrue(hasattr(quick_test, "results"))

    def test_check_function(self):
        """check() should record results correctly."""
        import quick_test
        # Reset results
        quick_test.results = []
        result = quick_test.check("test_check", True)
        self.assertTrue(result)
        self.assertEqual(len(quick_test.results), 1)
        self.assertEqual(quick_test.results[0], ("test_check", True))


class TestSweepAll(unittest.TestCase):
    """Verify sweep_all module is importable and functional."""

    def test_sweep_all_import(self):
        """Sweep all module should be importable."""
        import sweep_all
        self.assertTrue(hasattr(sweep_all, "sweep_all"))

    def test_sweep_all_callable(self):
        """sweep_all should be callable."""
        import sweep_all
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            # sweep_all should not raise on a valid temp directory
            result = sweep_all.sweep_all(
                str(tmp_path / ".pipeline"),
                str(tmp_path / "sweep_results.json")
            )
            self.assertIsNotNone(result)


class TestPairenvPackage(unittest.TestCase):
    """Verify pairenv package modules are importable."""

    def test_parser_import(self):
        """EnglishParser should be importable."""
        from pairenv.parser import EnglishParser
        self.assertTrue(hasattr(EnglishParser, "parse"))

    def test_registry_import(self):
        """DeviceRegistry should be importable."""
        from pairenv.registry import DeviceRegistry
        self.assertTrue(hasattr(DeviceRegistry, "add_device"))

    def test_handler_import(self):
        """MessageHandler should be importable."""
        from pairenv.message_handler import MessageHandler
        self.assertTrue(hasattr(MessageHandler, "format_response"))

    def test_router_import(self):
        """CommandRouter should be importable."""
        from pairenv.router import CommandRouter
        self.assertTrue(hasattr(CommandRouter, "route"))

    def test_transports_import(self):
        """Transports module should be importable."""
        import pairenv.transports
        self.assertTrue(hasattr(pairenv.transports, "Transport"))

    def test_transports_serial_import(self):
        """SerialTransport should be importable."""
        from pairenv.transports.serial_transport import SerialTransport
        self.assertTrue(hasattr(SerialTransport, "send"))

    def test_abstraction_import(self):
        """Abstraction module should be importable."""
        import pairenv.abstraction
        self.assertTrue(hasattr(pairenv.abstraction, "Abstraction"))

    def test_cli_import(self):
        """CLI module should be importable."""
        import pairenv.cli
        self.assertTrue(hasattr(pairenv.cli, "main"))


class TestConfig(unittest.TestCase):
    """Verify default configuration files."""

    def test_default_registry_json(self):
        """Default registry.json should exist and be valid JSON."""
        default_registry = WORKSPACE_ROOT / "default_registry.json"
        self.assertTrue(default_registry.exists(), "default_registry.json should exist")
        with open(default_registry) as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        self.assertIn("devices", data)


if __name__ == "__main__":
    unittest.main()
