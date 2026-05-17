"""test_harness_capabilities.py — Tests for pipeline harness capabilities.

Tests the health check and quick test infrastructure at the workspace root level.
"""

import json
import os
import pathlib
import sys
import unittest

# Ensure workspace root is on the path (for health_check, quick_test, sweep_all)
WORKSPACE_ROOT = pathlib.Path(__file__).parent
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
        quick_test.results.clear()
        quick_test.check("test_pass", True)
        quick_test.check("test_fail", False, "detail")
        self.assertEqual(len(quick_test.results), 2)
        self.assertEqual(quick_test.results[0], ("test_pass", True))
        self.assertEqual(quick_test.results[1], ("test_fail", False))


class TestSweepAll(unittest.TestCase):
    """Verify sweep_all module is importable and functional."""

    def test_sweep_all_import(self):
        """sweep_all module should be importable."""
        import sweep_all
        self.assertTrue(hasattr(sweep_all, "sweep_all"))

    def test_sweep_all_callable(self):
        """sweep_all should be callable with pipeline_dir and results_path."""
        import sweep_all
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            pipeline_dir = tmp / ".pipeline"
            pipeline_dir.mkdir(parents=True)
            results_path = tmp / "results.json"
            try:
                result = sweep_all.sweep_all(str(pipeline_dir), str(results_path))
                # Should return a dict or None
                self.assertTrue(result is None or isinstance(result, dict))
            except Exception as e:
                # If it fails, it should be a known error, not import error
                self.fail(f"sweep_all raised: {e}")


class TestPairenvPackage(unittest.TestCase):
    """Verify pairenv package modules are importable."""

    def test_abstraction_import(self):
        import pairenv.abstraction
        self.assertTrue(hasattr(pairenv.abstraction, "DeviceABC"))

    def test_cli_import(self):
        import pairenv.cli
        self.assertTrue(hasattr(pairenv.cli, "main"))

    def test_handler_import(self):
        import pairenv.handler
        self.assertTrue(hasattr(pairenv.handler, "Handler"))
        self.assertTrue(hasattr(pairenv.handler, "MessageHandler"))

    def test_parser_import(self):
        import pairenv.parser
        self.assertTrue(hasattr(pairenv.parser, "EnglishParser"))

    def test_registry_import(self):
        import pairenv.registry
        self.assertTrue(hasattr(pairenv.registry, "DeviceRegistry"))

    def test_router_import(self):
        import pairenv.router
        self.assertTrue(hasattr(pairenv.router, "CommandRouter"))
        self.assertTrue(hasattr(pairenv.router, "MessageHandler"))

    def test_transports_import(self):
        import pairenv.transports
        self.assertTrue(hasattr(pairenv.transports, "SerialTransport"))

    def test_transports_serial_import(self):
        from pairenv.transports import SerialTransport
        self.assertTrue(hasattr(SerialTransport, "send"))


class TestConfig(unittest.TestCase):
    """Verify configuration files are valid."""

    def test_default_registry_json(self):
        """default_registry.json should be valid JSON."""
        config_path = WORKSPACE_ROOT / "src" / "pairenv" / "config" / "default_registry.json"
        self.assertTrue(config_path.exists(), "default_registry.json should exist")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)


if __name__ == "__main__":
    unittest.main()
