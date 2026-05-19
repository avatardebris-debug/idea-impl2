"""Sync service for product synchronization between suppliers and stores."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.sync_log import SyncLog
from backend.utils.database import async_session_factory


def _generate_sync_id() -> str:
    """Generate a unique sync ID."""
    return f"sync_{uuid.uuid4().hex[:12]}"


async def create_sync_log(
    store_id: str,
    supplier_id: Optional[str] = None,
    sync_type: str = "full",
    status: str = "pending",
    products_count: int = 0,
    products_pushed: int = 0,
    products_failed: int = 0,
    errors: Optional[List[str]] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
) -> SyncLog:
    """Create a new sync log entry."""
    sync_id = _generate_sync_id()

    sync_log = SyncLog(
        sync_id=sync_id,
        store_id=store_id,
        supplier_id=supplier_id or "",
        sync_type=sync_type,
        status=status,
        products_count=products_count,
        products_pushed=products_pushed,
        products_failed=products_failed,
        errors=errors or [],
        started_at=started_at or datetime.now(timezone.utc),
        completed_at=completed_at,
    )

    async with async_session_factory() as session:
        session.add(sync_log)
        await session.commit()
        await session.refresh(sync_log)
    return sync_log


async def get_sync_log(sync_id: str) -> Optional[SyncLog]:
    """Get a sync log by ID."""
    async with async_session_factory() as session:
        sync_log = await session.get(SyncLog, sync_id)
        return sync_log


async def list_sync_logs(
    store_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[SyncLog]:
    """List sync logs with optional filters."""
    async with async_session_factory() as session:
        query = SyncLog.__table__.select()
        if store_id:
            query = query.where(SyncLog.store_id == store_id)
        if status:
            query = query.where(SyncLog.status == status)
        query = query.order_by(SyncLog.started_at.desc()).limit(limit)
        sync_logs = await session.execute(query)
        return list(sync_logs.scalars().all())


async def update_sync_log_status(sync_id: str, status: str, **kwargs) -> Optional[SyncLog]:
    """Update sync log status and details."""
    async with async_session_factory() as session:
        sync_log = await session.get(SyncLog, sync_id)
        if sync_log:
            sync_log.status = status
            for key, value in kwargs.items():
                if hasattr(sync_log, key):
                    setattr(sync_log, key, value)
            if status == "completed":
                sync_log.completed_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(sync_log)
        return sync_log


async def get_sync_stats(store_id: str, days: int = 30) -> Dict[str, Any]:
    """Get sync statistics for a store."""
    async with async_session_factory() as session:
        cutoff_date = datetime.now(timezone.utc)
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)

        sync_logs = await session.execute(
            SyncLog.__table__.select().where(
                (SyncLog.store_id == store_id) &
                (SyncLog.started_at >= cutoff_date)
            )
        )
        logs = list(sync_logs.scalars().all())

        if not logs:
            return {
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "total_products_pushed": 0,
                "total_products_failed": 0,
                "avg_products_per_sync": 0.0,
            }

        total_syncs = len(logs)
        successful_syncs = sum(1 for log in logs if log.status == "completed")
        failed_syncs = sum(1 for log in logs if log.status == "failed")
        total_products_pushed = sum(log.products_pushed for log in logs)
        total_products_failed = sum(log.products_failed for log in logs)
        avg_products_per_sync = total_products_pushed / total_syncs if total_syncs > 0 else 0.0

        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "total_products_pushed": total_products_pushed,
            "total_products_failed": total_products_failed,
            "avg_products_per_sync": avg_products_per_sync,
        }
