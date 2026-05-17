"""
Comprehensive test suite for pairenv.

Tests all components: plugins, transports, coordinator, NLP parser, and dashboard.
"""

import json
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pairenv.plugins.base import PluginABC, PluginState
from pairenv.plugins.registry import PluginRegistry
from pairenv.plugins.loader import PluginLoader
from pairenv.transports import (
    SerialTransport,
    MQTTTransport,
    WiFiTransport,
    BLETransport,
    SimulationTransport,
)
from pairenv.coordinator import MultiDeviceCoordinator, DeviceStatus
from pairenv.nlp_parser import EnhancedNLPParser, Intent, ParsedCommand, Entity
from pairenv.dashboard import WebDashboard, DashboardRequestHandler


# ==================== Plugin Base Tests ====================

class TestPluginABC(unittest.TestCase):
    """Tests for the PluginABC base class."""

    def test_plugin_abc_is_abstract(self):
        """PluginABC should not be instantiable directly."""
        with self.assertRaises(TypeError):
            PluginABC()

    def test_plugin_state_enum(self):
        """PluginState should have correct values."""
        self.assertEqual(PluginState.INACTIVE.value, "inactive")
        self.assertEqual(PluginState.ACTIVE.value, "active")
        self.assertEqual(PluginState.ERROR.value, "error")


class TestPluginRegistry(unittest.TestCase):
    """Tests for PluginRegistry."""

    def setUp(self):
        self.registry = PluginRegistry()

    def test_register_and_get(self):
        """Test registering and retrieving a plugin."""
        plugin = SimulationTransport()
        self.registry.register(plugin)
        retrieved = self.registry.get("simulation_transport")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "simulation_transport")

    def test_register_duplicate(self):
        """Test that registering a duplicate plugin raises."""
        plugin1 = SimulationTransport()
        plugin2 = WiFiTransport()
        self.registry.register(plugin1)
        with self.assertRaises(ValueError):
            self.registry.register(plugin2)

    def test_unregister(self):
        """Test unregistering a plugin."""
        plugin = SimulationTransport()
        self.registry.register(plugin)
        self.registry.unregister("simulation_transport")
        retrieved = self.registry.get("simulation_transport")
        self.assertIsNone(retrieved)

    def test_get_active_plugins(self):
        """Test getting active plugins."""
        plugin1 = SimulationTransport()
        plugin2 = WiFiTransport()
        self.registry.register(plugin1)
        self.registry.register(plugin2)
        active = self.registry.get_active_plugins()
        self.assertIn("simulation_transport", active)
        self.assertIn("wifi_transport", active)

    def test_get_inactive_plugins(self):
        """Test getting inactive plugins."""
        plugin = SimulationTransport()
        self.registry.register(plugin)
        self.registry.deactivate("simulation_transport")
        inactive = self.registry.get_inactive_plugins()
        self.assertIn("simulation_transport", inactive)

    def test_activate_deactivate(self):
        """Test activating and deactivating plugins."""
        plugin = SimulationTransport()
        self.registry.register(plugin)
        self.registry.deactivate("simulation_transport")
        self.registry.activate("simulation_transport")
        active = self.registry.get_active_plugins()
        self.assertIn("simulation_transport", active)

    def test_clear(self):
        """Test clearing all plugins."""
        self.registry.register(SimulationTransport())
        self.registry.register(WiFiTransport())
        self.registry.clear()
        self.assertEqual(len(self.registry.get_active_plugins()), 0)

    def test_contains(self):
        """Test __contains__."""
        plugin = SimulationTransport()
        self.registry.register(plugin)
        self.assertIn("simulation_transport", self.registry)
        self.assertNotIn("nonexistent", self.registry)


# ==================== Transport Plugin Tests ====================

class TestSerialTransport(unittest.TestCase):
    """Tests for SerialTransport."""

    def setUp(self):
        self.transport = SerialTransport()

    def test_name(self):
        self.assertEqual(self.transport.name, "serial_transport")

    def test_protocol(self):
        self.assertEqual(self.transport.protocol, "serial")

    def test_initial_state(self):
        self.assertEqual(self.transport.state, PluginState.INACTIVE)

    def test_activate_deactivate(self):
        self.transport.activate()
        self.assertEqual(self.transport.state, PluginState.ACTIVE)
        self.transport.deactivate()
        self.assertEqual(self.transport.state, PluginState.INACTIVE)

    def test_send_command(self):
        self.transport.activate()
        result = self.transport.send_command("test_device", "turn_on")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["command"], "turn_on")

    def test_send_command_inactive(self):
        with self.assertRaises(RuntimeError):
            self.transport.send_command("test_device", "turn_on")

    def test_get_capabilities(self):
        caps = self.transport.get_capabilities()
        self.assertIn("serial", caps["protocols"])
        self.assertIn("turn_on", caps["commands"])

    def test_to_dict(self):
        self.transport.activate()
        d = self.transport.to_dict()
        self.assertEqual(d["name"], "serial_transport")
        self.assertEqual(d["state"], "active")


class TestMQTTTransport(unittest.TestCase):
    """Tests for MQTTTransport."""

    def setUp(self):
        self.transport = MQTTTransport()

    def test_name(self):
        self.assertEqual(self.transport.name, "mqtt_transport")

    def test_protocol(self):
        self.assertEqual(self.transport.protocol, "mqtt")

    def test_default_config(self):
        self.assertEqual(self.transport.config["host"], "localhost")
        self.assertEqual(self.transport.config["port"], 1883)

    def test_custom_config(self):
        transport = MQTTTransport(host="test", port=1234)
        self.assertEqual(transport.config["host"], "test")
        self.assertEqual(transport.config["port"], 1234)

    def test_send_command(self):
        self.transport.activate()
        result = self.transport.send_command("test_device", "turn_on")
        self.assertEqual(result["status"], "success")


class TestWiFiTransport(unittest.TestCase):
    """Tests for WiFiTransport."""

    def setUp(self):
        self.transport = WiFiTransport()

    def test_name(self):
        self.assertEqual(self.transport.name, "wifi_transport")

    def test_protocol(self):
        self.assertEqual(self.transport.protocol, "wifi")

    def test_send_command(self):
        self.transport.activate()
        result = self.transport.send_command("test_device", "turn_on")
        self.assertEqual(result["status"], "success")


class TestBLETransport(unittest.TestCase):
    """Tests for BLETransport."""

    def setUp(self):
        self.transport = BLETransport()

    def test_name(self):
        self.assertEqual(self.transport.name, "ble_transport")

    def test_protocol(self):
        self.assertEqual(self.transport.protocol, "ble")

    def test_send_command(self):
        self.transport.activate()
        result = self.transport.send_command("test_device", "turn_on")
        self.assertEqual(result["status"], "success")


class TestSimulationTransport(unittest.TestCase):
    """Tests for SimulationTransport."""

    def setUp(self):
        self.transport = SimulationTransport()

    def test_name(self):
        self.assertEqual(self.transport.name, "simulation_transport")

    def test_protocol(self):
        self.assertEqual(self.transport.protocol, "simulation")

    def test_send_command(self):
        self.transport.activate()
        result = self.transport.send_command("test_device", "turn_on")
        self.assertEqual(result["status"], "success")

    def test_simulated_state(self):
        self.transport.activate()
        self.transport.send_command("test_device", "turn_on")
        state = self.transport.get_device_state("test_device")
        self.assertEqual(state, "on")


# ==================== Coordinator Tests ====================

class TestDeviceStatus(unittest.TestCase):
    """Tests for DeviceStatus."""

    def test_creation(self):
        status = DeviceStatus(
            device_id="test",
            name="Test Device",
            protocol="serial",
            status="online",
        )
        self.assertEqual(status.device_id, "test")
        self.assertEqual(status.name, "Test Device")
        self.assertEqual(status.protocol, "serial")
        self.assertEqual(status.status, "online")

    def test_to_dict(self):
        status = DeviceStatus(
            device_id="test",
            name="Test Device",
            protocol="serial",
            status="online",
        )
        d = status.to_dict()
        self.assertEqual(d["device_id"], "test")
        self.assertEqual(d["name"], "Test Device")


class TestMultiDeviceCoordinator(unittest.TestCase):
    """Tests for MultiDeviceCoordinator."""

    def setUp(self):
        self.coordinator = MultiDeviceCoordinator()
        self.coordinator.registry.register(SimulationTransport())

    def test_add_device(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        devices = self.coordinator.get_all_device_statuses()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "Test Device")

    def test_send_command(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        result = self.coordinator.send_command("test", "turn_on")
        self.assertEqual(result["status"], "success")

    def test_send_command_unknown_device(self):
        with self.assertRaises(ValueError):
            self.coordinator.send_command("unknown", "turn_on")

    def test_send_command_unknown_plugin(self):
        with self.assertRaises(ValueError):
            self.coordinator.send_command("test", "turn_on")

    def test_get_devices_by_protocol(self):
        self.coordinator.add_device("test1", "Test 1", "simulation")
        self.coordinator.add_device("test2", "Test 2", "simulation")
        devices = self.coordinator.get_devices_by_protocol("simulation")
        self.assertIn("test1", devices)
        self.assertIn("test2", devices)

    def test_get_devices_by_plugin(self):
        self.coordinator.add_device("test1", "Test 1", "simulation")
        self.coordinator.add_device("test2", "Test 2", "simulation")
        devices = self.coordinator.get_devices_by_plugin("simulation_transport")
        self.assertIn("test1", devices)
        self.assertIn("test2", devices)

    def test_remove_device(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        self.assertTrue(self.coordinator.remove_device("test"))
        devices = self.coordinator.get_all_device_statuses()
        self.assertEqual(len(devices), 0)

    def test_remove_nonexistent_device(self):
        self.assertFalse(self.coordinator.remove_device("nonexistent"))

    def test_command_history(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        self.coordinator.send_command("test", "turn_on")
        self.coordinator.send_command("test", "turn_off")
        history = self.coordinator.get_command_history()
        self.assertEqual(len(history), 2)

    def test_clear_command_history(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        self.coordinator.send_command("test", "turn_on")
        self.coordinator.clear_command_history()
        history = self.coordinator.get_command_history()
        self.assertEqual(len(history), 0)

    def test_execute_orchestration(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        steps = [
            {"device_id": "test", "command": "turn_on"},
            {"device_id": "test", "command": "turn_off"},
        ]
        results = self.coordinator.execute_orchestration(steps)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[1]["status"], "success")

    def test_get_capabilities_summary(self):
        caps = self.coordinator.get_capabilities_summary()
        self.assertIn("simulation_transport", caps)

    def test_discover_devices(self):
        discovered = self.coordinator.discover_devices()
        self.assertIsInstance(discovered, list)

    def test_repr(self):
        self.coordinator.add_device("test", "Test Device", "simulation")
        repr_str = repr(self.coordinator)
        self.assertIn("devices=1", repr_str)


# ==================== NLP Parser Tests ====================

class TestEnhancedNLPParser(unittest.TestCase):
    """Tests for EnhancedNLPParser."""

    def setUp(self):
        self.parser = EnhancedNLPParser()

    def test_detect_language_en(self):
        lang = self.parser.detect_language("turn on the light")
        self.assertEqual(lang, "en")

    def test_detect_language_es(self):
        lang = self.parser.detect_language("enciende la luz")
        self.assertEqual(lang, "es")

    def test_detect_language_fr(self):
        lang = self.parser.detect_language("allume la lumière")
        self.assertEqual(lang, "fr")

    def test_classify_intent_turn_on(self):
        intent, conf = self.parser.classify_intent("turn on the light")
        self.assertEqual(intent, Intent.TURN_ON)
        self.assertGreater(conf, 0)

    def test_classify_intent_turn_off(self):
        intent, conf = self.parser.classify_intent("turn off the light")
        self.assertEqual(intent, Intent.TURN_OFF)
        self.assertGreater(conf, 0)

    def test_classify_intent_unknown(self):
        intent, conf = self.parser.classify_intent("random text")
        self.assertEqual(intent, Intent.UNKNOWN)
        self.assertEqual(conf, 0.0)

    def test_extract_entities_device(self):
        entities = self.parser.extract_entities("turn on device light1")
        device_entities = [e for e in entities if e.entity_type == "device"]
        self.assertTrue(len(device_entities) > 0)

    def test_extract_entities_value(self):
        entities = self.parser.extract_entities("set value to 42")
        value_entities = [e for e in entities if e.entity_type == "value"]
        self.assertTrue(len(value_entities) > 0)

    def test_parse_turn_on(self):
        parsed = self.parser.parse("turn on the light")
        self.assertEqual(parsed.intent, Intent.TURN_ON)
        self.assertGreater(parsed.confidence, 0)

    def test_parse_turn_off(self):
        parsed = self.parser.parse("turn off the light")
        self.assertEqual(parsed.intent, Intent.TURN_OFF)

    def test_parse_and_command(self):
        cmd = self.parser.parse_and_command("turn on the light")
        self.assertEqual(cmd["action"], "turn_on")

    def test_add_device_alias(self):
        self.parser.add_device_alias("device_1", "light")
        resolved = self.parser.resolve_device("light")
        self.assertEqual(resolved, "device_1")

    def test_get_supported_intents(self):
        intents = self.parser.get_supported_intents()
        self.assertIn("turn_on", intents)

    def test_get_supported_languages(self):
        langs = self.parser.get_supported_languages()
        self.assertIn("en", langs)
        self.assertIn("es", langs)
        self.assertIn("fr", langs)


# ==================== Dashboard Tests ====================

class TestWebDashboard(unittest.TestCase):
    """Tests for WebDashboard."""

    def setUp(self):
        self.coordinator = MultiDeviceCoordinator()
        self.coordinator.registry.register(SimulationTransport())
        self.dashboard = WebDashboard(self.coordinator, port=0)  # Port 0 = random

    def test_init(self):
        self.assertEqual(self.dashboard.host, "0.0.0.0")
        self.assertEqual(self.dashboard.port, 0)

    def test_start_stop(self):
        self.dashboard.start()
        self.assertIsNotNone(self.dashboard.server)
        self.dashboard.stop()
        self.assertIsNone(self.dashboard.server)

    def test_context_manager(self):
        with WebDashboard(self.coordinator, port=0) as dashboard:
            self.assertIsNotNone(dashboard.server)
        self.assertIsNone(dashboard.server)


class TestDashboardRequestHandler(unittest.TestCase):
    """Tests for DashboardRequestHandler."""

    def setUp(self):
        self.coordinator = MultiDeviceCoordinator()
        self.coordinator.registry.register(SimulationTransport())
        self.coordinator.add_device("test", "Test Device", "simulation")
        DashboardRequestHandler.coordinator = self.coordinator

    def test_serve_index(self):
        handler = DashboardRequestHandler(
            MagicMock(),
            ("127.0.0.1", 12345),
            MagicMock(),
        )
        # Mock the request
        handler.path = "/"
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        handler.wfile.write.assert_called()
        call_args = handler.wfile.write.call_args
        body = call_args[0][0]
        self.assertIn(b"<!DOCTYPE html>", body)

    def test_get_devices(self):
        handler = DashboardRequestHandler(
            MagicMock(),
            ("127.0.0.1", 12345),
            MagicMock(),
        )
        handler.path = "/api/devices"
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        call_args = handler.wfile.write.call_args
        body = call_args[0][0]
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_get_status(self):
        handler = DashboardRequestHandler(
            MagicMock(),
            ("127.0.0.1", 12345),
            MagicMock(),
        )
        handler.path = "/api/status"
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        call_args = handler.wfile.write.call_args
        body = call_args[0][0]
        data = json.loads(body.decode())
        self.assertIn("devices", data)
        self.assertIn("plugins", data)

    def test_send_command(self):
        handler = DashboardRequestHandler(
            MagicMock(),
            ("127.0.0.1", 12345),
            MagicMock(),
        )
        handler.path = "/api/command"
        handler.headers = {"Content-Length": "42"}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.rfile = MagicMock()
        handler.rfile.read = MagicMock(return_value=b'{"device_id": "test", "command": "turn_on"}')

        handler.do_POST()

        call_args = handler.wfile.write.call_args
        body = call_args[0][0]
        data = json.loads(body.decode())
        self.assertEqual(data["status"], "success")

    def test_not_found(self):
        handler = DashboardRequestHandler(
            MagicMock(),
            ("127.0.0.1", 12345),
            MagicMock(),
        )
        handler.path = "/nonexistent"
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        call_args = handler.wfile.write.call_args
        body = call_args[0][0]
        data = json.loads(body.decode())
        self.assertEqual(data["error"], "Not found")


# ==================== Integration Tests ====================

class TestIntegration(unittest.TestCase):
    """Integration tests for the full system."""

    def test_full_workflow(self):
        """Test the full workflow from NLP to device control."""
        # Setup
        coordinator = MultiDeviceCoordinator()
        coordinator.registry.register(SimulationTransport())
        coordinator.add_device("light1", "Living Room Light", "simulation")

        parser = EnhancedNLPParser()
        dashboard = WebDashboard(coordinator, port=0)

        # Parse natural language
        parsed = parser.parse("turn on the light")
        self.assertEqual(parsed.intent, Intent.TURN_ON)

        # Get structured command
        cmd = parser.parse_and_command("turn on the light")
        self.assertEqual(cmd["action"], "turn_on")

        # Execute via coordinator
        result = coordinator.send_command("light1", "turn_on")
        self.assertEqual(result["status"], "success")

        # Check device state
        devices = coordinator.get_all_device_statuses()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "Living Room Light")

        # Start dashboard
        dashboard.start()
        self.assertIsNotNone(dashboard.server)
        dashboard.stop()

    def test_multi_device_workflow(self):
        """Test controlling multiple devices."""
        coordinator = MultiDeviceCoordinator()
        coordinator.registry.register(SimulationTransport())

        coordinator.add_device("light1", "Light 1", "simulation")
        coordinator.add_device("light2", "Light 2", "simulation")
        coordinator.add_device("sensor1", "Sensor 1", "simulation")

        # Control all devices
        coordinator.send_command("light1", "turn_on")
        coordinator.send_command("light2", "turn_on")
        coordinator.send_command("sensor1", "read_sensor")

        # Check history
        history = coordinator.get_command_history()
        self.assertEqual(len(history), 3)

        # Get devices by protocol
        sim_devices = coordinator.get_devices_by_protocol("simulation")
        self.assertEqual(len(sim_devices), 3)


if __name__ == "__main__":
    unittest.main()
