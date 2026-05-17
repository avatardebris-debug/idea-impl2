"""Rule-based English parser for pairenv.

Converts natural language commands into structured command dictionaries
using regex/template matching.
"""

import re
from typing import Any, Dict, List, Optional


class EnglishParser:
    """Rule-based parser that maps English phrases to structured commands.

    Supported command templates (≥6):
        1. "turn on the LED"          → {"action": "set_pin", "pin": 13, "state": "HIGH"}
        2. "turn off the LED"         → {"action": "set_pin", "pin": 13, "state": "LOW"}
        3. "set pin X to HIGH"        → {"action": "set_pin", "pin": X, "state": "HIGH"}
        4. "set pin X to LOW"         → {"action": "set_pin", "pin": X, "state": "LOW"}
        5. "read sensor on pin X"     → {"action": "read_pin", "pin": X}
        6. "blink LED N times"        → {"action": "blink", "pin": 13, "count": N}
        7. "read temperature on pin X" → {"action": "read_sensor", "pin": X, "sensor": "temperature"}
        8. "read humidity on pin X"   → {"action": "read_sensor", "pin": X, "sensor": "humidity"}
    """

    # Default pin for LED commands when not specified
    DEFAULT_LED_PIN = 13

    # Compiled regex patterns
    PATTERNS: List[tuple] = [
        # "turn on the LED" / "turn on LED" / "turn on the light"
        (
            re.compile(r"turn\s+on\s+(?:the\s+)?(?:LED|light)", re.IGNORECASE),
            lambda m: {
                "action": "set_pin",
                "pin": EnglishParser.DEFAULT_LED_PIN,
                "state": "HIGH",
            },
        ),
        # "turn off the LED" / "turn off LED" / "turn off the light"
        (
            re.compile(r"turn\s+off\s+(?:the\s+)?(?:LED|light)", re.IGNORECASE),
            lambda m: {
                "action": "set_pin",
                "pin": EnglishParser.DEFAULT_LED_PIN,
                "state": "LOW",
            },
        ),
        # "set pin X to HIGH" / "set pin X to LOW"
        (
            re.compile(
                r"set\s+pin\s+(\d+)\s+to\s+(HIGH|LOW)", re.IGNORECASE
            ),
            lambda m: {
                "action": "set_pin",
                "pin": int(m.group(1)),
                "state": m.group(2).upper(),
            },
        ),
        # "set pin X to Y" (generic)
        (
            re.compile(
                r"set\s+pin\s+(\d+)\s+to\s+(\S+)", re.IGNORECASE
            ),
            lambda m: {
                "action": "set_pin",
                "pin": int(m.group(1)),
                "state": m.group(2).upper(),
            },
        ),
        # "read sensor on pin X" / "read sensor on pin A0"
        (
            re.compile(
                r"read\s+(?:sensor|temperature|humidity|light)\s+(?:on\s+)?pin\s+(\S+)",
                re.IGNORECASE,
            ),
            lambda m: {
                "action": "read_sensor",
                "pin": m.group(1),
            },
        ),
        # "read pin X"
        (
            re.compile(r"read\s+pin\s+(\S+)", re.IGNORECASE),
            lambda m: {
                "action": "read_pin",
                "pin": m.group(1),
            },
        ),
        # "blink LED N times" / "blink the LED N times"
        (
            re.compile(
                r"blink\s+(?:the\s+)?LED\s+(\d+)\s+times?", re.IGNORECASE
            ),
            lambda m: {
                "action": "blink",
                "pin": EnglishParser.DEFAULT_LED_PIN,
                "count": int(m.group(1)),
            },
        ),
        # "blink pin X N times"
        (
            re.compile(
                r"blink\s+pin\s+(\d+)\s+(\d+)\s+times?", re.IGNORECASE
            ),
            lambda m: {
                "action": "blink",
                "pin": int(m.group(1)),
                "count": int(m.group(2)),
            },
        ),
    ]

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a natural language command into a structured dict.

        Args:
            text: The English command string.

        Returns:
            A structured command dict, or None if no template matched.
        """
        text = text.strip()
        for pattern, handler in self.PATTERNS:
            match = pattern.search(text)
            if match:
                return handler(match)
        return None

    def list_templates(self) -> List[str]:
        """Return human-readable descriptions of all supported templates."""
        return [
            "turn on the LED",
            "turn off the LED",
            "set pin <X> to HIGH",
            "set pin <X> to LOW",
            "read sensor on pin <X>",
            "read pin <X>",
            "blink LED <N> times",
            "blink pin <X> <N> times",
        ]
