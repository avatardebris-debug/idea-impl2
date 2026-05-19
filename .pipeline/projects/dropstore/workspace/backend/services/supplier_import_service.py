"""Supplier import service for fetching and storing supplier products."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from backend.services.supplier_base import SupplierBase
from backend.models.supplier import SupplierProduct
from backend.utils.database import async_session_factory
from sqlalchemy import select


class SupplierImportService:
    """Service for importing products from supplier APIs into the database."""

    def __init__(self, supplier: SupplierBase):
        self.supplier = supplier

    async def import_products(
        self,
        supplier_connection_id: str,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> dict:
        """Import products from a supplier into the database.

        Args:
            supplier_connection_id: The supplier connection ID.
            category: Optional category filter.
            min_margin_pct: Minimum margin percentage filter.
            max_results: Maximum number of products to import.

        Returns:
            Dict with import results (imported, updated, failed counts).
        """
        results = {"imported": 0, "updated": 0, "failed": 0, "errors": []}

        # Fetch products from supplier
        supplier_products = await self.supplier.fetch_products(
            category=category,
            min_margin_pct=min_margin_pct,
            max_results=max_results,
        )

        if not supplier_products:
            return results

        async with async_session_factory() as session:
            for sp in supplier_products:
                try:
                    # Check if product already exists
                    stmt = select(SupplierProduct).where(
                        SupplierProduct.supplier_product_id == sp.supplier_product_id,
                        SupplierProduct.supplier_id == supplier_connection_id,
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update existing product
                        existing.title = sp.title
                        existing.image_url = sp.image_url
                        existing.description = sp.description
                        existing.category = sp.category
                        existing.variants = sp.variants
                        existing.landed_cost = sp.landed_cost
                        existing.retail_price = sp.retail_price
                        existing.margin_pct = sp.margin_pct
                        existing.inventory = sp.inventory
                        existing.min_order = sp.min_order
                        existing.shipping_time_days = sp.shipping_time_days
                        existing.updated_at = datetime.now(timezone.utc)
                        results["updated"] += 1
                    else:
                        # Create new product
                        new_product = SupplierProduct(
                            product_id=str(uuid.uuid4()),
                            supplier_id=supplier_connection_id,
                            supplier_product_id=sp.supplier_product_id,
                            title=sp.title,
                            image_url=sp.image_url,
                            description=sp.description,
                            category=sp.category,
                            variants=sp.variants,
                            landed_cost=sp.landed_cost,
                            retail_price=sp.retail_price,
                            margin_pct=sp.margin_pct,
                            inventory=sp.inventory,
                            min_order=sp.min_order,
                            shipping_time_days=sp.shipping_time_days,
                            niche_id=None,
                            in_catalog=False,
                        )
                        session.add(new_product)
                        results["imported"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "supplier_product_id": sp.supplier_product_id,
                        "error": str(e),
                    })

            await session.commit()

        return results

    async def get_imported_products(
        self,
        supplier_connection_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SupplierProduct]:
        """Get products imported from a specific supplier connection."""
        async with async_session_factory() as session:
            stmt = (
                select(SupplierProduct)
                .where(SupplierProduct.supplier_id == supplier_connection_id)
                .order_by(SupplierProduct.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_product_count(self, supplier_connection_id: str) -> int:
        """Get the count of products for a supplier connection."""
        async with async_session_factory() as session:
            stmt = select(SupplierProduct).where(
                SupplierProduct.supplier_id == supplier_connection_id
            )
            result = await session.execute(stmt)
            return len(result.scalars().all())
