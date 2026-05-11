"""Message bus for agent communication."""


class Message:
    """Represents a message between agents."""

    def __init__(self, from_agent: str, to_agent: str, msg_type: str, payload: dict):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.type = msg_type
        self.payload = payload

    @staticmethod
    def create(from_agent: str, to_agent: str, type: str, payload: dict, **kwargs) -> "Message":
        """Factory method to create a Message."""
        return Message(from_agent=from_agent, to_agent=to_agent, msg_type=type, payload=payload)

    def __repr__(self):
        return f"Message(from={self.from_agent}, to={self.to_agent}, type={self.type})"


class MessageBus:
    """Simple in-memory message bus."""

    def __init__(self):
        self.sent = []

    def send(self, message: Message):
        """Send a message."""
        self.sent.append(message)

    def send_to(self, to_agent: str, msg_type: str, payload: dict, from_agent: str = "system") -> Message:
        """Convenience method to send a message."""
        msg = Message.create(from_agent=from_agent, to_agent=to_agent, type=msg_type, payload=payload)
        self.send(msg)
        return msg
