"""
BLE transport plugin for pairenv.

Connects to devices via Bluetooth Low Energy protocol.
"""

from typing import Any, Dict, List, Optional
from ..plugins.base import PluginABC


class BLETransport(PluginABC):
    """BLE transport plugin for Bluetooth Low Energy device communication."""

    @property
    def name(self) -> str:
        return "ble_transport"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def protocol(self) -> str:
        return "ble"

    def __init__(self):
        self._connected = False
        self._device_address = None
        self._last_data = None

    def connect(self, address: str = "00:00:00:00:00:00", **kwargs) -> bool:
        self._device_address = address
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        self._device_address = None
        return True

    def send(self, command: str, **kwargs) -> str:
        if not self._connected:
            raise ConnectionError("BLE not connected")
        self._last_data = f"BLE WRITE {self._device_address}: {command}"
        return self._last_data

    def receive(self) -> Optional[str]:
        return self._last_data

    def discover(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        return [
            {"id": "ble-device-1", "name": "BLE Device 1", "protocol": "ble", "status": "discoverable", "address": "AA:BB:CC:DD:EE:01"},
            {"id": "ble-device-2", "name": "BLE Device 2", "protocol": "ble", "status": "discoverable", "address": "AA:BB:CC:DD:EE:02"},
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "protocol": "ble",
            "features": ["gatt_write", "gatt_read", "gatt_notify", "discovery"],
            "max_payload": 512,
            "ble_version": "5.0",
        }
