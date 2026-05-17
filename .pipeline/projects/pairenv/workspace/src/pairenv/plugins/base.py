"""
Plugin abstract base class for the pairenv plugin architecture.

All transport plugins must subclass PluginABC and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class PluginState(Enum):
    """Lifecycle states for a plugin."""
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginABC(ABC):
    """
    Abstract base class for all plugin implementations.

    A new transport plugin can be written in < 100 lines by subclassing this
    and implementing the abstract methods below.

    Required methods:
        - connect(): Establish connection to the device/protocol
        - disconnect(): Close the connection
        - send(command: str, **kwargs) -> str: Send a command and get response
        - receive() -> Optional[str]: Receive pending data
        - discover() -> List[Dict]: Discover available devices
        - get_capabilities() -> Dict: Return plugin capabilities
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""
        pass

    @property
    @abstractmethod
    def protocol(self) -> str:
        """Return the protocol this plugin supports."""
        pass

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Establish connection. Returns True on success."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection. Returns True on success."""
        pass

    @abstractmethod
    def send(self, command: str, **kwargs) -> str:
        """Send a command to the device. Returns response string."""
        pass

    @abstractmethod
    def receive(self) -> Optional[str]:
        """Receive pending data from the device."""
        pass

    @abstractmethod
    def discover(self) -> List[Dict[str, Any]]:
        """Discover available devices. Returns list of device dicts."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return plugin capabilities dict."""
        pass

    def initialize(self, **kwargs) -> bool:
        """Initialize the plugin with optional config. Override for setup."""
        return self.connect(**kwargs)

    def shutdown(self) -> bool:
        """Shutdown the plugin. Override for cleanup."""
        return self.disconnect()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} version={self.version} protocol={self.protocol}>"
