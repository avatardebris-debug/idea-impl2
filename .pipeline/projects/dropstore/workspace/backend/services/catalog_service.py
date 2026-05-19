"""Catalog management service."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from backend.models.product import Catalog, CatalogProduct, Product
from backend.utils.database import async_session_factory


async def create_catalog(niche_id: str, niche_name: str) -> Catalog:
    """Create a new catalog for a niche."""
    catalog_id = f"cat_{uuid.uuid4().hex[:12]}"
    catalog = Catalog(
        catalog_id=catalog_id,
        niche_id=niche_id,
        niche_name=niche_name,
    )
    async with async_session_factory() as session:
        session.add(catalog)
        await session.commit()
        await session.refresh(catalog)
        return catalog


async def add_products_to_catalog(catalog_id: str, products: List[Product]) -> List[CatalogProduct]:
    """Add products to a catalog."""
    catalog_products = []
    async with async_session_factory() as session:
        for product in products:
            cp = CatalogProduct(
                catalog_id=catalog_id,
                product_id=product.product_id,
                title=product.title,
                image_url=product.image_url,
                estimated_cost=product.estimated_cost,
                suggested_retail=product.suggested_retail,
                margin_pct=product.margin_pct,
                category=product.category,
                supplier=product.supplier,
                niche_id=product.niche_id,
                optimized_title=product.optimized_title,
                variants=product.variants,
                in_catalog=True,
            )
            session.add(cp)
            catalog_products.append(cp)
        await session.commit()
        # Refresh to get IDs
        for cp in catalog_products:
            await session.refresh(cp)
        return catalog_products


async def get_catalog(catalog_id: str) -> Optional[Catalog]:
    """Get a catalog by ID."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(Catalog).where(Catalog.catalog_id == catalog_id))
        return result.scalar_one_or_none()


async def get_catalog_products(catalog_id: str) -> List[CatalogProduct]:
    """Get all products in a catalog."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(CatalogProduct).where(CatalogProduct.catalog_id == catalog_id)
        )
        return list(result.scalars().all())


async def remove_product_from_catalog(catalog_id: str, product_id: str) -> bool:
    """Remove a product from a catalog."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(CatalogProduct).where(
                CatalogProduct.catalog_id == catalog_id,
                CatalogProduct.product_id == product_id
            )
        )
        cp = result.scalar_one_or_none()
        if cp:
            cp.in_catalog = False
            await session.commit()
            return True
        return False


async def get_catalog_stats(catalog_id: str) -> dict:
    """Get statistics for a catalog."""
    products = await get_catalog_products(catalog_id)
    if not products:
        return {"total_products": 0, "avg_margin": 0, "avg_cost": 0, "avg_retail": 0}

    total = len(products)
    avg_margin = sum(p.margin_pct for p in products) / total
    avg_cost = sum(p.estimated_cost for p in products) / total
    avg_retail = sum(p.suggested_retail for p in products) / total

    return {
        "total_products": total,
        "avg_margin_pct": round(avg_margin, 1),
        "avg_cost": round(avg_cost, 2),
        "avg_retail": round(avg_retail, 2),
        "potential_profit": round((avg_retail - avg_cost) * total, 2),
    }
