"""Supplier import service - imports products from suppliers into the user's catalog."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.services.supplier_base import SupplierBase, SupplierProductInfo
from backend.models.supplier import SupplierConnection, SupplierProduct
from backend.models.product import Catalog, CatalogProduct
from backend.utils.database import async_session_factory
from backend.config import settings
from sqlalchemy import select


class ImportResult:
    """Result of a product import operation."""
    def __init__(
        self,
        supplier_id: str,
        supplier_name: str,
        products_imported: int = 0,
        products_skipped: int = 0,
        products_failed: int = 0,
        error_messages: Optional[List[str]] = None,
    ):
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.products_imported = products_imported
        self.products_skipped = products_skipped
        self.products_failed = products_failed
        self.error_messages = error_messages or []


class SupplierImportService:
    """Service for importing products from suppliers."""

    def __init__(self, supplier: SupplierBase):
        self.supplier = supplier

    async def import_products(
        self,
        user_id: str,
        catalog_id: str,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> ImportResult:
        """Import products from the supplier into the user's catalog.

        Args:
            user_id: The user's ID.
            catalog_id: The target catalog ID.
            category: Optional category filter.
            min_margin_pct: Minimum margin percentage filter.
            max_results: Maximum number of products to import.

        Returns:
            ImportResult with counts of imported, skipped, and failed products.
        """
        result = ImportResult(
            supplier_id=self.supplier.supplier_type,
            supplier_name=self.supplier.name,
        )

        # Fetch products from supplier
        try:
            supplier_products = await self.supplier.fetch_products(
                category=category,
                min_margin_pct=min_margin_pct,
                max_results=max_results,
            )
        except Exception as e:
            result.error_messages.append(f"Failed to fetch products: {str(e)}")
            return result

        if not supplier_products:
            return result

        async with async_session_factory() as session:
            # Get the catalog
            catalog_stmt = select(Catalog).where(
                Catalog.catalog_id == catalog_id,
                Catalog.user_id == user_id,
            )
            catalog_result = await session.execute(catalog_stmt)
            catalog = catalog_result.scalar_one_or_none()

            if not catalog:
                result.error_messages.append(f"Catalog {catalog_id} not found for user {user_id}")
                return result

            # Get existing supplier products to check for duplicates
            existing_stmt = select(SupplierProduct).where(
                SupplierProduct.supplier_id == self.supplier.supplier_type,
            )
            existing_result = await session.execute(existing_stmt)
            existing_products = {sp.supplier_product_id: sp for sp in existing_result.scalars().all()}

            # Get existing catalog products
            catalog_products_stmt = select(CatalogProduct).where(
                CatalogProduct.catalog_id == catalog_id,
            )
            catalog_products_result = await session.execute(catalog_products_stmt)
            existing_catalog_products = {cp.supplier_product_id: cp for cp in catalog_products_result.scalars().all()}

            for supplier_product in supplier_products:
                try:
                    # Check if product already exists in supplier products
                    if supplier_product.supplier_product_id in existing_products:
                        result.products_skipped += 1
                        continue

                    # Create supplier product record
                    supplier_product_record = SupplierProduct(
                        product_id=str(uuid.uuid4()),
                        supplier_id=self.supplier.supplier_type,
                        supplier_product_id=supplier_product.supplier_product_id,
                        title=supplier_product.title,
                        image_url=supplier_product.image_url,
                        description=supplier_product.description,
                        category=supplier_product.category,
                        variants=supplier_product.variants,
                        landed_cost=supplier_product.landed_cost,
                        retail_price=supplier_product.retail_price,
                        margin_pct=supplier_product.margin_pct,
                        inventory=supplier_product.inventory,
                        min_order=supplier_product.min_order,
                        shipping_time_days=supplier_product.shipping_time_days,
                        niche_id=catalog.niche_id,
                        in_catalog=False,
                    )
                    session.add(supplier_product_record)

                    # Add to catalog
                    catalog_product = CatalogProduct(
                        catalog_id=catalog_id,
                        supplier_product_id=supplier_product.supplier_product_id,
                        product_id=supplier_product_record.product_id,
                        title=supplier_product.title,
                        image_url=supplier_product.image_url,
                        landed_cost=supplier_product.landed_cost,
                        retail_price=supplier_product.retail_price,
                        margin_pct=supplier_product.margin_pct,
                        inventory=supplier_product.inventory,
                        shipping_time_days=supplier_product.shipping_time_days,
                        status="imported",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(catalog_product)

                    result.products_imported += 1

                except Exception as e:
                    result.products_failed += 1
                    result.error_messages.append(f"Failed to import product {supplier_product.supplier_product_id}: {str(e)}")

            await session.commit()

        return result

    async def get_available_categories(self) -> List[str]:
        """Get list of available categories from the supplier."""
        if settings.mock_data:
            return ["Electronics", "Wearables", "Sports", "Home & Garden", "Fashion", "Beauty"]
        return []
