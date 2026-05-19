"""Store ORM models for multi-platform store support."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class Store(Base):
    """A connected storefront (Shopify, WooCommerce, etc.)."""
    __tablename__ = "stores"

    store_id = Column(String, primary_key=True)
    platform_type = Column(String, nullable=False)  # 'shopify', 'woocommerce', 'custom'
    store_name = Column(String, nullable=False)
    store_domain = Column(String, nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, default="")
    status = Column(String, default="connected")  # connected, disconnected, error
    settings = Column(JSON, default=dict)  # Platform-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StoreTemplate(Base):
    """A store template that defines layout and styling."""
    __tablename__ = "store_templates"

    template_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    platform_type = Column(String, nullable=False)  # 'shopify', 'woocommerce'
    category = Column(String, default="general")  # 'general', 'fashion', 'tech', etc.
    preview_image_url = Column(String, default="")
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TemplateSection(Base):
    """A section within a store template."""
    __tablename__ = "template_sections"

    section_id = Column(String, primary_key=True)
    template_id = Column(String, nullable=False)
    section_type = Column(String, nullable=False)  # 'hero', 'product_grid', 'features', 'testimonials', 'footer'
    display_order = Column(Integer, default=0)
    config = Column(JSON, default=dict)  # Section-specific configuration
    is_visible = Column(Boolean, default=True)


class TemplateStyle(Base):
    """Styling configuration for a store template."""
    __tablename__ = "template_styles"

    style_id = Column(String, primary_key=True)
    template_id = Column(String, nullable=False)
    primary_color = Column(String, default="#000000")
    secondary_color = Column(String, default="#666666")
    background_color = Column(String, default="#ffffff")
    text_color = Column(String, default="#333333")
    font_family = Column(String, default="Inter, sans-serif")
    font_size_base = Column(String, default="16px")
    border_radius = Column(String, default="8px")
    spacing = Column(String, default="24px")
    custom_css = Column(Text, default="")
