"""Serial transport adapter for pairenv.

Provides UART communication with Arduino and other serial devices
using pyserial.
"""

import asyncio
import logging
from typing import Optional

import serial  # pyserial

from pairenv.abstraction import DeviceABC

logger = logging.getLogger(__name__)


class SerialTransport(DeviceABC):
    """Serial (UART) transport adapter using pyserial.

    Wraps a serial port connection and implements the DeviceABC protocol.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = serial.EIGHTBITS,
        parity: str = "N",
        stopbits: int = serial.STOPBITS_ONE,
        timeout: float = 1.0,
    ):
        """Initialize the serial transport.

        Args:
            port: Serial port path (e.g. '/dev/ttyUSB0', 'COM3').
            baudrate: Baud rate for the serial connection.
            bytesize: Number of data bits.
            parity: Parity setting ('N', 'E', 'O', 'M', 'S').
            stopbits: Number of stop bits.
            timeout: Default read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._connected = False

    # -- DeviceABC implementation -------------------------------------------

    async def connect(self) -> bool:
        """Open the serial port.

        Returns:
            True if the port was opened successfully.
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
            )
            self._connected = True
            logger.info("Connected to %s at %d baud", self.port, self.baudrate)
            return True
        except (serial.SerialException, OSError) as exc:
            logger.error("Failed to connect to %s: %s", self.port, exc)
            return False

    async def disconnect(self) -> bool:
        """Close the serial port.

        Returns:
            True if the port was closed successfully.
        """
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._connected = False
            logger.info("Disconnected from %s", self.port)
            return True
        return False

    async def send(self, data: bytes) -> int:
        """Send bytes to the device.

        Args:
            data: Byte string to send.

        Returns:
            Number of bytes actually written.
        """
        if not self._connected or not self._serial or not self._serial.is_open:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._serial.write(data)

    async def receive(self, timeout: float = 5.0) -> Optional[bytes]:
        """Read a response from the device.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            Response bytes, or None on timeout.
        """
        if not self._connected or not self._serial or not self._serial.is_open:
            raise RuntimeError("Not connected. Call connect() first.")
        self._serial.timeout = timeout
        line = self._serial.readline()
        if line:
            return line.rstrip(b"\r\n")
        return None

    # -- Convenience --------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Whether the serial port is currently open."""
        return self._connected
