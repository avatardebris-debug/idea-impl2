"""VAST.ai instance message bus.

Provides a simple message bus for communication between pipeline components.
"""

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """A message in the pipeline."""

    from_agent: str
    to_agent: str
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__('time').time())

    @classmethod
    def create(
        cls,
        from_agent: str,
        to_agent: str,
        type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "Message":
        """Create a new message.

        Args:
            from_agent: The agent sending the message.
            to_agent: The agent receiving the message.
            type: The type of the message.
            payload: The payload of the message.
            **kwargs: Additional keyword arguments.

        Returns:
            A new Message instance.
        """
        if payload is None:
            payload = {}
        return cls(
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            payload=payload,
            **kwargs,
        )


class MessageBus:
    """A simple message bus for pipeline communication."""

    def __init__(self) -> None:
        self._messages: list[Message] = []
        self._lock = threading.Lock()

    def send(self, message: Message) -> None:
        """Send a message to the bus.

        Args:
            message: The message to send.

        Raises:
            ValueError: If the message is invalid.
        """
        if not message.from_agent or not message.to_agent:
            raise ValueError("Message must have from_agent and to_agent.")
        if not message.type:
            raise ValueError("Message must have a type.")

        with self._lock:
            self._messages.append(message)

    def get_messages(self, to_agent: str | None = None) -> list[Message]:
        """Get messages from the bus.

        Args:
            to_agent: Filter messages by recipient. Defaults to None (all messages).

        Returns:
            A list of messages.
        """
        with self._lock:
            if to_agent:
                return [msg for msg in self._messages if msg.to_agent == to_agent]
            return list(self._messages)

    def clear(self) -> None:
        """Clear all messages from the bus."""
        with self._lock:
            self._messages.clear()
