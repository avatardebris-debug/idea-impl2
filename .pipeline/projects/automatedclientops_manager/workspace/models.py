"""Client model for AutomatedClientOps Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Client:
    """Represents a client in the AutomatedClientOps system.

    Attributes:
        client_id: Unique identifier for the client.
        name: Human-readable client name.
        email: Client's email address.
        status: Current engagement status (e.g., 'active', 'pending', 'completed').
        metadata: Free-form dict for additional client data.
    """

    client_id: str
    name: str
    email: str
    status: str = "pending"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.client_id:
            raise ValueError("client_id must be non-empty")
        if not self.email:
            raise ValueError("email must be non-empty")

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "client_id": self.client_id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Client":
        """Deserialize from a dictionary."""
        return cls(
            client_id=data["client_id"],
            name=data["name"],
            email=data["email"],
            status=data.get("status", "pending"),
            metadata=data.get("metadata", {}),
        )
