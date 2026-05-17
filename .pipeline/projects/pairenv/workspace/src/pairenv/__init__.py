"""
paienv - Python IoT Device Management Framework

A modular framework for managing IoT devices across multiple transport protocols
with natural language command parsing, multi-device coordination, and a web dashboard.

Main components:
    - plugins: Plugin system for transport protocols (MQTT, WiFi, BLE, Serial, Simulation)
    - coordinator: Multi-device coordination and command routing
    - nlp_parser: Natural language command parsing
    - dashboard: Web-based monitoring and control UI
"""

from .plugins import PluginABC, PluginState, PluginRegistry, PluginLoader
from .plugins.base import PluginABC, PluginState
from .plugins.registry import PluginRegistry
from .plugins.loader import PluginLoader
from .transports import (
    SerialTransport,
    MQTTTransport,
    WiFiTransport,
    BLETransport,
    SimulationTransport,
)
from .coordinator import MultiDeviceCoordinator
from .nlp_parser import EnhancedNLPParser
from .dashboard import WebDashboard

__version__ = "0.1.0"
__all__ = [
    # Plugins
    "PluginABC",
    "PluginState",
    "PluginRegistry",
    "PluginLoader",
    # Transports
    "SerialTransport",
    "MQTTTransport",
    "WiFiTransport",
    "BLETransport",
    "SimulationTransport",
    # Coordinator
    "MultiDeviceCoordinator",
    # NLP
    "EnhancedNLPParser",
    # Dashboard
    "WebDashboard",
    # Version
    "__version__",
]
