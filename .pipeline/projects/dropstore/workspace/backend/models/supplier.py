"""Supplier ORM models."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class SupplierConnection(Base):
    """A connected supplier account (AliExpress, CJDropshipping, etc.)."""
    __tablename__ = "supplier_connections"

    connection_id = Column(String, primary_key=True)
    supplier_type = Column(String, nullable=False)  # 'aliexpress', 'cjdropshipping'
    name = Column(String, nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, inactive, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SupplierProduct(Base):
    """A product fetched from a supplier."""
    __tablename__ = "supplier_products"

    product_id = Column(String, primary_key=True)
    supplier_id = Column(String, nullable=False)
    supplier_product_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(String)
    description = Column(Text)
    category = Column(String)
    variants = Column(JSON, default=list)
    landed_cost = Column(Float, nullable=False)
    retail_price = Column(Float, nullable=False)
    margin_pct = Column(Float, nullable=False)
    inventory = Column(Integer, default=0)
    min_order = Column(Integer, default=1)
    shipping_time_days = Column(Integer, default=0)
    niche_id = Column(String)
    in_catalog = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
