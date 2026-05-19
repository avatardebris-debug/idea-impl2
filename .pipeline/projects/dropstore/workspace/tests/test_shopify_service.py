"""Tests for Shopify service."""

import pytest
from backend.services.shopify_service import create_shopify_store, get_shopify_store


@pytest.mark.asyncio
async def test_create_shopify_store():
    """Test creating a Shopify store connection."""
    store = await create_shopify_store(
        store_name="Test Store",
        domain="test-store.myshopify.com",
        access_token="test_token_123",
    )
    assert store is not None
    assert store.shop_domain == "test-store.myshopify.com"


@pytest.mark.asyncio
async def test_get_shopify_store():
    """Test getting a Shopify store."""
    store = await create_shopify_store(
        store_name="Test Store 2",
        domain="test-store-2.myshopify.com",
        access_token="test_token_456",
    )
    retrieved = await get_shopify_store("test-store-2.myshopify.com")
    assert retrieved is not None
    assert retrieved.store_id == store.store_id
