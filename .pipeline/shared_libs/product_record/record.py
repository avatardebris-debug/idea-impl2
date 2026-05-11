"""Generic product record dataclass for e-commerce catalogs.

A typed dataclass representing a single product with optional fields
for common e-commerce attributes, plus a raw dict for unmapped columns.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProductRecord:
    """A single product record with canonical field names.

    All fields are optional to support partial data. The `raw` dict
    stores any unmapped columns from the source CSV.
    """
    product_id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[str] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    url: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    raw: dict = field(default_factory=dict)
