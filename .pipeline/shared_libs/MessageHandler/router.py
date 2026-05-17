"""Command router and bidirectional message handler for pairenv.

CommandRouter routes structured command dicts to paired devices via
the appropriate transport adapter. MessageHandler converts device
responses back into natural language.
"""

import logging
from typing import Any, Dict, Optional

from pairenv.registry import DeviceRegistry
from pairenv.transports.serial_transport import SerialTransport

logger = logging.getLogger(__name__)


class CommandRouter:
    """Routes structured commands to paired devices.

    Looks up a device in the registry, creates the appropriate transport
    adapter, translates the command into transport-specific bytes, sends
    it, and returns the response.
    """

    def __init__(self, registry: Optional[DeviceRegistry] = None):
        """Initialize the router.

        Args:
            registry: DeviceRegistry instance. Creates a default one if None.
        """
        self.registry = registry or DeviceRegistry()

    def _build_transport(self, device: Dict[str, Any]) -> SerialTransport:
        """Create a SerialTransport from a device registry entry."""
        cfg = device["transport_config"]
        return SerialTransport(
            port=cfg.get("port", "/dev/ttyUSB0"),
            baudrate=cfg.get("baudrate", 9600),
        )

    def _command_to_bytes(self, cmd: Dict[str, Any]) -> bytes:
        """Translate a structured command dict into transport-specific bytes.

        Supported actions:
            - set_pin:  "SET <pin> <state>\n"
            - read_pin: "READ <pin>\n"
            - read_sensor: "READ_SENSOR <pin>\n"
            - blink:    "BLINK <pin> <count>\n"
        """
        action = cmd.get("action", "")
        if action == "set_pin":
            pin = cmd.get("pin", 13)
            state = cmd.get("state", "HIGH")
            return f"SET {pin} {state}\n".encode()
        elif action == "read_pin":
            pin = cmd.get("pin", "A0")
            return f"READ {pin}\n".encode()
        elif action == "read_sensor":
            pin = cmd.get("pin", "A0")
            return f"READ_SENSOR {pin}\n".encode()
        elif action == "blink":
            pin = cmd.get("pin", 13)
            count = cmd.get("count", 3)
            return f"BLINK {pin} {count}\n".encode()
        else:
            raise ValueError(f"Unknown action: {action}")

    async def route(
        self, device_id: str, command: Dict[str, Any]
    ) -> Optional[str]:
        """Route a command to a device and return the response.

        Args:
            device_id: ID of the paired device.
            command: Structured command dict from the parser.

        Returns:
            Response string from the device, or None on failure.
        """
        device = self.registry.get(device_id)
        if not device:
            logger.error("Device '%s' not found in registry", device_id)
            return None

        transport = self._build_transport(device)
        success = await transport.connect()
        if not success:
            logger.error("Failed to connect to device '%s'", device_id)
            return None

        try:
            payload = self._command_to_bytes(command)
            await transport.send(payload)
            response = await transport.receive(timeout=5.0)
            if response:
                return response.decode(errors="replace").strip()
            return None
        finally:
            await transport.disconnect()


class MessageHandler:
    """Converts device responses into natural language for the user.

    Handles common response formats like "PIN13=HIGH", "SENSOR=A0:256",
    "BLINK_OK", etc.
    """

    # Response patterns: (regex, template)
    RESPONSE_PATTERNS = [
        # "PIN13=HIGH" / "PIN13=LOW"
        (
            r"PIN(\d+)=([A-Z]+)",
            lambda m: f"The LED on pin {m.group(1)} is now {'ON' if m.group(2) == 'HIGH' else 'OFF'}",
        ),
        # "SENSOR=A0:256"
        (
            r"SENSOR=([A-Z]\d+):(\d+)",
            lambda m: f"Sensor on pin {m.group(1)} reads {m.group(2)}",
        ),
        # "READ_PIN=A0:1023"
        (
            r"READ_PIN=([A-Z]\d+):(\d+)",
            lambda m: f"Pin {m.group(1)} value: {m.group(2)}",
        ),
        # "BLINK_OK" / "BLINK_DONE"
        (
            r"BLINK_(OK|DONE)",
            lambda m: f"LED blinking completed ({m.group(1).lower()})",
        ),
        # "SET_OK" / "SET_DONE"
        (
            r"SET_(OK|DONE)",
            lambda m: f"Command executed successfully ({m.group(1).lower()})",
        ),
        # Generic fallback: "PIN13=HIGH" style
        (
            r"([A-Z_]+)=([A-Z0-9:]+)",
            lambda m: f"Device reports {m.group(1)}={m.group(2)}",
        ),
    ]

    @classmethod
    def format_response(cls, raw_response: str) -> str:
        """Convert a raw device response to natural language.

        Args:
            raw_response: Raw string from the device.

        Returns:
            Human-readable response string.
        """
        if not raw_response:
            return "No response from device."
        for pattern, formatter in cls.RESPONSE_PATTERNS:
            import re
            match = re.search(pattern, raw_response)
            if match:
                return formatter(match)
        return f"Device response: {raw_response}"
