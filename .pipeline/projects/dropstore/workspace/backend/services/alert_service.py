"""Alert service for generating and managing notifications."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from backend.models.alert import Alert
from backend.models.product import CatalogProduct
from backend.models.sync_log import SyncLog
from backend.config import settings
from backend.utils.database import async_session_factory
from sqlalchemy import select


class AlertService:
    """Service for generating and managing alerts."""

    @staticmethod
    async def generate_low_stock_alerts(catalog_id: str) -> List[Alert]:
        """Generate alerts for low stock products.

        Args:
            catalog_id: The catalog ID to check.

        Returns:
            List of generated alerts.
        """
        alerts = []

        async with async_session_factory() as session:
            stmt = select(CatalogProduct).where(
                CatalogProduct.catalog_id == catalog_id,
                CatalogProduct.inventory < settings.low_stock_threshold,
                CatalogProduct.inventory > 0,
            )
            result = await session.execute(stmt)
            low_stock_products = result.scalars().all()

        for product in low_stock_products:
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type="low_stock",
                severity="warning" if product.inventory > 5 else "critical",
                title=f"Low Stock: {product.title}",
                message=f"Product '{product.title}' has only {product.inventory} units in stock.",
                product_id=product.supplier_product_id,
                is_read=False,
                is_dismissed=False,
                action_suggestion=f"Consider reordering or finding an alternative supplier for '{product.title}'.",
                metadata={"inventory": product.inventory, "threshold": settings.low_stock_threshold},
                created_at=datetime.now(timezone.utc),
            )
            alerts.append(alert)

        return alerts

    @staticmethod
    async def generate_sync_failure_alerts(sync_log: SyncLog) -> List[Alert]:
        """Generate alerts for sync failures.

        Args:
            sync_log: The sync log to check.

        Returns:
            List of generated alerts.
        """
        alerts = []

        if sync_log.status == "failed":
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type="sync_failure",
                severity="critical",
                title=f"Sync Failed: {sync_log.sync_type} sync failed",
                message=f"Sync log {sync_log.log_id} failed with {sync_log.products_failed} errors.",
                supplier_id=sync_log.supplier_id,
                is_read=False,
                is_dismissed=False,
                action_suggestion="Check supplier API status and retry the sync.",
                metadata={
                    "sync_log_id": sync_log.log_id,
                    "sync_type": sync_log.sync_type,
                    "products_failed": sync_log.products_failed,
                    "error_messages": sync_log.error_messages,
                },
                created_at=datetime.now(timezone.utc),
            )
            alerts.append(alert)

        return alerts

    @staticmethod
    async def generate_price_change_alerts(catalog_id: str, threshold_pct: Optional[float] = None) -> List[Alert]:
        """Generate alerts for significant price changes.

        Args:
            catalog_id: The catalog ID to check.
            threshold_pct: Price change threshold percentage. Uses config default if None.

        Returns:
            List of generated alerts.
        """
        alerts = []
        threshold = threshold_pct or settings.price_change_threshold_pct

        # In a real implementation, this would compare current prices with previous prices
        # For now, return empty list as we don't have historical data
        return alerts

    async def get_user_alerts(
        self,
        user_id: str,
        is_read: Optional[bool] = None,
        alert_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """Get alerts for a user.

        Args:
            user_id: The user ID.
            is_read: Filter by read status.
            alert_type: Filter by alert type.
            limit: Maximum number of alerts to return.

        Returns:
            List of alerts.
        """
        async with async_session_factory() as session:
            stmt = select(Alert).where(
                Alert.is_dismissed == False,
            )
            if is_read is not None:
                stmt = stmt.where(Alert.is_read == is_read)
            if alert_type:
                stmt = stmt.where(Alert.alert_type == alert_type)
            stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def mark_alert_as_read(self, alert_id: str) -> bool:
        """Mark an alert as read.

        Args:
            alert_id: The alert ID.

        Returns:
            True if the alert was found and marked as read.
        """
        async with async_session_factory() as session:
            stmt = select(Alert).where(Alert.alert_id == alert_id)
            result = await session.execute(stmt)
            alert = result.scalar_one_or_none()

            if alert:
                alert.is_read = True
                await session.commit()
                return True
            return False

    async def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert.

        Args:
            alert_id: The alert ID.

        Returns:
            True if the alert was found and dismissed.
        """
        async with async_session_factory() as session:
            stmt = select(Alert).where(Alert.alert_id == alert_id)
            result = await session.execute(stmt)
            alert = result.scalar_one_or_none()

            if alert:
                alert.is_dismissed = True
                await session.commit()
                return True
            return False

    async def get_unread_count(self, user_id: str) -> int:
        """Get the count of unread alerts for a user.

        Args:
            user_id: The user ID.

        Returns:
            Count of unread alerts.
        """
        async with async_session_factory() as session:
            stmt = select(Alert).where(
                Alert.is_read == False,
                Alert.is_dismissed == False,
            )
            result = await session.execute(stmt)
            return len(list(result.scalars().all()))
