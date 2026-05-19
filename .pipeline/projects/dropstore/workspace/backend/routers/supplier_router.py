"""Supplier management router."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from backend.services.supplier_import_service import SupplierImportService
from backend.services.aliexpress_supplier import AliExpressSupplier, DSersSupplier
from backend.services.cjdropshipping_supplier import CJDropshippingSupplier
from backend.models.supplier import SupplierConnection
from backend.utils.database import async_session_factory
from shared.schemas import ProductDetail

router = APIRouter()


@router.get("/suppliers", response_model=list[dict])
async def list_suppliers():
    """List all supplier connections."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(SupplierConnection))
        connections = result.scalars().all()
        return [
            {
                "connection_id": c.connection_id,
                "supplier_type": c.supplier_type,
                "name": c.name,
                "status": c.status,
            }
            for c in connections
        ]


@router.post("/suppliers/{connection_id}/import", response_model=dict)
async def import_products(
    connection_id: str,
    category: Optional[str] = Query(None),
    min_margin_pct: float = Query(0.0),
    max_results: int = Query(50, le=200),
):
    """Import products from a supplier connection."""
    # Get the connection
    async with async_session_factory() as session:
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == connection_id)
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

    # Import products
    import_service = SupplierImportService(supplier)
    results = await import_service.import_products(
        supplier_connection_id=connection_id,
        category=category,
        min_margin_pct=min_margin_pct,
        max_results=max_results,
    )
    return results


@router.get("/suppliers/{connection_id}/products", response_model=list[ProductDetail])
async def get_supplier_products(
    connection_id: str,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """Get products imported from a supplier connection."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == connection_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Supplier connection not found")

    import_service = SupplierImportService(
        AliExpressSupplier() if connection.supplier_type == "aliexpress" else CJDropshippingSupplier()
    )
    products = await import_service.get_imported_products(
        supplier_connection_id=connection_id,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "product_id": p.product_id,
            "title": p.title,
            "image_url": p.image_url or "",
            "estimated_cost": p.landed_cost,
            "suggested_retail": p.retail_price,
            "margin_pct": p.margin_pct,
            "category": p.category or "",
            "supplier": connection.supplier_type,
            "niche_id": p.niche_id or "",
            "optimized_title": p.title,
            "variants": p.variants or [],
            "demand_score": 0.0,
            "supply_score": 0.0,
        }
        for p in products
    ]


@router.get("/suppliers/{connection_id}/stats", response_model=dict)
async def get_supplier_stats(connection_id: str):
    """Get statistics for a supplier connection."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(SupplierConnection).where(SupplierConnection.connection_id == connection_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Supplier connection not found")

    import_service = SupplierImportService(AliExpressSupplier())
    count = await import_service.get_product_count(connection_id)

    return {
        "connection_id": connection_id,
        "supplier_type": connection.supplier_type,
        "product_count": count,
        "status": connection.status,
    }
