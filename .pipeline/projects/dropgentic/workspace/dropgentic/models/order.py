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
        total_fees: Total fees (shipping + platform + payment).
        net_profit: Net profit after all costs and fees.
        net_margin_pct: Net margin as percentage (0-100).
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
    total_fees: float = 0.0
    net_profit: float = 0.0
    net_margin_pct: float = 0.0
    status: str = "pending"
    retail_price: float = 0.0
    raw: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate order fields."""
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must be non-empty")
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.supplier_id or not self.supplier_id.strip():
            raise ValueError("supplier_id must be non-empty")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if not isinstance(self.unit_cost, (int, float)):
            raise ValueError("unit_cost must be a number")
        if self.unit_cost < 0:
            raise ValueError("unit_cost must be non-negative")
        if not isinstance(self.total_cost, (int, float)):
            raise ValueError("total_cost must be a number")
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
    def gross_profit(self) -> float:
        """Calculate gross profit per unit.

        Returns:
            Gross profit per unit.
        """
        return self.retail_price - self.total_cost

    @property
    def gross_margin_pct(self) -> float:
        """Calculate gross margin percentage.

        Returns:
            Gross margin as percentage (0-100).
        """
        if self.retail_price > 0:
            return (self.gross_profit / self.retail_price) * 100
        return 0.0

    @property
    def total_fees(self) -> float:
        """Calculate total fees.

        Returns:
            Total fees (shipping + platform + payment).
        """
        return self.shipping_cost + self.platform_fee + self.payment_fee

    @total_fees.setter
    def total_fees(self, value: float) -> None:
        """Set total fees."""
        object.__setattr__(self, "total_fees", value)

    @property
    def net_profit(self) -> float:
        """Calculate net profit per unit.

        Returns:
            Net profit per unit.
        """
        return self.retail_price - self.total_cost - self.total_fees

    @net_profit.setter
    def net_profit(self, value: float) -> None:
        """Set net profit."""
        object.__setattr__(self, "net_profit", value)

    @property
    def net_margin_pct(self) -> float:
        """Calculate net margin percentage.

        Returns:
            Net margin as percentage (0-100).
        """
        if self.retail_price > 0:
            return (self.net_profit / self.retail_price) * 100
        return 0.0

    @net_margin_pct.setter
    def net_margin_pct(self, value: float) -> None:
        """Set net margin percentage."""
        object.__setattr__(self, "net_margin_pct", value)

    def to_dict(self) -> dict:
        """Convert order to dictionary.

        Returns:
            Dictionary representation of the order.
        """
        d = asdict(self)
        d["gross_profit"] = self.gross_profit
        d["gross_margin_pct"] = self.gross_margin_pct
        d["net_profit"] = self.net_profit
        d["net_margin_pct"] = self.net_margin_pct
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Order:
        """Create Order from dictionary.

        Args:
            data: Dictionary with order data.

        Returns:
            Order instance.
        """
        # Extract known fields
        known_fields = {
            "order_id", "product_id", "supplier_id", "quantity",
            "unit_cost", "total_cost", "shipping_cost", "platform_fee",
            "payment_fee", "retail_price", "status",
        }
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        # Set defaults for missing fields
        if "shipping_cost" not in kwargs:
            kwargs["shipping_cost"] = 0.0
        if "platform_fee" not in kwargs:
            kwargs["platform_fee"] = 0.0
        if "payment_fee" not in kwargs:
            kwargs["payment_fee"] = 0.0
        if "retail_price" not in kwargs:
            kwargs["retail_price"] = 0.0
        if "status" not in kwargs:
            kwargs["status"] = "pending"
        # Pass raw data for unmapped fields
        kwargs["raw"] = {k: v for k, v in data.items() if k not in known_fields}
        instance = cls(**kwargs)
        # Set extra fields as attributes on the instance
        for key, value in kwargs["raw"].items():
            setattr(instance, key, value)
        return instance

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Order(order_id={self.order_id!r}, product_id={self.product_id!r}, "
            f"supplier_id={self.supplier_id!r}, quantity={self.quantity}, "
            f"status={self.status!r})"
        )
