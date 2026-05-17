"""Product model for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Product:
    """Represents a dropshipping product.

    Attributes:
        product_id: Unique identifier for the product.
        title: Product title.
        cost_price: Cost price from the supplier.
        retail_price: Suggested retail price.
        category: Product category.
        sku: Stock keeping unit.
        weight_kg: Weight in kilograms.
        dimensions_cm: Dimensions (length, width, height) in centimeters.
        image_url: URL to product image.
        description: Product description.
        tags: List of product tags.
        raw: Extra unmapped fields.
    """
    product_id: str
    title: str
    cost_price: float
    retail_price: float
    category: str = ""
    sku: str = ""
    weight_kg: float = 0.0
    dimensions_cm: dict = field(default_factory=dict)
    image_url: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate product data after initialization."""
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not isinstance(self.cost_price, (int, float)):
            raise ValueError("cost_price must be a number")
        if not isinstance(self.retail_price, (int, float)):
            raise ValueError("retail_price must be a number")
        if self.cost_price < 0:
            raise ValueError("cost_price must be non-negative")
        if self.retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        if self.retail_price < self.cost_price:
            raise ValueError("retail_price must be >= cost_price")

    @property
    def gross_margin(self) -> float:
        """Calculate gross margin as decimal (0-1).

        Returns:
            Gross margin percentage as decimal.
        """
        if self.retail_price <= 0:
            return 0.0
        return (self.retail_price - self.cost_price) / self.retail_price

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        result = asdict(self)
        result["gross_margin"] = self.gross_margin
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        """Create from dictionary.

        Args:
            data: Dictionary with product fields.

        Returns:
            Product instance.
        """
        # Remove gross_margin if present since it's a computed property
        data = {k: v for k, v in data.items() if k != "gross_margin"}
        return cls(**data)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Product(id={self.product_id}, title={self.title}, "
            f"cost={self.cost_price}, retail={self.retail_price})"
        )
