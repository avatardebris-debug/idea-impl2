"""SQLAlchemy ORM models."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class Niche(Base):
    __tablename__ = "niches"

    niche_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    demand_score = Column(Float, default=0)
    supply_score = Column(Float, default=0)
    competition_level = Column(String, default="medium")
    trend_direction = Column(String, default="stable")
    avg_margin_pct = Column(Float, default=0)
    combined_score = Column(Float, default=0)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    image_url = Column(String)
    estimated_cost = Column(Float, nullable=False)
    suggested_retail = Column(Float, nullable=False)
    margin_pct = Column(Float, nullable=False)
    category = Column(String)
    supplier = Column(String)
    niche_id = Column(String, nullable=False)
    optimized_title = Column(String)
    variants = Column(JSON, default=list)
    demand_score = Column(Float, default=0)
    supply_score = Column(Float, default=0)


class Catalog(Base):
    __tablename__ = "catalogs"

    catalog_id = Column(String, primary_key=True)
    niche_id = Column(String, nullable=False)
    niche_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CatalogProduct(Base):
    __tablename__ = "catalog_products"

    id = Column(Integer, primary_key=True)
    catalog_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    title = Column(String)
    image_url = Column(String)
    estimated_cost = Column(Float)
    suggested_retail = Column(Float)
    margin_pct = Column(Float)
    category = Column(String)
    supplier = Column(String)
    niche_id = Column(String)
    optimized_title = Column(String)
    variants = Column(JSON, default=list)
    in_catalog = Column(Boolean, default=True)


class ShopifyStore(Base):
    __tablename__ = "shopify_stores"

    store_id = Column(String, primary_key=True)
    shop_name = Column(String, nullable=False)
    shop_domain = Column(String, nullable=False)
    access_token = Column(Text, nullable=False)
    status = Column(String, default="connected")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    job_id = Column(String, primary_key=True)
    store_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    products_pushed = Column(Integer, default=0)
    products_failed = Column(Integer, default=0)
    total_products = Column(Integer, default=0)
    error_messages = Column(JSON, default=list)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
