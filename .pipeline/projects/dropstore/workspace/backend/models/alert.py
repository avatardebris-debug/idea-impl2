"""Alert ORM model."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class Alert(Base):
    """A notification/alert for the user."""
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True)
    alert_type = Column(String, nullable=False)  # 'low_stock', 'price_change', 'supplier_error', 'sync_failure'
    severity = Column(String, nullable=False)  # 'info', 'warning', 'critical'
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    product_id = Column(String)
    supplier_id = Column(String)
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    action_suggestion = Column(Text, default="")
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    dismissed_at = Column(DateTime(timezone=True))
