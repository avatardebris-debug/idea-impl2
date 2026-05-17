"""Device abstraction interface for pairenv.

Defines the DeviceABC protocol that all transport adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional


class DeviceABC(ABC):
    """Abstract base class for hardware device transport adapters.

    Every transport adapter (Serial, WiFi, BLE, MQTT, etc.) must implement
    these four methods to be compatible with the CommandRouter.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Open a connection to the device.

        Returns:
            True if connection succeeded, False otherwise.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close the connection to the device.

        Returns:
            True if disconnection succeeded, False otherwise.
        """
        ...

    @abstractmethod
    async def send(self, data: bytes) -> int:
        """Send data to the device.

        Args:
            data: Byte string to send.

        Returns:
            Number of bytes sent.
        """
        ...

    @abstractmethod
    async def receive(self, timeout: float = 5.0) -> Optional[bytes]:
        """Read a response from the device.

        Args:
            timeout: Maximum seconds to wait for a response.

        Returns:
            Response bytes, or None if timeout occurred.
        """
        ...


# Alias for compatibility with tests that expect 'Abstraction'
Abstraction = DeviceABC
