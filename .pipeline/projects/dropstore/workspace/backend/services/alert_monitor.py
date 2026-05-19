"""Alert monitor for periodic alert generation and dispatch."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone

from backend.services.alert_service import AlertService
from backend.services.supplier_base import SupplierBase
from backend.models.alert import Alert
from backend.utils.database import async_session_factory
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitors system state and generates alerts periodically."""

    def __init__(self, alert_service: Optional[AlertService] = None):
        self.alert_service = alert_service or AlertService()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._interval_seconds: int = 300  # Default: check every 5 minutes

    async def start(self, interval_seconds: int = 300):
        """Start the alert monitor loop.

        Args:
            interval_seconds: How often to check for alerts.
        """
        self._interval_seconds = interval_seconds
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Alert monitor started with interval %ds", interval_seconds)

    async def stop(self):
        """Stop the alert monitor loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Alert monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_all_alerts()
            except Exception:
                logger.exception("Error in alert monitor loop")
            await asyncio.sleep(self._interval_seconds)

    async def _check_all_alerts(self):
        """Run all alert checks."""
        # Check low stock alerts
        await self._check_low_stock()

        # Check sync failure alerts
        await self._check_sync_failures()

        # Check price change alerts
        await self._check_price_changes()

    async def _check_low_stock(self):
        """Check for low stock alerts across all catalogs."""
        async with async_session_factory() as session:
            from backend.models.product import Catalog
            result = await session.execute(select(Catalog))
            catalogs = result.scalars().all()

        for catalog in catalogs:
            alerts = await self.alert_service.generate_low_stock_alerts(catalog.catalog_id)
            if alerts:
                await self._store_alerts(alerts)
                logger.info("Generated %d low stock alerts for catalog %s", len(alerts), catalog.catalog_id)

    async def _check_sync_failures(self):
        """Check for recent sync failures."""
        async with async_session_factory() as session:
            from backend.models.sync_log import SyncLog
            # Get sync logs from the last hour that failed
            one_hour_ago = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            stmt = (
                select(SyncLog)
                .where(
                    SyncLog.status == "failed",
                    SyncLog.started_at >= one_hour_ago,
                )
            )
            result = await session.execute(stmt)
            failed_logs = result.scalars().all()

        for log in failed_logs:
            alerts = await self.alert_service.generate_sync_failure_alerts(log)
            if alerts:
                await self._store_alerts(alerts)
                logger.info("Generated %d sync failure alerts for log %s", len(alerts), log.log_id)

    async def _check_price_changes(self):
        """Check for significant price changes."""
        # In a real implementation, this would compare current prices with previous prices
        # For now, this is a placeholder for future implementation
        pass

    async def _store_alerts(self, alerts: List[Alert]):
        """Store generated alerts in the database."""
        if not alerts:
            return

        async with async_session_factory() as session:
            for alert in alerts:
                session.add(alert)
            await session.commit()

    async def check_now(self):
        """Run all alert checks immediately (for testing/on-demand)."""
        await self._check_all_alerts()

    @property
    def is_running(self) -> bool:
        """Check if the monitor is currently running."""
        return self._running
