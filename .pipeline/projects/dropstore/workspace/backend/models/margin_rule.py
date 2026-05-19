"""Margin rule ORM model."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class MarginRule(Base):
    """A pricing margin rule that can be applied to catalog products."""
    __tablename__ = "margin_rules"

    rule_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    markup_pct = Column(Float, nullable=False)  # Markup percentage (e.g., 40 = 40%)
    min_margin_pct = Column(Float, default=0)  # Minimum margin floor
    max_margin_pct = Column(Float, default=200)  # Maximum margin cap
    price_rounding = Column(String, default="none")  # 'none', '.99', '.95', '.50', '.00'
    is_active = Column(Boolean, default=True)
    applies_to_all = Column(Boolean, default=False)
    niche_filter = Column(JSON, default=list)  # List of niche_ids to apply to
    category_filter = Column(JSON, default=list)  # List of categories to apply to
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
