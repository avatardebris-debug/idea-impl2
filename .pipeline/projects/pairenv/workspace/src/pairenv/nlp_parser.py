"""
Enhanced NLP parser for pairenv.

Provides intent classification, entity extraction, and multi-language support
for natural language command parsing.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Command intents recognized by the NLP parser."""
    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    BLINK = "blink"
    READ_SENSOR = "read_sensor"
    READ_TEMP = "read_temp"
    READ_HUMIDITY = "read_humidity"
    READ_PIN = "read_pin"
    SET_PIN = "set_pin"
    LIST_DEVICES = "list_devices"
    SET_VALUE = "set_value"
    GET_STATUS = "get_status"
    UNKNOWN = "unknown"


class Entity:
    """Represents an extracted entity from a command."""

    def __init__(self, entity_type: str, value: str, confidence: float = 1.0):
        self.entity_type = entity_type
        self.value = value
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.entity_type,
            "value": self.value,
            "confidence": self.confidence,
        }


class ParsedCommand:
    """Result of parsing a natural language command."""

    def __init__(self, intent: Intent, entities: List[Entity], raw_text: str, confidence: float = 1.0):
        self.intent = intent
        self.entities = entities
        self.raw_text = raw_text
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "entities": [e.to_dict() for e in self.entities],
            "raw_text": self.raw_text,
            "confidence": self.confidence,
        }

    def __repr__(self) -> str:
        return f"ParsedCommand(intent={self.intent.value}, entities={self.entities}, confidence={self.confidence})"


class EnhancedNLPParser:
    """
    Enhanced NLP parser with intent classification and entity extraction.

    Supports:
        - Intent classification via keyword matching
        - Entity extraction (device names, values, pins, etc.)
        - Multi-language support (English, Spanish, French)
        - Confidence scoring
        - Fallback to default commands
    """

    # Intent patterns
    INTENT_PATTERNS = {
        Intent.TURN_ON: [
            r"turn\s+on", r"switch\s+on", r"power\s+on", r"enable", r"activate",
            r"enciende", r"activa", r"allume", r"active",
        ],
        Intent.TURN_OFF: [
            r"turn\s+off", r"switch\s+off", r"power\s+off", r"disable", r"deactivate",
            r"apaga", r"desactiva", r"éteins", r"désactive",
        ],
        Intent.BLINK: [
            r"blink", r"flash", r"parpadea", r"clignote",
        ],
        Intent.READ_SENSOR: [
            r"read\s+sensor", r"get\s+sensor", r"read\s+value", r"get\s+value",
            r"lee\s+sensor", r"obten\s+sensor", r"lis\s+capteur",
        ],
        Intent.READ_TEMP: [
            r"read\s+temp", r"get\s+temp", r"temperature", r"lee\s+temp",
            r"obten\s+temp", r"lis\s+température",
        ],
        Intent.READ_HUMIDITY: [
            r"read\s+humidity", r"get\s+humidity", r"humidity", r"lee\s+humedad",
            r"obten\s+humedad", r"lis\s+humidité",
        ],
        Intent.READ_PIN: [
            r"read\s+pin", r"get\s+pin", r"pin\s+state", r"lee\s+pin",
            r"obten\s+pin", r"lis\s+pin",
        ],
        Intent.SET_PIN: [
            r"set\s+pin", r"pin\s+to", r"pin\s+high", r"pin\s+low",
            r"configura\s+pin", r"pin\s+alto", r"pin\s+bajo",
            r"configure\s+pin", r"pin\s+haut", r"pin\s+bas",
        ],
        Intent.LIST_DEVICES: [
            r"list\s+devices", r"show\s+devices", r"what\s+devices",
            r"lista\s+dispositivos", r"muestra\s+dispositivos",
            r"liste\s+appareils", r"montre\s+appareils",
        ],
        Intent.SET_VALUE: [
            r"set\s+value", r"set\s+to", r"change\s+to", r"configure\s+value",
            r"configura\s+valor", r"cambia\s+a",
            r"configure\s+valeur", r"change\s+à",
        ],
        Intent.GET_STATUS: [
            r"status", r"state", r"how\s+is", r"check\s+status",
            r"estado", r"estado\s+de", r"état", r"état\s+de",
        ],
    }

    # Entity patterns
    ENTITY_PATTERNS = {
        "device": r"(?:device|light|sensor|temp|humidity|pin|led|relay)\s*(?:name\s*)?['\"]?(\w+)['\"]?",
        "value": r"(?:value|to|set|at)\s*(?:['\"]?)(\d+\.?\d*)['\"]?",
        "pin": r"pin\s*(?:number\s*)?['\"]?(\d+)['\"]?",
        "state": r"(?:high|low|on|off|true|false|1|0)",
        "duration": r"(\d+\.?\d*)\s*(?:seconds?|s|ms)",
    }

    # Language mappings
    LANGUAGE_MAP = {
        "en": {
            "turn_on": Intent.TURN_ON,
            "turn_off": Intent.TURN_OFF,
            "blink": Intent.BLINK,
            "read_sensor": Intent.READ_SENSOR,
            "read_temp": Intent.READ_TEMP,
            "read_humidity": Intent.READ_HUMIDITY,
            "read_pin": Intent.READ_PIN,
            "set_pin": Intent.SET_PIN,
            "list_devices": Intent.LIST_DEVICES,
            "set_value": Intent.SET_VALUE,
            "get_status": Intent.GET_STATUS,
        },
        "es": {
            "enciende": Intent.TURN_ON,
            "apaga": Intent.TURN_OFF,
            "parpadea": Intent.BLINK,
            "lee_sensor": Intent.READ_SENSOR,
            "lee_temp": Intent.READ_TEMP,
            "lee_humedad": Intent.READ_HUMIDITY,
            "lee_pin": Intent.READ_PIN,
            "configura_pin": Intent.SET_PIN,
            "lista_dispositivos": Intent.LIST_DEVICES,
            "configura_valor": Intent.SET_VALUE,
            "estado": Intent.GET_STATUS,
        },
        "fr": {
            "allume": Intent.TURN_ON,
            "éteins": Intent.TURN_OFF,
            "clignote": Intent.BLINK,
            "lis_capteur": Intent.READ_SENSOR,
            "lis_température": Intent.READ_TEMP,
            "lis_humidité": Intent.READ_HUMIDITY,
            "lis_pin": Intent.READ_PIN,
            "configure_pin": Intent.SET_PIN,
            "liste_appareils": Intent.LIST_DEVICES,
            "configure_valeur": Intent.SET_VALUE,
            "état": Intent.GET_STATUS,
        },
    }

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self._device_cache: Dict[str, str] = {}

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        text_lower = text.lower()
        for lang, mappings in self.LANGUAGE_MAP.items():
            for keyword in mappings.keys():
                if keyword in text_lower:
                    return lang
        return self.default_language

    def classify_intent(self, text: str, language: Optional[str] = None) -> Tuple[Intent, float]:
        """Classify the intent of the input text."""
        lang = language or self.detect_language(text)
        text_lower = text.lower()

        # Check language-specific mappings first
        if lang in self.LANGUAGE_MAP:
            for keyword, intent in self.LANGUAGE_MAP[lang].items():
                if keyword in text_lower:
                    return intent, 0.9

        # Fall back to pattern matching
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent, 0.85

        return Intent.UNKNOWN, 0.0

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from the input text."""
        entities = []
        text_lower = text.lower()

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1)
                entities.append(Entity(entity_type, value, 0.9))

        return entities

    def parse(self, text: str, language: Optional[str] = None) -> ParsedCommand:
        """Parse a natural language command."""
        lang = language or self.detect_language(text)
        intent, confidence = self.classify_intent(text, lang)
        entities = self.extract_entities(text)

        return ParsedCommand(intent, entities, text, confidence)

    def get_command_from_parsed(self, parsed: ParsedCommand) -> Dict[str, Any]:
        """Convert a parsed command to a structured command dict."""
        command = {
            "intent": parsed.intent.value,
            "entities": {e.entity_type: e.value for e in parsed.entities},
        }

        # Map intent to specific command structure
        if parsed.intent == Intent.TURN_ON:
            command["action"] = "turn_on"
        elif parsed.intent == Intent.TURN_OFF:
            command["action"] = "turn_off"
        elif parsed.intent == Intent.BLINK:
            command["action"] = "blink"
        elif parsed.intent == Intent.READ_SENSOR:
            command["action"] = "read_sensor"
        elif parsed.intent == Intent.READ_TEMP:
            command["action"] = "read_temp"
        elif parsed.intent == Intent.READ_HUMIDITY:
            command["action"] = "read_humidity"
        elif parsed.intent == Intent.READ_PIN:
            command["action"] = "read_pin"
        elif parsed.intent == Intent.SET_PIN:
            command["action"] = "set_pin"
        elif parsed.intent == Intent.LIST_DEVICES:
            command["action"] = "list_devices"
        elif parsed.intent == Intent.SET_VALUE:
            command["action"] = "set_value"
        elif parsed.intent == Intent.GET_STATUS:
            command["action"] = "get_status"
        else:
            command["action"] = "unknown"

        return command

    def parse_and_command(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Parse text and return a structured command."""
        parsed = self.parse(text, language)
        return self.get_command_from_parsed(parsed)

    def add_device_alias(self, device_id: str, alias: str) -> None:
        """Add an alias for a device."""
        self._device_cache[alias.lower()] = device_id

    def resolve_device(self, device_name: str) -> Optional[str]:
        """Resolve a device name to a device ID using aliases."""
        return self._device_cache.get(device_name.lower())

    def get_supported_intents(self) -> List[str]:
        """Get list of supported intents."""
        return [intent.value for intent in Intent if intent != Intent.UNKNOWN]

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.LANGUAGE_MAP.keys())
