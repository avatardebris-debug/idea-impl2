"""Supplier management service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.supplier import Supplier, SupplierProduct, SupplierIntegration
from backend.utils.database import async_session_factory


def _generate_supplier_id() -> str:
    """Generate a unique supplier ID."""
    return f"sup_{uuid.uuid4().hex[:12]}"


def _generate_supplier_product_id() -> str:
    """Generate a unique supplier product ID."""
    return f"sup_prod_{uuid.uuid4().hex[:12]}"


async def create_supplier(
    name: str,
    contact_email: str,
    contact_phone: str = "",
    website: str = "",
    description: str = "",
    is_active: bool = True,
) -> Supplier:
    """Create a new supplier."""
    supplier_id = _generate_supplier_id()

    supplier = Supplier(
        supplier_id=supplier_id,
        name=name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        website=website,
        description=description,
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)
    return supplier


async def get_supplier(supplier_id: str) -> Optional[Supplier]:
    """Get a supplier by ID."""
    async with async_session_factory() as session:
        supplier = await session.get(Supplier, supplier_id)
        return supplier


async def list_suppliers(is_active: Optional[bool] = None) -> List[Supplier]:
    """List suppliers with optional filters."""
    async with async_session_factory() as session:
        query = Supplier.__table__.select()
        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)
        query = query.order_by(Supplier.name)
        suppliers = await session.execute(query)
        return list(suppliers.scalars().all())


async def update_supplier(supplier_id: str, **kwargs) -> Optional[Supplier]:
    """Update supplier information."""
    async with async_session_factory() as session:
        supplier = await session.get(Supplier, supplier_id)
        if supplier:
            for key, value in kwargs.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            await session.commit()
            await session.refresh(supplier)
        return supplier


async def create_supplier_product(
    supplier_id: str,
    supplier_product_id: str,
    title: str,
    price: float,
    description: str = "",
    compare_at_price: Optional[float] = None,
    images: Optional[List[str]] = None,
    variants: Optional[List[Dict[str, Any]]] = None,
    categories: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    weight: Optional[float] = None,
    dimensions: Optional[Dict[str, Any]] = None,
    shipping_info: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> SupplierProduct:
    """Create a new supplier product."""
    product_id = _generate_supplier_product_id()

    product = SupplierProduct(
        product_id=product_id,
        supplier_id=supplier_id,
        supplier_product_id=supplier_product_id,
        title=title,
        description=description,
        price=price,
        compare_at_price=compare_at_price,
        images=images or [],
        variants=variants or [],
        categories=categories or [],
        tags=tags or [],
        weight=weight,
        dimensions=dimensions or {},
        shipping_info=shipping_info or {},
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(product)
        await session.commit()
        await session.refresh(product)
    return product


async def get_supplier_product(product_id: str) -> Optional[SupplierProduct]:
    """Get a supplier product by ID."""
    async with async_session_factory() as session:
        product = await session.get(SupplierProduct, product_id)
        return product


async def list_supplier_products(
    supplier_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> List[SupplierProduct]:
    """List supplier products with optional filters."""
    async with async_session_factory() as session:
        query = SupplierProduct.__table__.select()
        if supplier_id:
            query = query.where(SupplierProduct.supplier_id == supplier_id)
        if is_active is not None:
            query = query.where(SupplierProduct.is_active == is_active)
        if category:
            query = query.where(SupplierProduct.categories.contains([category]))
        query = query.order_by(SupplierProduct.title).limit(limit)
        products = await session.execute(query)
        return list(products.scalars().all())


async def update_supplier_product(product_id: str, **kwargs) -> Optional[SupplierProduct]:
    """Update supplier product information."""
    async with async_session_factory() as session:
        product = await session.get(SupplierProduct, product_id)
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            await session.commit()
            await session.refresh(product)
        return product


async def create_supplier_integration(
    supplier_id: str,
    integration_type: str,
    api_key: str,
    api_secret: Optional[str] = None,
    webhook_url: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> SupplierIntegration:
    """Create a new supplier integration."""
    integration_id = f"int_{uuid.uuid4().hex[:12]}"

    integration = SupplierIntegration(
        integration_id=integration_id,
        supplier_id=supplier_id,
        integration_type=integration_type,
        api_key=api_key,
        api_secret=api_secret or "",
        webhook_url=webhook_url or "",
        config=config or {},
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(integration)
        await session.commit()
        await session.refresh(integration)
    return integration


async def get_supplier_integration(integration_id: str) -> Optional[SupplierIntegration]:
    """Get a supplier integration by ID."""
    async with async_session_factory() as session:
        integration = await session.get(SupplierIntegration, integration_id)
        return integration


async def list_supplier_integrations(supplier_id: Optional[str] = None) -> List[SupplierIntegration]:
    """List supplier integrations with optional filters."""
    async with async_session_factory() as session:
        query = SupplierIntegration.__table__.select()
        if supplier_id:
            query = query.where(SupplierIntegration.supplier_id == supplier_id)
        query = query.order_by(SupplierIntegration.integration_type)
        integrations = await session.execute(query)
        return list(integrations.scalars().all())
