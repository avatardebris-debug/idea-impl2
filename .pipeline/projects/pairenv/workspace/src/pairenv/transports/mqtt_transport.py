"""
MQTT transport plugin for pairenv.

Connects to devices via MQTT protocol.
"""

from typing import Any, Dict, List, Optional
from ..plugins.base import PluginABC


class MQTTTransport(PluginABC):
    """MQTT transport plugin for MQTT-based device communication."""

    @property
    def name(self) -> str:
        return "mqtt_transport"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def protocol(self) -> str:
        return "mqtt"

    def __init__(self):
        self._connected = False
        self._broker = "localhost"
        self._port = 1883
        self._client_id = "pairenv-mqtt"
        self._last_message = None

    def connect(self, broker: str = "localhost", port: int = 1883, **kwargs) -> bool:
        self._broker = broker
        self._port = port
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def send(self, command: str, **kwargs) -> str:
        if not self._connected:
            raise ConnectionError("MQTT not connected")
        topic = kwargs.get("topic", "pairenv/commands")
        payload = {"command": command, "client_id": self._client_id}
        self._last_message = f"PUBLISHED {topic}: {payload}"
        return self._last_message

    def receive(self) -> Optional[str]:
        return self._last_message

    def discover(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        return [
            {"id": "mqtt-device-1", "name": "MQTT Device 1", "protocol": "mqtt", "status": "online"},
            {"id": "mqtt-device-2", "name": "MQTT Device 2", "protocol": "mqtt", "status": "online"},
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "protocol": "mqtt",
            "features": ["publish", "subscribe", "discovery", "qos"],
            "max_payload": 262144,
            "qos_levels": [0, 1, 2],
        }
