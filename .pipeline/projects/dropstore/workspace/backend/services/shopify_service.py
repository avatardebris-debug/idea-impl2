"""Shopify integration service."""

import hashlib
import base64
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from backend.models.product import ShopifyStore
from backend.utils.database import async_session_factory


# Simple symmetric encryption for demo (NOT production-grade)
def _encrypt_token(token: str) -> str:
    """Simple XOR-based obfuscation for demo purposes."""
    key = "dropstore-secret-key-2024"
    encrypted = bytearray()
    for i, c in enumerate(token):
        encrypted.append(ord(c) ^ ord(key[i % len(key)]))
    return base64.b64encode(bytes(encrypted)).decode()


def _decrypt_token(encrypted: str) -> str:
    """Decrypt the obfuscated token."""
    key = "dropstore-secret-key-2024"
    decrypted = bytearray(base64.b64decode(encrypted))
    for i, c in enumerate(decrypted):
        decrypted[i] = c ^ ord(key[i % len(key)])
    return decrypted.decode()


async def create_shopify_store(
    store_name: str,
    domain: str,
    access_token: str,
    api_version: str = "2024-01"
) -> ShopifyStore:
    """Create a new Shopify store connection."""
    store_id = f"shop_{hashlib.md5(domain.encode()).hexdigest()[:8]}"
    
    store = ShopifyStore(
        store_id=store_id,
        shop_name=store_name,
        shop_domain=domain,
        access_token=_encrypt_token(access_token),
        status="connected",
    )
    
    async with async_session_factory() as session:
        session.add(store)
        await session.commit()
        await session.refresh(store)
        return store


async def get_shopify_store(domain: str) -> Optional[ShopifyStore]:
    """Get a Shopify store by domain."""
    from sqlalchemy import select
    async with async_session_factory() as session:
        result = await session.execute(
            select(ShopifyStore).where(ShopifyStore.shop_domain == domain)
        )
        return result.scalar_one_or_none()


async def get_shopify_store_by_id(store_id: str) -> Optional[ShopifyStore]:
    """Get a Shopify store by ID."""
    async with async_session_factory() as session:
        result = await session.execute(
            ShopifyStore.__table__.select().where(ShopifyStore.store_id == store_id)
        )
        return result.scalar_one_or_none()


async def list_shopify_stores() -> List[ShopifyStore]:
    """List all Shopify stores."""
    async with async_session_factory() as session:
        result = await session.execute(ShopifyStore.__table__.select())
        return list(result.scalars().all())


async def delete_shopify_store(store_id: str) -> bool:
    """Delete a Shopify store connection."""
    async with async_session_factory() as session:
        store = await get_shopify_store_by_id(store_id)
        if not store:
            return False
        await session.execute(
            ShopifyStore.__table__.delete().where(ShopifyStore.store_id == store_id)
        )
        await session.commit()
        return True


async def sync_products_to_shopify(
    store_id: str,
    product_ids: List[str]
) -> dict:
    """Sync products to a Shopify store (mock)."""
    store = await get_shopify_store_by_id(store_id)
    if not store:
        raise ValueError(f"Store {store_id} not found")
    
    # Generate a mock sync job
    job_id = f"sync_{uuid.uuid4().hex[:8]}"
    
    # Simulate sync results
    products_pushed = len(product_ids)
    products_failed = 0
    error_messages = []
    
    # Create a SyncJob-like dict
    sync_job = {
        "job_id": job_id,
        "store_id": store_id,
        "status": "success",
        "products_pushed": products_pushed,
        "products_failed": products_failed,
        "total_products": len(product_ids),
        "error_messages": error_messages,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return sync_job
