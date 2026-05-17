"""
Multi-device coordinator for pairenv.

Manages multiple devices across different transport protocols,
routes commands to the correct device, and aggregates responses.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .plugins.base import PluginABC
from .plugins.registry import PluginRegistry
from .registry import DeviceRegistry

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Status of a managed device."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class ManagedDevice:
    """Represents a device managed by the coordinator."""

    def __init__(self, device_id: str, name: str, protocol: str, plugin: PluginABC):
        self.device_id = device_id
        self.name = name
        self.protocol = protocol
        self.plugin = plugin
        self.status = DeviceStatus.OFFLINE
        self.last_seen: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "protocol": self.protocol,
            "status": self.status.value,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }


class MultiDeviceCoordinator:
    """
    Coordinates multiple devices across different transport protocols.

    Features:
        - Device discovery across all transports
        - Command routing to the correct device
        - Device status tracking
        - Batch command execution
        - Cross-device orchestration
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or PluginRegistry()
        self._devices: Dict[str, ManagedDevice] = {}
        self._device_to_plugin: Dict[str, str] = {}
        self._command_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    @property
    def devices(self) -> Dict[str, ManagedDevice]:
        return dict(self._devices)

    def register_device(self, device_id: str, name: str, protocol: str, plugin: PluginABC) -> bool:
        """Register a device with the coordinator."""
        if device_id in self._devices:
            logger.warning("Device '%s' already registered, updating.", device_id)
        managed = ManagedDevice(device_id, name, protocol, plugin)
        self._devices[device_id] = managed
        self._device_to_plugin[device_id] = plugin.name
        logger.info("Registered device '%s' (%s) via plugin '%s'", name, protocol, plugin.name)
        return True

    def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover devices across all active plugins."""
        discovered = []
        for plugin_name in self.registry.get_active_plugins():
            plugin = self.registry.get(plugin_name)
            if plugin:
                try:
                    devices = plugin.discover()
                    for dev in devices:
                        dev_id = dev.get("id", f"{plugin_name}-{dev.get('name', 'unknown')}")
                        dev["plugin"] = plugin_name
                        discovered.append(dev)
                        # Auto-register discovered devices
                        self.register_device(
                            dev_id,
                            dev.get("name", dev_id),
                            dev.get("protocol", plugin.protocol),
                            plugin,
                        )
                except Exception as e:
                    logger.error("Discovery failed for plugin '%s': %s", plugin_name, e)
        return discovered

    def send_command(self, device_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """Send a command to a specific device."""
        if device_id not in self._devices:
            return {"error": f"Device '{device_id}' not found"}

        device = self._devices[device_id]
        plugin_name = self._device_to_plugin.get(device_id)
        plugin = self.registry.get(plugin_name) if plugin_name else None

        if not plugin:
            return {"error": f"No plugin found for device '{device_id}'"}

        try:
            device.status = DeviceStatus.BUSY
            device.last_seen = time.time()
            response = plugin.send(command, device_id=device_id, **kwargs)
            result = {
                "device_id": device_id,
                "command": command,
                "response": response,
                "status": "success",
                "timestamp": time.time(),
            }
            self._command_history.append(result)
            device.status = DeviceStatus.ONLINE
            return result
        except Exception as e:
            device.status = DeviceStatus.ERROR
            result = {
                "device_id": device_id,
                "command": command,
                "error": str(e),
                "status": "error",
                "timestamp": time.time(),
            }
            self._command_history.append(result)
            return result

    def batch_send(self, commands: List[Tuple[str, str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Send multiple commands to multiple devices.

        Args:
            commands: List of (device_id, command, kwargs) tuples
        """
        results = []
        for device_id, command, kwargs in commands:
            result = self.send_command(device_id, command, **kwargs)
            results.append(result)
        return results

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific device."""
        device = self._devices.get(device_id)
        if device:
            return device.to_dict()
        return None

    def get_all_device_statuses(self) -> List[Dict[str, Any]]:
        """Get the status of all managed devices."""
        return [dev.to_dict() for dev in self._devices.values()]

    def get_command_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent command history."""
        return self._command_history[-limit:]

    def clear_command_history(self) -> None:
        """Clear the command history."""
        self._command_history.clear()

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the coordinator."""
        if device_id in self._devices:
            del self._devices[device_id]
            self._device_to_plugin.pop(device_id, None)
            logger.info("Removed device '%s'", device_id)
            return True
        return False

    def get_devices_by_protocol(self, protocol: str) -> List[str]:
        """Get all device IDs for a specific protocol."""
        return [did for did, dev in self._devices.items() if dev.protocol == protocol]

    def get_devices_by_plugin(self, plugin_name: str) -> List[str]:
        """Get all device IDs managed by a specific plugin."""
        return [did for did, pname in self._device_to_plugin.items() if pname == plugin_name]

    def execute_orchestration(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a sequence of steps as an orchestration.

        Each step is a dict with:
            - device_id: str
            - command: str
            - kwargs: dict (optional)
            - wait: float (optional, seconds to wait after step)
        """
        results = []
        for step in steps:
            device_id = step["device_id"]
            command = step["command"]
            kwargs = step.get("kwargs", {})
            wait = step.get("wait", 0)

            result = self.send_command(device_id, command, **kwargs)
            results.append(result)

            if wait > 0:
                time.sleep(wait)

        return results

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of all plugin capabilities."""
        summary = {}
        for plugin_name in self.registry.get_active_plugins():
            plugin = self.registry.get(plugin_name)
            if plugin:
                caps = plugin.get_capabilities()
                summary[plugin_name] = caps
        return summary

    def __repr__(self) -> str:
        return f"<MultiDeviceCoordinator devices={len(self._devices)} plugins={len(self.registry.get_active_plugins())}>"
