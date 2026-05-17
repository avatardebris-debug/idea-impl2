"""TasteProfile data model for the Ranker Architecture."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


class TasteProfileValidationError(Exception):
    """Raised when a TasteProfile fails validation."""


@dataclass
class TasteProfile:
    """Represents a user's accumulated taste profile.

    Attributes:
        user_id: Identifier for the user.
        taste_vector: Mapping of item_id to aggregated preference weight.
        domain_taste_vectors: Mapping of domain_name to per-domain taste vectors.
        metadata: Optional arbitrary metadata dict (e.g., tags, categories).
        created_at: When the profile was first created.
        updated_at: When the profile was last updated.
        id: Unique identifier for this profile.
    """

    user_id: str
    taste_vector: Dict[str, float] = field(default_factory=dict)
    domain_taste_vectors: Dict[str, Dict[str, float]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate profile fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all fields. Raises TasteProfileValidationError on failure."""
        errors: list[str] = []

        if not self.user_id or not str(self.user_id).strip():
            errors.append("user_id is required and must be non-empty")

        if not isinstance(self.taste_vector, dict):
            errors.append("taste_vector must be a dict")
        else:
            for key, val in self.taste_vector.items():
                if not isinstance(key, str) or not key.strip():
                    errors.append(f"taste_vector key must be a non-empty string, got '{key}'")
                if not isinstance(val, (int, float)):
                    errors.append(f"taste_vector value for key '{key}' must be numeric, got {type(val).__name__}")

        if not isinstance(self.domain_taste_vectors, dict):
            errors.append("domain_taste_vectors must be a dict")
        else:
            for domain_name, vector in self.domain_taste_vectors.items():
                if not isinstance(domain_name, str) or not domain_name.strip():
                    errors.append(f"domain_taste_vectors key must be a non-empty string, got '{domain_name}'")
                if not isinstance(vector, dict):
                    errors.append(f"domain_taste_vectors value for domain '{domain_name}' must be a dict")
                else:
                    for item_id, weight in vector.items():
                        if not isinstance(item_id, str) or not item_id.strip():
                            errors.append(f"domain_taste_vectors item_id must be a non-empty string, got '{item_id}'")
                        if not isinstance(weight, (int, float)):
                            errors.append(f"domain_taste_vectors weight for item '{item_id}' must be numeric")

        if not isinstance(self.metadata, dict):
            errors.append("metadata must be a dict")

        if errors:
            raise TasteProfileValidationError("; ".join(errors))

    def update_taste_vector(self, item_id: str, weight: float) -> None:
        """Update or add an item's weight in the taste vector.

        Args:
            item_id: The item to update.
            weight: The new weight value.

        Raises:
            TasteProfileValidationError: If weight is invalid.
        """
        if weight < 0.0:
            raise TasteProfileValidationError(f"taste_vector weight must be non-negative, got {weight}")
        self.taste_vector[item_id] = weight
        self.updated_at = datetime.now(timezone.utc)

    def update_domain_taste_vector(self, domain_name: str, item_id: str, weight: float) -> None:
        """Update or add an item's weight in a specific domain's taste vector.

        Args:
            domain_name: The domain to update.
            item_id: The item to update.
            weight: The new weight value.

        Raises:
            TasteProfileValidationError: If domain_name or weight is invalid.
        """
        if not isinstance(domain_name, str) or not domain_name.strip():
            raise TasteProfileValidationError("domain_name must be a non-empty string")
        if weight < 0.0:
            raise TasteProfileValidationError(f"domain taste_vector weight must be non-negative, got {weight}")
        if domain_name not in self.domain_taste_vectors:
            self.domain_taste_vectors[domain_name] = {}
        self.domain_taste_vectors[domain_name][item_id] = weight
        self.updated_at = datetime.now(timezone.utc)

    def get_domain_taste_vector(self, domain_name: str) -> Dict[str, float]:
        """Get the taste vector for a specific domain.

        Args:
            domain_name: The domain to get the taste vector for.

        Returns:
            A copy of the domain's taste vector, or empty dict if domain doesn't exist.
        """
        return dict(self.domain_taste_vectors.get(domain_name, {}))

    def get_domain_taste_values(self, domain_name: str) -> List[float]:
        """Get all taste values for a specific domain.

        Args:
            domain_name: The domain to get taste values for.

        Returns:
            A list of taste values for the domain.
        """
        return list(self.domain_taste_vectors.get(domain_name, {}).values())

    def get_domain_item_taste(self, domain_name: str, item_id: str) -> float:
        """Get the taste value for a specific item in a specific domain.

        Args:
            domain_name: The domain to query.
            item_id: The item to query.

        Returns:
            The taste value, or 0.0 if not found.
        """
        return self.domain_taste_vectors.get(domain_name, {}).get(item_id, 0.0)

    def get_all_domains(self) -> List[str]:
        """Get all domains that have taste vectors.

        Returns:
            A list of domain names.
        """
        return list(self.domain_taste_vectors.keys())

    def merge(self, other: TasteProfile) -> None:
        """Merge another profile's taste vector into this one.

        For overlapping keys, the other profile's values take precedence.

        Args:
            other: The profile to merge from.
        """
        for item_id, weight in other.taste_vector.items():
            self.taste_vector[item_id] = weight
        for domain_name, domain_vector in other.domain_taste_vectors.items():
            if domain_name not in self.domain_taste_vectors:
                self.domain_taste_vectors[domain_name] = {}
            for item_id, weight in domain_vector.items():
                self.domain_taste_vectors[domain_name][item_id] = weight
        self.metadata.update(other.metadata)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert profile to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "taste_vector": self.taste_vector,
            "domain_taste_vectors": self.domain_taste_vectors,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> TasteProfile:
        """Create a TasteProfile from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        return cls(
            user_id=data["user_id"],
            taste_vector=data.get("taste_vector", {}),
            domain_taste_vectors=data.get("domain_taste_vectors", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            id=data.get("id", str(uuid.uuid4())),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TasteProfile):
            return NotImplemented
        return (
            self.user_id == other.user_id
            and self.taste_vector == other.taste_vector
            and self.domain_taste_vectors == other.domain_taste_vectors
            and self.metadata == other.metadata
        )

    def __hash__(self) -> int:
        return hash((
            self.user_id,
            frozenset(self.taste_vector.items()),
            frozenset((k, frozenset(v.items())) for k, v in self.domain_taste_vectors.items()),
            frozenset(self.metadata.items()),
        ))
