"""Analytics ORM models."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class DailyMetrics(Base):
    """Daily aggregated metrics for a store."""
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True)
    store_id = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    page_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    sessions = Column(Integer, default=0)
    bounce_rate = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    orders = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    top_referrer = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductPerformance(Base):
    """Product-level performance metrics."""
    __tablename__ = "product_performance"

    id = Column(Integer, primary_key=True)
    product_id = Column(String, nullable=False)
    store_id = Column(String, nullable=False)
    product_title = Column(String)
    total_views = Column(Integer, default=0)
    total_add_to_cart = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    avg_position = Column(Float, default=0.0)
    last_viewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalyticsSnapshot(Base):
    """Periodic analytics snapshot for trend analysis."""
    __tablename__ = "analytics_snapshots"

    snapshot_id = Column(String, primary_key=True)
    store_id = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    total_revenue = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    total_products_sold = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0.0)
    total_visitors = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    top_categories = Column(JSON, default=list)
    top_products = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
