"""Pydantic models for multi-store competitor analysis."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ProductMatch(BaseModel):
    """Represents a matched product across stores."""

    product_name: str = Field(description="Canonical product name")
    price_at_store: float = Field(description="Price at the primary store")
    price_at_source: Optional[float] = Field(default=None, description="Price at the supplier/source")
    overlap_score: float = Field(description="Similarity score (0.0–1.0) indicating how likely these are the same product")


class SupplierChain(BaseModel):
    """Represents a detected supplier chain for a store."""

    source: str = Field(description="Supplier source name (e.g., 'AliExpress', 'CJ Dropshipping')")
    confidence: float = Field(description="Confidence score (0.0–1.0) for this detection")
    detected_urls: List[str] = Field(default_factory=list, description="List of detected supplier URLs")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated supplier cost if detectable")


class StoreAnalysis(BaseModel):
    """Analysis results for a single competitor store."""

    stores_url: str = Field(description="The URL of the analyzed store")
    platform: str = Field(description="Detected e-commerce platform (e.g., 'Shopify', 'WooCommerce', 'Generic')")
    products: List[dict] = Field(default_factory=list, description="List of extracted product dicts with keys: name, price, description, image_url, url")
    supplier_info: List[SupplierChain] = Field(default_factory=list, description="Detected supplier chains")
    raw_html: str = Field(default="", description="Raw HTML content of the store page")


class CompetitorComparison(BaseModel):
    """Aggregated comparison across multiple competitor stores."""

    stores: List[StoreAnalysis] = Field(description="List of analyzed stores")
    product_overlaps: List[dict] = Field(default_factory=list, description="List of overlapping product dicts with keys: product_name, stores, prices, price_spread")
    price_gaps: List[dict] = Field(default_factory=list, description="List of price gap dicts with keys: product_name, store_prices, max_price, min_price, gap_pct")
    margins: List[dict] = Field(default_factory=list, description="List of margin estimate dicts")
    insights: List[str] = Field(default_factory=list, description="List of actionable insights")
