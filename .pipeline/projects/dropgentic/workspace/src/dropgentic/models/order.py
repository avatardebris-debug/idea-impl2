"""Order model for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Order:
    """Represents a dropshipping order.

    Attributes:
        order_id: Unique identifier for the order.
        product_id: ID of the ordered product.
        supplier_id: ID of the supplier fulfilling the order.
        quantity: Number of units ordered.
        unit_cost: Cost per unit (from supplier).
        total_cost: Total cost per unit.
        shipping_cost: Total shipping cost for the order.
        platform_fee: Platform fee charged.
        payment_fee: Payment processing fee charged.
        status: Order status (pending, processing, shipped, delivered, cancelled).
        retail_price: Retail price per unit.
        raw: Extra unmapped fields.
    """
    order_id: str
    product_id: str
    supplier_id: str
    quantity: int
    unit_cost: float
    total_cost: float
    shipping_cost: float = 0.0
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    status: str = "pending"
    retail_price: float = 0.0
    raw: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate order data after initialization."""
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must be non-empty")
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.supplier_id or not self.supplier_id.strip():
            raise ValueError("supplier_id must be non-empty")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.unit_cost < 0:
            raise ValueError("unit_cost must be non-negative")
        if self.total_cost < 0:
            raise ValueError("total_cost must be non-negative")
        if self.shipping_cost < 0:
            raise ValueError("shipping_cost must be non-negative")
        if self.platform_fee < 0:
            raise ValueError("platform_fee must be non-negative")
        if self.payment_fee < 0:
            raise ValueError("payment_fee must be non-negative")
        if self.retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        valid_statuses = {"pending", "processing", "shipped", "delivered", "cancelled"}
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")

    @property
    def total_fees(self) -> float:
        """Calculate total fees for the order."""
        return self.platform_fee + self.payment_fee

    @property
    def net_profit(self) -> float:
        """Calculate net profit for the order."""
        revenue = self.quantity * self.retail_price
        total_order_cost = (self.total_cost * self.quantity) + self.shipping_cost + self.total_fees
        return revenue - total_order_cost

    @property
    def net_margin_pct(self) -> float:
        """Calculate net margin percentage."""
        if self.retail_price <= 0 or self.quantity <= 0:
            return 0.0
        revenue = self.quantity * self.retail_price
        if revenue <= 0:
            return 0.0
        return self.net_profit / revenue

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Order:
        """Create from dictionary."""
        # Extract known fields and pass the rest as raw
        known_fields = {
            "order_id", "product_id", "supplier_id", "quantity",
            "unit_cost", "total_cost", "shipping_cost", "platform_fee",
            "payment_fee", "status", "retail_price", "raw"
        }
        raw_data = {k: v for k, v in data.items() if k not in known_fields}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        if raw_data:
            filtered_data["raw"] = raw_data
            # Also set extra fields as direct attributes
            for k, v in raw_data.items():
                filtered_data[k] = v
        return cls(**filtered_data)

    def __getattr__(self, name: str) -> object:
        """Allow access to raw fields as attributes."""
        if name.startswith("_"):
            raise AttributeError(name)
        if hasattr(self, "raw") and name in self.raw:
            return self.raw[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Order(id={self.order_id}, product={self.product_id}, "
            f"qty={self.quantity}, status={self.status})"
        )
