"""Sync log ORM model."""

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class SyncLog(Base):
    """Tracks each sync run (price/inventory updates)."""
    __tablename__ = "sync_logs"

    log_id = Column(String, primary_key=True)
    supplier_id = Column(String, nullable=False)
    sync_type = Column(String, nullable=False)  # 'price', 'inventory', 'full'
    status = Column(String, default="pending")  # pending, running, success, failed
    products_updated = Column(Integer, default=0)
    products_failed = Column(Integer, default=0)
    products_skipped = Column(Integer, default=0)
    error_messages = Column(JSON, default=list)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
