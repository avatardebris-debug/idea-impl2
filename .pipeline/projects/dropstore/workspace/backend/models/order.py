"""Order ORM models for unified order management."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class Order(Base):
    """A customer order from a storefront."""
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    store_id = Column(String, nullable=False)
    platform_order_id = Column(String)  # Original order ID from Shopify/WooCommerce
    customer_name = Column(String, nullable=False)
    customer_email = Column(String)
    status = Column(String, default="pending")  # pending, processing, fulfilled, shipped, delivered, cancelled
    payment_status = Column(String, default="pending")  # pending, paid, refunded, partially_refunded
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    shipping_address = Column(JSON, default=dict)
    billing_address = Column(JSON, default=dict)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrderItem(Base):
    """A line item within an order."""
    __tablename__ = "order_items"

    item_id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    product_title = Column(String, nullable=False)
    variant_id = Column(String)
    variant_title = Column(String)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    image_url = Column(String)
    supplier = Column(String)
    supplier_product_id = Column(String)
    fulfillment_status = Column(String, default="unfulfilled")  # unfulfilled, partial, fulfilled


class OrderFulfillment(Base):
    """Fulfillment tracking for an order."""
    __tablename__ = "order_fulfillments"

    fulfillment_id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    supplier_id = Column(String)
    supplier_order_id = Column(String)
    tracking_number = Column(String)
    tracking_url = Column(String)
    carrier = Column(String)
    status = Column(String, default="pending")  # pending, shipped, delivered
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    notes = Column(Text, default="")
