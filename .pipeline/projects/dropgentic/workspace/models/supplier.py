"""Supplier model for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Supplier:
    """Represents a supplier in the DropGentic system.

    Attributes:
        supplier_id: Unique identifier for the supplier.
        name: Supplier name.
        rating: Supplier rating (0-5).
        active: Whether the supplier is active.
        shipping_cost_per_unit: Shipping cost per unit.
        shipping_weight_factor: Additional shipping cost per kg.
        lead_time_days: Supplier lead time in days.
        min_order_quantity: Minimum order quantity.
        max_order_quantity: Maximum order quantity.
        categories: Supplier categories.
        raw: Extra unmapped fields.
    """
    supplier_id: str
    name: str
    rating: float = 0.0
    active: bool = True
    shipping_cost_per_unit: float = 0.0
    shipping_weight_factor: float = 0.0
    lead_time_days: int = 0
    min_order_quantity: int = 0
    max_order_quantity: int = 0
    categories: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate supplier fields."""
        if not self.supplier_id or not self.supplier_id.strip():
            raise ValueError("supplier_id must be non-empty")
        if not self.name or not self.name.strip():
            raise ValueError("name must be non-empty")
        if not isinstance(self.rating, (int, float)):
            raise ValueError("rating must be a number")
        if self.rating < 0 or self.rating > 5:
            raise ValueError("rating must be between 0 and 5")
        if not isinstance(self.shipping_cost_per_unit, (int, float)):
            raise ValueError("shipping_cost_per_unit must be a number")
        if self.shipping_cost_per_unit < 0:
            raise ValueError("shipping_cost_per_unit must be non-negative")
        if not isinstance(self.shipping_weight_factor, (int, float)):
            raise ValueError("shipping_weight_factor must be a number")
        if self.shipping_weight_factor < 0:
            raise ValueError("shipping_weight_factor must be non-negative")
        if not isinstance(self.lead_time_days, int):
            raise ValueError("lead_time_days must be an integer")
        if self.lead_time_days < 0:
            raise ValueError("lead_time_days must be non-negative")

    def to_dict(self) -> dict:
        """Convert supplier to dictionary.

        Returns:
            Dictionary representation of the supplier.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Supplier:
        """Create a Supplier from a dictionary.

        Args:
            data: Dictionary with supplier fields.

        Returns:
            Supplier instance.
        """
        # Extract known fields
        known_fields = {
            "supplier_id", "name", "rating", "active",
            "shipping_cost_per_unit", "shipping_weight_factor",
            "lead_time_days", "min_order_quantity", "max_order_quantity",
            "categories",
        }
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        # Set defaults for missing fields
        if "rating" not in kwargs:
            kwargs["rating"] = 0.0
        if "active" not in kwargs:
            kwargs["active"] = True
        if "shipping_cost_per_unit" not in kwargs:
            kwargs["shipping_cost_per_unit"] = 0.0
        if "shipping_weight_factor" not in kwargs:
            kwargs["shipping_weight_factor"] = 0.0
        if "lead_time_days" not in kwargs:
            kwargs["lead_time_days"] = 0
        if "min_order_quantity" not in kwargs:
            kwargs["min_order_quantity"] = 0
        if "max_order_quantity" not in kwargs:
            kwargs["max_order_quantity"] = 0
        if "categories" not in kwargs:
            kwargs["categories"] = []
        # Pass raw data for unmapped fields
        kwargs["raw"] = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**kwargs)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Supplier(supplier_id={self.supplier_id!r}, name={self.name!r}, "
            f"rating={self.rating})"
        )
