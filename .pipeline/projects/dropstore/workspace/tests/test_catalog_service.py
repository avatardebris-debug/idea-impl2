"""Tests for catalog service."""

import pytest
from backend.services.catalog_service import create_catalog, get_catalog, get_catalog_stats


@pytest.mark.asyncio
async def test_create_catalog():
    """Test creating a catalog."""
    catalog = await create_catalog("niche_1", "Test Niche")
    assert catalog is not None
    assert catalog.niche_id == "niche_1"


@pytest.mark.asyncio
async def test_get_catalog():
    """Test getting a catalog."""
    catalog = await create_catalog("niche_2", "Test Niche 2")
    retrieved = await get_catalog(catalog.catalog_id)
    assert retrieved is not None
    assert retrieved.catalog_id == catalog.catalog_id


@pytest.mark.asyncio
async def test_get_catalog_stats_empty():
    """Test stats for empty catalog."""
    catalog = await create_catalog("niche_3", "Test Niche 3")
    stats = await get_catalog_stats(catalog.catalog_id)
    assert stats["total_products"] == 0
