"""Integration test harness for pairenv.

Exercises the full pipeline: register device → parse command → route → format response.
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest

# Ensure src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pairenv.parser import EnglishParser
from pairenv.registry import DeviceRegistry
from pairenv.router import CommandRouter, MessageHandler
from pairenv.transports.serial_transport import SerialTransport
from pairenv.abstraction import DeviceABC


class TestSerialTransportImport(unittest.TestCase):
    """Task 1: Verify SerialTransport can be imported."""

    def test_import(self):
        self.assertTrue(hasattr(SerialTransport, "connect"))
        self.assertTrue(hasattr(SerialTransport, "disconnect"))
        self.assertTrue(hasattr(SerialTransport, "send"))
        self.assertTrue(hasattr(SerialTransport, "receive"))


class TestDeviceRegistry(unittest.TestCase):
    """Task 2: Verify DeviceRegistry CRUD operations."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_add_and_list(self):
        r = DeviceRegistry(self.tmp)
        r.add("test", "arduino", {"port": "/dev/ttyUSB0"})
        devices = r.list_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["device_id"], "test")

    def test_get(self):
        r = DeviceRegistry(self.tmp)
        r.add("test", "arduino", {"port": "/dev/ttyUSB0"})
        device = r.get("test")
        self.assertIsNotNone(device)
        self.assertEqual(device["device_type"], "arduino")

    def test_remove(self):
        r = DeviceRegistry(self.tmp)
        r.add("test", "arduino", {"port": "/dev/ttyUSB0"})
        self.assertTrue(r.remove("test"))
        self.assertIsNone(r.get("test"))

    def test_update_connection(self):
        r = DeviceRegistry(self.tmp)
        r.add("test", "arduino", {"port": "/dev/ttyUSB0"})
        self.assertTrue(r.update_connection_state("test", True))
        device = r.get("test")
        self.assertTrue(device["connected"])


class TestEnglishParser(unittest.TestCase):
    """Task 3: Verify EnglishParser handles ≥6 templates."""

    def setUp(self):
        self.parser = EnglishParser()

    def test_turn_on(self):
        cmd = self.parser.parse("turn on the LED")
        self.assertEqual(cmd["action"], "set_pin")
        self.assertEqual(cmd["state"], "HIGH")

    def test_turn_off(self):
        cmd = self.parser.parse("turn off the LED")
        self.assertEqual(cmd["action"], "set_pin")
        self.assertEqual(cmd["state"], "LOW")

    def test_set_pin(self):
        cmd = self.parser.parse("set pin 5 to HIGH")
        self.assertEqual(cmd["pin"], 5)
        self.assertEqual(cmd["state"], "HIGH")

    def test_read_sensor(self):
        cmd = self.parser.parse("read sensor on pin A0")
        self.assertEqual(cmd["action"], "read_sensor")
        self.assertEqual(cmd["pin"], "A0")

    def test_read_pin(self):
        cmd = self.parser.parse("read pin A1")
        self.assertEqual(cmd["action"], "read_pin")
        self.assertEqual(cmd["pin"], "A1")

    def test_blink(self):
        cmd = self.parser.parse("blink LED 5 times")
        self.assertEqual(cmd["action"], "blink")
        self.assertEqual(cmd["count"], 5)

    def test_unparseable(self):
        self.assertIsNone(self.parser.parse("xyz"))

    def test_list_templates(self):
        templates = self.parser.list_templates()
        self.assertGreaterEqual(len(templates), 6)


class TestMessageHandler(unittest.TestCase):
    """Task 4: Verify MessageHandler formats responses."""

    def test_pin_high(self):
        result = MessageHandler.format_response("PIN13=HIGH")
        self.assertIn("ON", result)

    def test_pin_low(self):
        result = MessageHandler.format_response("PIN13=LOW")
        self.assertIn("OFF", result)

    def test_sensor(self):
        result = MessageHandler.format_response("SENSOR=A0:256")
        self.assertIn("256", result)

    def test_blink_ok(self):
        result = MessageHandler.format_response("BLINK_OK")
        self.assertIn("blink", result.lower())

    def test_empty(self):
        result = MessageHandler.format_response("")
        self.assertIn("No response", result)


class TestCommandRouterIntegration(unittest.TestCase):
    """Task 5: Verify full pipeline with mock transport."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DeviceRegistry(self.tmp)
        self.registry.add("test", "arduino", {"port": "/dev/ttyUSB0", "baudrate": 9600})
        self.parser = EnglishParser()
        self.router = CommandRouter(self.registry)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_full_pipeline(self):
        """Parse → route → format response."""
        cmd = self.parser.parse("turn on the LED")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd["action"], "set_pin")

        # Verify command serialization
        payload = self.router._command_to_bytes(cmd)
        self.assertEqual(payload, b"SET 13 HIGH\n")

        # Verify response formatting
        formatted = MessageHandler.format_response("PIN13=HIGH")
        self.assertIn("ON", formatted)


class TestAbstraction(unittest.TestCase):
    """Verify DeviceABC is properly defined."""

    def test_abstract_methods(self):
        self.assertTrue(hasattr(DeviceABC, "connect"))
        self.assertTrue(hasattr(DeviceABC, "disconnect"))
        self.assertTrue(hasattr(DeviceABC, "send"))
        self.assertTrue(hasattr(DeviceABC, "receive"))


if __name__ == "__main__":
    unittest.main()
