"""Product model for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Product:
    """Represents a dropshipping product.

    Attributes:
        product_id: Unique identifier for the product.
        title: Product title/name.
        cost_price: Cost price of the product.
        retail_price: Retail selling price.
        category: Product category.
        sku: Stock keeping unit.
        weight_kg: Product weight in kilograms.
        dimensions_cm: Product dimensions (length, width, height) in cm.
        image_url: URL of product image.
        description: Product description.
        tags: Product tags.
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
        """Validate product fields."""
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.title or not self.title.strip():
            raise ValueError("title must be non-empty")
        if not isinstance(self.cost_price, (int, float)):
            raise ValueError("cost_price must be a number")
        if self.cost_price < 0:
            raise ValueError("cost_price must be non-negative")
        if not isinstance(self.retail_price, (int, float)):
            raise ValueError("retail_price must be a number")
        if self.retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        if self.retail_price < self.cost_price:
            raise ValueError("retail_price must be >= cost_price")

    @property
    def gross_margin(self) -> float:
        """Calculate gross margin percentage.

        Returns:
            Gross margin as percentage (0-100).
        """
        if self.retail_price > 0:
            return (self.retail_price - self.cost_price) / self.retail_price
        return 0.0

    def to_dict(self) -> dict:
        """Convert product to dictionary.

        Returns:
            Dictionary representation of the product.
        """
        d = asdict(self)
        d["gross_margin"] = self.gross_margin
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        """Create a Product from a dictionary.

        Args:
            data: Dictionary with product fields.

        Returns:
            Product instance.
        """
        # Extract known fields
        known_fields = {
            "product_id", "title", "cost_price", "retail_price",
            "category", "sku", "weight_kg", "dimensions_cm",
            "image_url", "description", "tags",
        }
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        # Set defaults for missing fields
        if "category" not in kwargs:
            kwargs["category"] = ""
        if "sku" not in kwargs:
            kwargs["sku"] = ""
        if "weight_kg" not in kwargs:
            kwargs["weight_kg"] = 0.0
        if "dimensions_cm" not in kwargs:
            kwargs["dimensions_cm"] = {}
        if "image_url" not in kwargs:
            kwargs["image_url"] = ""
        if "description" not in kwargs:
            kwargs["description"] = ""
        if "tags" not in kwargs:
            kwargs["tags"] = []
        # Pass raw data for unmapped fields
        kwargs["raw"] = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**kwargs)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Product(product_id={self.product_id!r}, title={self.title!r}, "
            f"cost_price={self.cost_price}, retail_price={self.retail_price})"
        )
