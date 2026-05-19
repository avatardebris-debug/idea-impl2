"""Shared Pydantic schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class NicheScore(BaseModel):
    niche_id: str
    name: str
    category: str
    demand_score: float
    supply_score: float
    competition_level: str = "medium"
    trend_direction: str = "stable"
    avg_margin_pct: float = 0.0
    combined_score: float = 0.0


class NicheCategory(BaseModel):
    category: str
    count: int
    avg_demand: float
    avg_supply: float


class ProductSuggestion(BaseModel):
    product_id: str
    title: str
    image_url: str
    estimated_cost: float
    suggested_retail: float
    margin_pct: float
    category: str
    supplier: str
    niche_id: str
    optimized_title: str
    variants: List[Dict[str, str]]
    demand_score: float
    supply_score: float
    in_catalog: bool = False


class CatalogSummary(BaseModel):
    total_products: int
    avg_margin_pct: float
    avg_cost: float
    avg_retail: float
    potential_profit: float


class ShopifyStore(BaseModel):
    store_id: str
    shop_name: str
    shop_domain: str
    access_token: str
    status: str
    created_at: Optional[datetime] = None


class SyncJob(BaseModel):
    job_id: str
    store_id: str
    status: str
    products_pushed: int
    products_failed: int
    total_products: int
    error_messages: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProductDetail(BaseModel):
    product_id: str
    title: str
    image_url: str
    estimated_cost: float
    suggested_retail: float
    margin_pct: float
    category: str
    supplier: str
    niche_id: str
    optimized_title: str
    variants: List[Dict[str, str]]
    demand_score: float
    supply_score: float
