"""Sync management router."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from backend.services.sync_engine import SyncEngine
from backend.services.sync_scheduler import SyncScheduler
from backend.services.supplier_base import SupplierBase
from backend.services.aliexpress_supplier import AliExpressSupplier, DSersSupplier
from backend.services.cjdropshipping_supplier import CJDropshippingSupplier
from backend.models.supplier import SupplierConnection
from backend.models.sync_log import SyncLog
from backend.utils.database import async_session_factory
from shared.schemas import SyncJob

router = APIRouter()


@router.get("/sync/logs", response_model=list[dict])
async def list_sync_logs(
    supplier_id: Optional[str] = Query(None),
    sync_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List sync logs with optional filters."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        stmt = select(SyncLog)
        if supplier_id:
            stmt = stmt.where(SyncLog.supplier_id == supplier_id)
        if sync_type:
            stmt = stmt.where(SyncLog.sync_type == sync_type)
        if status:
            stmt = stmt.where(SyncLog.status == status)
        stmt = stmt.order_by(SyncLog.started_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        logs = result.scalars().all()

    return [
        {
            "log_id": log.log_id,
            "supplier_id": log.supplier_id,
            "sync_type": log.sync_type,
            "status": log.status,
            "products_updated": log.products_updated,
            "products_failed": log.products_failed,
            "products_skipped": log.products_skipped,
            "error_messages": log.error_messages,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": log.duration_seconds,
        }
        for log in logs
    ]


@router.get("/sync/logs/{log_id}", response_model=dict)
async def get_sync_log(log_id: str):
    """Get a specific sync log."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(SyncLog).where(SyncLog.log_id == log_id))
        log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Sync log not found")

    return {
        "log_id": log.log_id,
        "supplier_id": log.supplier_id,
        "sync_type": log.sync_type,
        "status": log.status,
        "products_updated": log.products_updated,
        "products_failed": log.products_failed,
        "products_skipped": log.products_skipped,
        "error_messages": log.error_messages,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        "duration_seconds": log.duration_seconds,
    }


@router.post("/sync/{supplier_id}/price", response_model=dict)
async def sync_prices(supplier_id: str):
    """Trigger a price sync for a supplier."""
    # Get the supplier connection
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == supplier_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Supplier connection not found")

    # Create supplier adapter
    if connection.supplier_type == "aliexpress":
        supplier = AliExpressSupplier()
    elif connection.supplier_type == "dsers":
        supplier = DSersSupplier()
    elif connection.supplier_type == "cjdropshipping":
        supplier = CJDropshippingSupplier()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported supplier type: {connection.supplier_type}")

    # Run sync
    engine = SyncEngine(supplier)
    log = await engine.sync_prices(supplier_id)

    return {
        "log_id": log.log_id,
        "status": log.status,
        "products_updated": log.products_updated,
        "products_failed": log.products_failed,
    }


@router.post("/sync/{supplier_id}/inventory", response_model=dict)
async def sync_inventory(supplier_id: str):
    """Trigger an inventory sync for a supplier."""
    # Get the supplier connection
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == supplier_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Supplier connection not found")

    # Create supplier adapter
    if connection.supplier_type == "aliexpress":
        supplier = AliExpressSupplier()
    elif connection.supplier_type == "dsers":
        supplier = DSersSupplier()
    elif connection.supplier_type == "cjdropshipping":
        supplier = CJDropshippingSupplier()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported supplier type: {connection.supplier_type}")

    # Run sync
    engine = SyncEngine(supplier)
    log = await engine.sync_inventory(supplier_id)

    return {
        "log_id": log.log_id,
        "status": log.status,
        "products_updated": log.products_updated,
        "products_failed": log.products_failed,
    }


@router.post("/sync/{supplier_id}/full", response_model=dict)
async def sync_full(supplier_id: str):
    """Trigger a full sync (price + inventory) for a supplier."""
    # Get the supplier connection
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == supplier_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Supplier connection not found")

    # Create supplier adapter
    if connection.supplier_type == "aliexpress":
        supplier = AliExpressSupplier()
    elif connection.supplier_type == "dsers":
        supplier = DSersSupplier()
    elif connection.supplier_type == "cjdropshipping":
        supplier = CJDropshippingSupplier()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported supplier type: {connection.supplier_type}")

    # Run sync
    engine = SyncEngine(supplier)
    log = await engine.sync_full(supplier_id)

    return {
        "log_id": log.log_id,
        "status": log.status,
        "products_updated": log.products_updated,
        "products_failed": log.products_failed,
    }


@router.post("/sync/schedule", response_model=dict)
async def schedule_sync(
    supplier_id: str,
    interval_hours: int = Query(6, ge=1, le=168),
):
    """Schedule automatic sync for a supplier."""
    scheduler = SyncScheduler()
    await scheduler.schedule_sync(supplier_id, interval_hours)

    return {
        "supplier_id": supplier_id,
        "interval_hours": interval_hours,
        "status": "scheduled",
    }


@router.delete("/sync/schedule/{supplier_id}", response_model=dict)
async def unschedule_sync(supplier_id: str):
    """Remove automatic sync schedule for a supplier."""
    scheduler = SyncScheduler()
    await scheduler.remove_sync_schedule(supplier_id)

    return {
        "supplier_id": supplier_id,
        "status": "unscheduled",
    }


@router.get("/sync/schedules", response_model=list[dict])
async def list_sync_schedules():
    """List all active sync schedules."""
    scheduler = SyncScheduler()
    schedules = scheduler.get_active_schedules()

    return [
        {
            "supplier_id": s["supplier_id"],
            "interval_hours": s["interval_hours"],
            "next_run": s["next_run"].isoformat() if s["next_run"] else None,
            "status": "active",
        }
        for s in schedules
    ]
