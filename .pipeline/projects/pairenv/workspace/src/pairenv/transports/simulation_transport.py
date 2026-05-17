"""
Simulation transport plugin for pairenv.

Provides simulated device responses for testing without hardware.
"""

import json
from typing import Any, Dict, List, Optional
from ..plugins.base import PluginABC


class SimulationTransport(PluginABC):
    """Simulation transport plugin for testing without hardware."""

    @property
    def name(self) -> str:
        return "simulation_transport"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def protocol(self) -> str:
        return "simulation"

    def __init__(self):
        self._connected = False
        self._simulated_devices: Dict[str, Dict[str, Any]] = {}
        self._last_response = None
        self._default_responses = {
            "turn_on": "Device turned on",
            "turn_off": "Device turned off",
            "read_temp": "25.0",
            "read_sensor": "42",
            "set_pin": "Pin set",
            "read_pin": "HIGH",
        }

    def connect(self, **kwargs) -> bool:
        self._connected = True
        # Register default simulated devices
        self._simulated_devices = {
            "sim-light-1": {"type": "light", "state": "off"},
            "sim-temp-1": {"type": "temperature", "value": 25.0},
            "sim-sensor-1": {"type": "sensor", "value": 42},
            "sim-pin-1": {"type": "pin", "state": "LOW"},
        }
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def send(self, command: str, **kwargs) -> str:
        if not self._connected:
            raise ConnectionError("Simulation not connected")
        device_id = kwargs.get("device_id", "sim-light-1")
        if device_id in self._simulated_devices:
            device = self._simulated_devices[device_id]
            if command == "turn_on":
                device["state"] = "on"
                self._last_response = json.dumps({"device": device_id, "command": command, "result": "Device turned on"})
            elif command == "turn_off":
                device["state"] = "off"
                self._last_response = json.dumps({"device": device_id, "command": command, "result": "Device turned off"})
            elif command == "read_temp":
                self._last_response = json.dumps({"device": device_id, "command": command, "result": str(device.get("value", 25.0))})
            elif command == "read_sensor":
                self._last_response = json.dumps({"device": device_id, "command": command, "result": str(device.get("value", 42))})
            elif command == "set_pin":
                pin_state = kwargs.get("pin_state", "HIGH")
                device["state"] = pin_state
                self._last_response = json.dumps({"device": device_id, "command": command, "result": f"Pin set to {pin_state}"})
            elif command == "read_pin":
                self._last_response = json.dumps({"device": device_id, "command": command, "result": device.get("state", "LOW")})
            else:
                self._last_response = json.dumps({"device": device_id, "command": command, "result": "ok"})
        else:
            self._last_response = json.dumps({"device": device_id, "command": command, "result": "device not found"})
        return self._last_response

    def receive(self) -> Optional[str]:
        return self._last_response

    def discover(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        return [
            {"id": did, "name": f"Sim {d['type']} {did}", "protocol": "simulation", "status": "online"}
            for did, d in self._simulated_devices.items()
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "protocol": "simulation",
            "features": ["mock_responses", "state_tracking", "error_injection"],
            "max_payload": 1048576,
            "simulated_devices": list(self._simulated_devices.keys()),
        }

    def add_device(self, device_id: str, device_type: str, **kwargs) -> bool:
        """Add a simulated device."""
        self._simulated_devices[device_id] = {"type": device_type, **kwargs}
        return True

    def remove_device(self, device_id: str) -> bool:
        """Remove a simulated device."""
        if device_id in self._simulated_devices:
            del self._simulated_devices[device_id]
            return True
        return False
