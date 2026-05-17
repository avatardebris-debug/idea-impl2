"""Supplier model for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Supplier:
    """Represents a dropshipping supplier.

    Attributes:
        supplier_id: Unique identifier for the supplier.
        name: Supplier name.
        base_url: Base URL of the supplier's platform.
        rating: Supplier rating (0.0 to 5.0).
        shipping_cost_per_unit: Base shipping cost per unit.
        shipping_weight_factor: Additional shipping cost per kg.
        min_order_quantity: Minimum order quantity.
        max_order_quantity: Maximum order quantity.
        lead_time_days: Estimated delivery time in days.
        supported_currencies: List of supported currencies.
        active: Whether the supplier is currently active.
        categories: List of product categories.
        raw: Extra unmapped fields.
    """
    supplier_id: str
    name: str
    base_url: str = ""
    rating: float = 0.0
    shipping_cost_per_unit: float = 0.0
    shipping_weight_factor: float = 0.0
    min_order_quantity: int = 0
    max_order_quantity: int = 0
    lead_time_days: int = 0
    supported_currencies: list = field(default_factory=list)
    active: bool = True
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
        return cls(**data)

    def __repr__(self) -> str:
        """Return string representation of the supplier."""
        return (
            f"Supplier(supplier_id={self.supplier_id!r}, name={self.name!r}, "
            f"rating={self.rating})"
        )
