"""Data models for droppain."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Product:
    """Represents a product from a dropship store (e.g. Shopify)."""

    id: str
    title: str
    price: float
    image_url: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    vendor: str = ""
    product_type: str = ""
    variants: List["Variant"] = field(default_factory=list)
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def display_price(self) -> str:
        """Return formatted price string."""
        return f"${self.price:.2f}"

    @property
    def is_available(self) -> bool:
        """Check if the product is available for purchase."""
        if self.status != "active":
            return False
        if not self.variants:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        d = asdict(self)
        d["variants"] = [v.to_dict() for v in self.variants]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        """Create a Product from a dictionary."""
        variants_data = data.get("variants", [])
        variants = [Variant.from_dict(v) for v in variants_data]
        data = {k: v for k, v in data.items() if k != "variants"}
        return cls(variants=variants, **data)


@dataclass
class Variant:
    """Represents a product variant."""

    id: str
    title: str
    price: float
    sku: str = ""
    inventory_quantity: int = 0
    available: bool = True

    @property
    def display_price(self) -> str:
        """Return formatted price string."""
        return f"${self.price:.2f}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variant":
        """Create a Variant from a dictionary."""
        return cls(**data)
