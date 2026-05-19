"""Shopify integration router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from backend.services import shopify_service
from shared.schemas import ShopifyStore, SyncJob

router = APIRouter()


class ConnectRequest(BaseModel):
    store_name: str
    domain: str
    access_token: str


class ProductIdsRequest(BaseModel):
    product_ids: List[str]


@router.post("/shopify/connect", response_model=ShopifyStore)
async def connect_shopify(request: ConnectRequest):
    """Connect a new Shopify store."""
    store = await shopify_service.create_shopify_store(
        store_name=request.store_name,
        domain=request.domain,
        access_token=request.access_token,
    )
    return store


@router.get("/shopify/stores", response_model=list[ShopifyStore])
async def list_stores():
    """List all connected Shopify stores."""
    stores = await shopify_service.list_shopify_stores()
    return stores


@router.get("/shopify/stores/{store_id}", response_model=ShopifyStore)
async def get_store(store_id: str):
    """Get a specific Shopify store."""
    store = await shopify_service.get_shopify_store_by_id(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.delete("/shopify/stores/{store_id}")
async def disconnect_store(store_id: str):
    """Disconnect a Shopify store."""
    success = await shopify_service.delete_shopify_store(store_id)
    if not success:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"success": True}


@router.post("/shopify/stores/{store_id}/sync", response_model=SyncJob)
async def sync_products(store_id: str, request: ProductIdsRequest):
    """Sync products to a Shopify store."""
    result = await shopify_service.sync_products_to_shopify(store_id, request.product_ids)
    return result
