"""Domain-aware taste modeling for the Ranker Architecture.

Provides domain management, per-domain taste vectors, and cross-domain
weight transfer with configurable transfer ratios.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .profile import TasteProfile, TasteProfileValidationError


class DomainValidationError(Exception):
    """Raised when a Domain fails validation."""


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

@dataclass
class Domain:
    """Represents a taste domain (category) with its own taste vector.

    Attributes:
        name: Human-readable domain name (e.g. "music", "film").
        description: Optional free-text description.
        taste_vector: Per-domain preference weights keyed by item_id.
        parent_domain: Optional name of a parent domain for hierarchy.
        created_at: Creation timestamp.
        id: Unique identifier.
    """

    name: str
    description: str = ""
    taste_vector: Dict[str, float] = field(default_factory=dict)
    parent_domain: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        errors: list[str] = []
        if not self.name or not self.name.strip():
            errors.append("name is required and must be non-empty")
        if not isinstance(self.taste_vector, dict):
            errors.append("taste_vector must be a dict")
        else:
            for key, val in self.taste_vector.items():
                if not isinstance(key, str) or not key.strip():
                    errors.append(f"taste_vector key must be a non-empty string, got '{key}'")
                if not isinstance(val, (int, float)):
                    errors.append(f"taste_vector value for key '{key}' must be numeric, got {type(val).__name__}")
        if errors:
            raise DomainValidationError("; ".join(errors))

    def update_taste_vector(self, item_id: str, value: float) -> None:
        """Update a single item's weight in this domain.

        Args:
            item_id: Item identifier.
            value: Non-negative preference weight.

        Raises:
            DomainValidationError: If value is negative or item_id is invalid.
        """
        if not isinstance(item_id, str) or not item_id.strip():
            raise DomainValidationError("item_id must be a non-empty string")
        if not isinstance(value, (int, float)) or value < 0:
            raise DomainValidationError("value must be a non-negative number")
        self.taste_vector[item_id] = float(value)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "taste_vector": self.taste_vector,
            "parent_domain": self.parent_domain,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Domain:
        """Deserialize from a dictionary."""
        required = ("id", "name")
        for key in required:
            if key not in data or not data[key]:
                raise DomainValidationError(f"Missing or empty required field: {key}")
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            taste_vector=data.get("taste_vector", {}),
            parent_domain=data.get("parent_domain"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            id=data["id"],
        )


# ---------------------------------------------------------------------------
# DomainManager
# ---------------------------------------------------------------------------

@dataclass
class DomainManager:
    """Manages domains and cross-domain weight transfer.

    Attributes:
        domains: Mapping of domain name → Domain.
        transfer_ratios: Mapping of (source_domain, target_domain) → float ratio.
        default_transfer_ratio: Fallback ratio when no specific ratio is defined.
    """

    domains: Dict[str, Domain] = field(default_factory=dict)
    transfer_ratios: Dict[tuple, float] = field(default_factory=dict)
    default_transfer_ratio: float = 0.1

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        for name, domain in self.domains.items():
            if not isinstance(name, str) or not name.strip():
                raise DomainValidationError(f"Domain name must be a non-empty string, got '{name}'")
            if name in self.domains and self.domains[name] is not domain:
                raise DomainValidationError(f"Duplicate domain name: {name}")
        for (src, tgt), ratio in self.transfer_ratios.items():
            if src not in self.domains:
                raise DomainValidationError(f"Transfer ratio source domain '{src}' not registered")
            if tgt not in self.domains:
                raise DomainValidationError(f"Transfer ratio target domain '{tgt}' not registered")
            if not (0.0 <= ratio <= 1.0):
                raise DomainValidationError(f"Transfer ratio must be between 0.0 and 1.0, got {ratio}")

    # -- Domain lifecycle ---------------------------------------------------

    def register_domain(self, domain: Domain) -> None:
        """Register a new domain.

        Raises:
            DomainValidationError: If domain is invalid or name already exists.
        """
        if domain.name in self.domains:
            raise DomainValidationError(f"Domain already registered: {domain.name}")
        self.domains[domain.name] = domain

    def get_domain(self, name: str) -> Domain:
        """Get a domain by name.

        Raises:
            KeyError: If the domain does not exist.
        """
        if name not in self.domains:
            raise KeyError(f"Domain not found: {name}")
        return self.domains[name]

    def list_domains(self) -> List[str]:
        """Return all registered domain names."""
        return list(self.domains.keys())

    def remove_domain(self, name: str) -> None:
        """Remove a domain.

        Raises:
            KeyError: If the domain does not exist.
        """
        if name not in self.domains:
            raise KeyError(f"Domain not found: {name}")
        del self.domains[name]
        # Clean up transfer ratios involving this domain
        keys_to_remove = [k for k in self.transfer_ratios if name in k]
        for k in keys_to_remove:
            del self.transfer_ratios[k]

    # -- Transfer ratios ----------------------------------------------------

    def set_transfer_ratio(self, source_domain: str, target_domain: str, ratio: float) -> None:
        """Set the weight transfer ratio from source to target domain.

        Args:
            source_domain: Source domain name.
            target_domain: Target domain name.
            ratio: Transfer ratio between 0.0 and 1.0.

        Raises:
            DomainValidationError: If domains are not registered or ratio is invalid.
        """
        if source_domain not in self.domains:
            raise DomainValidationError(f"Source domain not registered: {source_domain}")
        if target_domain not in self.domains:
            raise DomainValidationError(f"Target domain not registered: {target_domain}")
        if not (0.0 <= ratio <= 1.0):
            raise DomainValidationError(f"Transfer ratio must be between 0.0 and 1.0, got {ratio}")
        self.transfer_ratios[(source_domain, target_domain)] = ratio

    def get_transfer_ratio(self, source_domain: str, target_domain: str) -> float:
        """Get the transfer ratio between two domains.

        Returns the configured ratio or the default_transfer_ratio if none is set.
        """
        return self.transfer_ratios.get((source_domain, target_domain), self.default_transfer_ratio)

    # -- Cross-domain weight transfer ---------------------------------------

    def transfer_weights(
        self,
        source_domain_name: str,
        target_domain_name: str,
        item_id: str,
        amount: float,
    ) -> float:
        """Transfer weight from one domain to another for a specific item.

        Args:
            source_domain_name: Source domain name.
            target_domain_name: Target domain name.
            item_id: Item identifier.
            amount: Weight to transfer.

        Returns:
            The actual amount transferred (amount * ratio).

        Raises:
            KeyError: If either domain is not registered.
            DomainValidationError: If amount is negative or item_id is invalid.
        """
        if not isinstance(item_id, str) or not item_id.strip():
            raise DomainValidationError("item_id must be a non-empty string")
        if not isinstance(amount, (int, float)) or amount < 0:
            raise DomainValidationError("amount must be a non-negative number")

        source = self.get_domain(source_domain_name)
        target = self.get_domain(target_domain_name)
        ratio = self.get_transfer_ratio(source_domain_name, target_domain_name)
        transferred = amount * ratio

        source.taste_vector[item_id] = source.taste_vector.get(item_id, 0.0) - amount
        target.taste_vector[item_id] = target.taste_vector.get(item_id, 0.0) + transferred

        return transferred

    def transfer_weights_to_profile(
        self,
        source_domain_name: str,
        target_profile: TasteProfile,
    ) -> TasteProfile:
        """Transfer all weights from a source domain to a target TasteProfile.

        Args:
            source_domain_name: Source domain name.
            target_profile: Target taste profile to update.

        Returns:
            The updated target profile.
        """
        source = self.get_domain(source_domain_name)
        for item_id, weight in source.taste_vector.items():
            target_profile.taste_vector[item_id] = target_profile.taste_vector.get(item_id, 0.0) + weight
        return target_profile

    # -- Serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire DomainManager to a dictionary."""
        return {
            "domains": {name: domain.to_dict() for name, domain in self.domains.items()},
            "transfer_ratios": {
                f"{src}||{tgt}": ratio
                for (src, tgt), ratio in self.transfer_ratios.items()
            },
            "default_transfer_ratio": self.default_transfer_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainManager:
        """Deserialize from a dictionary."""
        dm = cls()
        for name, domain_data in data.get("domains", {}).items():
            dm.register_domain(Domain.from_dict(domain_data))
        for key, ratio in data.get("transfer_ratios", {}).items():
            src, tgt = key.split("||")
            dm.transfer_ratios[(src, tgt)] = ratio
        dm.default_transfer_ratio = data.get("default_transfer_ratio", 0.1)
        dm._validate()
        return dm
