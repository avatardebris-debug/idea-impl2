"""Price & inventory sync engine."""

import uuid
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.services.supplier_base import SupplierBase
from backend.models.supplier import SupplierConnection, SupplierProduct
from backend.models.product import CatalogProduct
from backend.models.sync_log import SyncLog
from backend.utils.database import async_session_factory
from backend.config import settings
from sqlalchemy import select


class SyncEngine:
    """Engine for syncing price and inventory data from suppliers."""

    def __init__(self, supplier: SupplierBase):
        self.supplier = supplier

    async def sync_prices(self, supplier_connection_id: str) -> SyncLog:
        """Sync price data from the supplier.

        Args:
            supplier_connection_id: The supplier connection ID.

        Returns:
            SyncLog with sync results.
        """
        return await self._run_sync(supplier_connection_id, "price")

    async def sync_inventory(self, supplier_connection_id: str) -> SyncLog:
        """Sync inventory data from the supplier.

        Args:
            supplier_connection_id: The supplier connection ID.

        Returns:
            SyncLog with sync results.
        """
        return await self._run_sync(supplier_connection_id, "inventory")

    async def sync_full(self, supplier_connection_id: str) -> SyncLog:
        """Sync both price and inventory data from the supplier.

        Args:
            supplier_connection_id: The supplier connection ID.

        Returns:
            SyncLog with sync results.
        """
        return await self._run_sync(supplier_connection_id, "full")

    async def _run_sync(self, supplier_connection_id: str, sync_type: str) -> SyncLog:
        """Run a sync operation.

        Args:
            supplier_connection_id: The supplier connection ID.
            sync_type: Type of sync ('price', 'inventory', 'full').

        Returns:
            SyncLog with sync results.
        """
        sync_log = SyncLog(
            log_id=str(uuid.uuid4()),
            supplier_id=supplier_connection_id,
            sync_type=sync_type,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        async with async_session_factory() as session:
            session.add(sync_log)
            await session.commit()

        try:
            # Get supplier connection
            async with async_session_factory() as session:
                stmt = select(SupplierConnection).where(
                    SupplierConnection.connection_id == supplier_connection_id,
                )
                result = await session.execute(stmt)
                connection = result.scalar_one_or_none()

                if not connection:
                    raise ValueError(f"Supplier connection {supplier_connection_id} not found")

                # Get supplier products
                products_stmt = select(SupplierProduct).where(
                    SupplierProduct.supplier_id == connection.supplier_type,
                )
                products_result = await session.execute(products_stmt)
                supplier_products = products_result.scalars().all()

            if not supplier_products:
                sync_log.status = "success"
                sync_log.products_updated = 0
                sync_log.products_skipped = 0
                sync_log.completed_at = datetime.now(timezone.utc)
                sync_log.duration_seconds = 0
                return sync_log

            # Fetch data from supplier
            product_ids = [sp.supplier_product_id for sp in supplier_products]
            updated_count = 0
            skipped_count = 0
            failed_count = 0
            error_messages = []

            if sync_type in ("price", "full"):
                try:
                    pricing = await self.supplier.get_pricing(product_ids)
                    async with async_session_factory() as session:
                        for sp in supplier_products:
                            if sp.supplier_product_id in pricing:
                                sp.retail_price = pricing[sp.supplier_product_id]
                                sp.updated_at = datetime.now(timezone.utc)
                                updated_count += 1
                            else:
                                skipped_count += 1
                        await session.commit()
                except Exception as e:
                    error_messages.append(f"Price sync failed: {str(e)}")
                    failed_count += len(product_ids)

            if sync_type in ("inventory", "full"):
                try:
                    inventory = await self.supplier.check_inventory(product_ids)
                    async with async_session_factory() as session:
                        for sp in supplier_products:
                            if sp.supplier_product_id in inventory:
                                sp.inventory = inventory[sp.supplier_product_id]
                                sp.updated_at = datetime.now(timezone.utc)
                                updated_count += 1
                            else:
                                skipped_count += 1
                        await session.commit()
                except Exception as e:
                    error_messages.append(f"Inventory sync failed: {str(e)}")
                    failed_count += len(product_ids)

            # Update catalog products
            if updated_count > 0:
                async with async_session_factory() as session:
                    catalog_products_stmt = select(CatalogProduct).where(
                        CatalogProduct.supplier_product_id.in_(product_ids),
                    )
                    catalog_products_result = await session.execute(catalog_products_stmt)
                    catalog_products = catalog_products_result.scalars().all()

                    for cp in catalog_products:
                        # Find corresponding supplier product
                        for sp in supplier_products:
                            if sp.supplier_product_id == cp.supplier_product_id:
                                if sync_type in ("price", "full"):
                                    cp.retail_price = sp.retail_price
                                if sync_type in ("inventory", "full"):
                                    cp.inventory = sp.inventory
                                cp.updated_at = datetime.now(timezone.utc)
                                break

                    await session.commit()

            sync_log.status = "success" if failed_count == 0 else "failed"
            sync_log.products_updated = updated_count
            sync_log.products_skipped = skipped_count
            sync_log.products_failed = failed_count
            sync_log.error_messages = error_messages
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.duration_seconds = time.time() - sync_log.started_at.timestamp()

            async with async_session_factory() as session:
                session.add(sync_log)
                await session.commit()

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_messages = [str(e)]
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.duration_seconds = time.time() - sync_log.started_at.timestamp()

            async with async_session_factory() as session:
                session.add(sync_log)
                await session.commit()

        return sync_log
