"""Redis-based sync scheduler."""

import asyncio
import uuid
from typing import Optional
from datetime import datetime, timezone, timedelta

from backend.config import settings
from backend.services.sync_engine import SyncEngine
from backend.services.supplier_base import SupplierBase
from backend.models.supplier import SupplierConnection
from backend.models.sync_log import SyncLog
from backend.utils.database import async_session_factory
from sqlalchemy import select


class SyncScheduler:
    """Scheduler for periodic sync operations."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._sync_interval = settings.sync_interval_hours * 3600  # Convert hours to seconds

    async def start(self):
        """Start the sync scheduler."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """Stop the sync scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _sync_loop(self):
        """Main sync loop."""
        while self._running:
            try:
                await self._run_syncs()
            except Exception as e:
                print(f"Sync scheduler error: {e}")
            await asyncio.sleep(self._sync_interval)

    async def _run_syncs(self):
        """Run syncs for all active supplier connections."""
        async with async_session_factory() as session:
            # Get all active supplier connections
            stmt = select(SupplierConnection).where(
                SupplierConnection.is_active == True,
            )
            result = await session.execute(stmt)
            connections = result.scalars().all()

        if not connections:
            return

        # Map supplier types to their adapters
        supplier_adapters = {
            "aliexpress": None,  # Will be initialized
            "dsers": None,
            "cjdropshipping": None,
        }

        for connection in connections:
            # Initialize supplier adapter
            if connection.supplier_type not in supplier_adapters or not supplier_adapters[connection.supplier_type]:
                if connection.supplier_type == "aliexpress":
                    from backend.services.aliexpress_supplier import AliExpressSupplier
                    supplier_adapters[connection.supplier_type] = AliExpressSupplier()
                elif connection.supplier_type == "dsers":
                    from backend.services.aliexpress_supplier import DSersSupplier
                    supplier_adapters[connection.supplier_type] = DSersSupplier()
                elif connection.supplier_type == "cjdropshipping":
                    from backend.services.cjdropshipping_supplier import CJDropshippingSupplier
                    supplier_adapters[connection.supplier_type] = CJDropshippingSupplier()

            supplier = supplier_adapters[connection.supplier_type]
            if not supplier:
                continue

            # Create sync engine and run sync
            engine = SyncEngine(supplier)
            await engine.sync_full(connection.connection_id)
