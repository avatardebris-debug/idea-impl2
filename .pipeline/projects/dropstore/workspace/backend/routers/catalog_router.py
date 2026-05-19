"""Product catalog router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from backend.services import catalog_service, product_service
from shared.schemas import ProductSuggestion, CatalogSummary

router = APIRouter()


class ProductIdsRequest(BaseModel):
    product_ids: List[str]


class CreateCatalogRequest(BaseModel):
    niche_id: str
    niche_name: str


@router.get("/catalogs", response_model=list[dict])
async def list_catalogs():
    """List all user catalogs."""
    # In real impl, this would be user-scoped
    return []


@router.post("/catalogs", response_model=dict)
async def create_catalog(request: CreateCatalogRequest):
    """Create a new catalog for a niche."""
    catalog = await catalog_service.create_catalog(request.niche_id, request.niche_name)
    return {
        "catalog_id": catalog.catalog_id,
        "niche_id": catalog.niche_id,
        "niche_name": catalog.niche_name,
    }


@router.post("/catalogs/{catalog_id}/products", response_model=dict)
async def add_products(catalog_id: str, request: ProductIdsRequest):
    """Add products to a catalog."""
    products = []
    for pid in request.product_ids:
        p = await product_service.get_product_by_id(pid)
        if p:
            products.append(p)

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    catalog_products = await catalog_service.add_products_to_catalog(catalog_id, products)
    return {"added": len(catalog_products)}


@router.get("/catalogs/{catalog_id}", response_model=dict)
async def get_catalog(catalog_id: str):
    """Get catalog details."""
    catalog = await catalog_service.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return {
        "catalog_id": catalog.catalog_id,
        "niche_id": catalog.niche_id,
        "niche_name": catalog.niche_name,
    }


@router.get("/catalogs/{catalog_id}/products", response_model=list[ProductSuggestion])
async def get_catalog_products(catalog_id: str):
    """Get products in a catalog."""
    products = await catalog_service.get_catalog_products(catalog_id)
    return products


@router.delete("/catalogs/{catalog_id}/products/{product_id}")
async def remove_product(catalog_id: str, product_id: str):
    """Remove a product from catalog."""
    success = await catalog_service.remove_product_from_catalog(catalog_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not in catalog")
    return {"success": True}


@router.get("/catalogs/{catalog_id}/stats", response_model=CatalogSummary)
async def get_catalog_stats(catalog_id: str):
    """Get catalog statistics."""
    stats = await catalog_service.get_catalog_stats(catalog_id)
    return stats
