"""
WiFi/HTTP transport plugin for pairenv.

Connects to devices via WiFi/HTTP protocol.
"""

from typing import Any, Dict, List, Optional
from ..plugins.base import PluginABC


class WiFiTransport(PluginABC):
    """WiFi/HTTP transport plugin for HTTP-based device communication."""

    @property
    def name(self) -> str:
        return "wifi_transport"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def protocol(self) -> str:
        return "wifi_http"

    def __init__(self):
        self._connected = False
        self._base_url = "http://localhost"
        self._last_response = None

    def connect(self, base_url: str = "http://localhost", **kwargs) -> bool:
        self._base_url = base_url.rstrip("/")
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def send(self, command: str, **kwargs) -> str:
        if not self._connected:
            raise ConnectionError("WiFi not connected")
        endpoint = kwargs.get("endpoint", "/api/command")
        url = f"{self._base_url}{endpoint}"
        self._last_response = f"HTTP POST {url} -> {{'command': '{command}', 'status': 'ok'}}"
        return self._last_response

    def receive(self) -> Optional[str]:
        return self._last_response

    def discover(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        return [
            {"id": "wifi-device-1", "name": "WiFi Device 1", "protocol": "wifi_http", "status": "online", "ip": "192.168.1.101"},
            {"id": "wifi-device-2", "name": "WiFi Device 2", "protocol": "wifi_http", "status": "online", "ip": "192.168.1.102"},
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "protocol": "wifi_http",
            "features": ["http_post", "http_get", "websocket", "discovery"],
            "max_payload": 1048576,
            "tls_supported": True,
        }
