"""Device registry with JSON-based pairing state persistence."""

import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "config", "default_registry.json"
)


class DeviceRegistry:
    """Persists device pairings to a JSON file on disk.

    Each device entry stores:
        - device_id (str): unique identifier
        - device_type (str): e.g. 'arduino', 'sensor', 'actuator'
        - transport_config (dict): transport-specific settings (port, baudrate, etc.)
        - connected (bool): current connection state
    """

    def __init__(self, path: Optional[str] = None):
        """Initialize the registry.

        Args:
            path: Path to the JSON registry file. Defaults to the bundled
                  default_registry.json.
        """
        self.path = path or DEFAULT_REGISTRY_PATH
        self._ensure_file()

    # -- internal helpers ------------------------------------------------

    def _ensure_file(self) -> None:
        """Create the registry file if it does not exist."""
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                json.dump({"devices": {}}, f, indent=2)

    def _load(self) -> Dict[str, Any]:
        """Read the entire registry from disk."""
        with open(self.path, "r") as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]) -> None:
        """Write the registry to disk."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    # -- public API ------------------------------------------------------

    def add(
        self,
        device_id: str,
        device_type: str,
        transport_config: Dict[str, Any],
    ) -> None:
        """Register a new device pairing.

        Args:
            device_id: Unique identifier for the device.
            device_type: Type of device (e.g. 'arduino').
            transport_config: Transport-specific configuration dict.
        """
        data = self._load()
        data["devices"][device_id] = {
            "device_id": device_id,
            "device_type": device_type,
            "transport_config": transport_config,
            "connected": False,
        }
        self._save(data)

    def get(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a device entry by ID.

        Args:
            device_id: The device identifier.

        Returns:
            Device dict or None if not found.
        """
        data = self._load()
        return data["devices"].get(device_id)

    def list_devices(self) -> List[Dict[str, Any]]:
        """Return all paired devices.

        Returns:
            List of device dicts.
        """
        data = self._load()
        return list(data["devices"].values())

    def remove(self, device_id: str) -> bool:
        """Remove a device from the registry.

        Args:
            device_id: The device identifier to remove.

        Returns:
            True if the device was removed, False if not found.
        """
        data = self._load()
        if device_id in data["devices"]:
            del data["devices"][device_id]
            self._save(data)
            return True
        return False

    def update_connection_state(self, device_id: str, connected: bool) -> bool:
        """Update the connection state of a device.

        Args:
            device_id: The device identifier.
            connected: New connection state.

        Returns:
            True if the device was found and updated.
        """
        data = self._load()
        if device_id in data["devices"]:
            data["devices"][device_id]["connected"] = connected
            self._save(data)
            return True
        return False
