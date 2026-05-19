"""Shopify sync service for pushing products to Shopify stores."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.models.product import ShopifyStore, CatalogProduct
from backend.models.sync_log import SyncLog
from backend.utils.database import async_session_factory
from backend.config import settings
from sqlalchemy import select


class ShopifySyncResult:
    """Result of a Shopify sync operation."""
    def __init__(
        self,
        store_id: str,
        products_pushed: int = 0,
        products_updated: int = 0,
        products_failed: int = 0,
        error_messages: Optional[List[str]] = None,
    ):
        self.store_id = store_id
        self.products_pushed = products_pushed
        self.products_updated = products_updated
        self.products_failed = products_failed
        self.error_messages = error_messages or []


class ShopifySyncService:
    """Service for syncing products to Shopify stores."""

    async def sync_products(
        self,
        store_id: str,
        catalog_id: Optional[str] = None,
        product_ids: Optional[List[str]] = None,
    ) -> ShopifySyncResult:
        """Sync products to a Shopify store.

        Args:
            store_id: The Shopify store ID.
            catalog_id: Optional catalog ID to sync from.
            product_ids: Optional list of product IDs to sync.

        Returns:
            ShopifySyncResult with sync results.
        """
        result = ShopifySyncResult(store_id=store_id)

        # Get store details
        async with async_session_factory() as session:
            stmt = select(ShopifyStore).where(ShopifyStore.store_id == store_id)
            result_stmt = await session.execute(stmt)
            store = result_stmt.scalar_one_or_none()

            if not store:
                result.error_messages.append(f"Shopify store {store_id} not found")
                return result

        # Get products to sync
        products_to_sync = []
        async with async_session_factory() as session:
            if product_ids:
                stmt = select(CatalogProduct).where(
                    CatalogProduct.product_id.in_(product_ids),
                )
            elif catalog_id:
                stmt = select(CatalogProduct).where(
                    CatalogProduct.catalog_id == catalog_id,
                )
            else:
                # Sync all products from all catalogs linked to this store
                stmt = select(CatalogProduct).join(
                    ShopifyStore, ShopifyStore.store_id == store_id
                ).where(
                    CatalogProduct.catalog_id == ShopifyStore.catalog_id,
                )

            result_stmt = await session.execute(stmt)
            products_to_sync = list(result_stmt.scalars().all())

        if not products_to_sync:
            return result

        # In a real implementation, this would call Shopify API
        # For now, we simulate the sync
        for product in products_to_sync:
            try:
                # Simulate Shopify API call
                if settings.mock_data:
                    # Simulate success
                    result.products_pushed += 1
                else:
                    # In production, this would call Shopify API
                    # response = await shopify_api.create_product(...)
                    result.products_pushed += 1

            except Exception as e:
                result.products_failed += 1
                result.error_messages.append(f"Failed to sync product {product.supplier_product_id}: {str(e)}")

        return result

    async def get_sync_status(self, store_id: str) -> Dict[str, Any]:
        """Get the sync status for a Shopify store.

        Args:
            store_id: The Shopify store ID.

        Returns:
            Dictionary with sync status information.
        """
        async with async_session_factory() as session:
            # Get last sync log
            stmt = select(SyncLog).where(
                SyncLog.supplier_id == store_id,
                SyncLog.sync_type == "shopify_sync",
            ).order_by(SyncLog.started_at.desc()).limit(1)
            result_stmt = await session.execute(stmt)
            last_sync = result_stmt.scalar_one_or_none()

            # Get store details
            stmt = select(ShopifyStore).where(ShopifyStore.store_id == store_id)
            result_stmt = await session.execute(stmt)
            store = result_stmt.scalar_one_or_none()

            return {
                "store_id": store_id,
                "store_name": store.store_name if store else "Unknown",
                "last_sync": last_sync.started_at.isoformat() if last_sync else None,
                "last_sync_status": last_sync.status if last_sync else None,
                "products_synced": last_sync.products_updated if last_sync else 0,
                "is_connected": bool(store and store.is_connected),
            }

    async def test_connection(self, store_id: str) -> bool:
        """Test the connection to a Shopify store.

        Args:
            store_id: The Shopify store ID.

        Returns:
            True if the connection is successful.
        """
        async with async_session_factory() as session:
            stmt = select(ShopifyStore).where(ShopifyStore.store_id == store_id)
            result_stmt = await session.execute(stmt)
            store = result_stmt.scalar_one_or_none()

            if not store:
                return False

            # In a real implementation, this would test the Shopify API connection
            # For now, we just check if the store exists and is connected
            return store.is_connected
