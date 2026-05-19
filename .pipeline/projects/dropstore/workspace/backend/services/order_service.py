"""Order management service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.order import Order, OrderItem, OrderFulfillment
from backend.utils.database import async_session_factory


def _generate_order_id() -> str:
    """Generate a unique order ID."""
    return f"ord_{uuid.uuid4().hex[:12]}"


async def create_order(
    store_id: str,
    customer_name: str,
    customer_email: str,
    total_amount: float,
    currency: str = "USD",
    shipping_address: Optional[Dict[str, Any]] = None,
    billing_address: Optional[Dict[str, Any]] = None,
    notes: str = "",
) -> Order:
    """Create a new order."""
    order_id = _generate_order_id()

    order = Order(
        order_id=order_id,
        store_id=store_id,
        customer_name=customer_name,
        customer_email=customer_email,
        status="pending",
        payment_status="pending",
        total_amount=total_amount,
        currency=currency,
        shipping_address=shipping_address or {},
        billing_address=billing_address or {},
        notes=notes,
    )

    async with async_session_factory() as session:
        session.add(order)
        await session.commit()
        await session.refresh(order)
    return order


async def get_order(order_id: str) -> Optional[Order]:
    """Get an order by ID."""
    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        return order


async def list_orders(store_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Order]:
    """List orders with optional filters."""
    async with async_session_factory() as session:
        query = Order.__table__.select()
        if store_id:
            query = query.where(Order.store_id == store_id)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc()).limit(limit)
        orders = await session.execute(query)
        return list(orders.scalars().all())


async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    """Update order status."""
    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if order:
            order.status = status
            await session.commit()
            await session.refresh(order)
        return order


async def add_order_item(
    order_id: str,
    product_id: str,
    product_title: str,
    quantity: int,
    unit_price: float,
    variant_id: Optional[str] = None,
    variant_title: Optional[str] = None,
    image_url: Optional[str] = None,
    supplier: Optional[str] = None,
    supplier_product_id: Optional[str] = None,
) -> OrderItem:
    """Add an item to an order."""
    item_id = f"item_{uuid.uuid4().hex[:12]}"

    item = OrderItem(
        item_id=item_id,
        order_id=order_id,
        product_id=product_id,
        product_title=product_title,
        variant_id=variant_id,
        variant_title=variant_title,
        quantity=quantity,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        image_url=image_url or "",
        supplier=supplier or "",
        supplier_product_id=supplier_product_id or "",
        fulfillment_status="unfulfilled",
    )

    async with async_session_factory() as session:
        session.add(item)
        await session.commit()
        await session.refresh(item)
    return item


async def get_order_items(order_id: str) -> List[OrderItem]:
    """Get all items for an order."""
    async with async_session_factory() as session:
        items = await session.execute(
            OrderItem.__table__.select().where(OrderItem.order_id == order_id)
        )
        return list(items.scalars().all())


async def create_fulfillment(
    order_id: str,
    supplier_id: Optional[str] = None,
    tracking_number: Optional[str] = None,
    tracking_url: Optional[str] = None,
    carrier: Optional[str] = None,
    notes: str = "",
) -> OrderFulfillment:
    """Create a fulfillment record for an order."""
    fulfillment_id = f"ful_{uuid.uuid4().hex[:12]}"

    fulfillment = OrderFulfillment(
        fulfillment_id=fulfillment_id,
        order_id=order_id,
        supplier_id=supplier_id or "",
        supplier_order_id="",
        tracking_number=tracking_number or "",
        tracking_url=tracking_url or "",
        carrier=carrier or "",
        status="pending",
        notes=notes,
    )

    async with async_session_factory() as session:
        session.add(fulfillment)
        await session.commit()
        await session.refresh(fulfillment)
    return fulfillment


async def update_fulfillment_status(fulfillment_id: str, status: str, tracking_number: Optional[str] = None) -> Optional[OrderFulfillment]:
    """Update fulfillment status."""
    async with async_session_factory() as session:
        fulfillment = await session.get(OrderFulfillment, fulfillment_id)
        if fulfillment:
            fulfillment.status = status
            if tracking_number:
                fulfillment.tracking_number = tracking_number
            if status == "shipped":
                fulfillment.shipped_at = datetime.now(timezone.utc)
            elif status == "delivered":
                fulfillment.delivered_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(fulfillment)
        return fulfillment
