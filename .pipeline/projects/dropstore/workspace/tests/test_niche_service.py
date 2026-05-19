"""Tests for niche service."""

import pytest
from backend.services.niche_service import list_niches, get_niche, list_categories, seed_niches


@pytest.mark.asyncio
async def test_list_niches():
    """Test listing niches."""
    niches = await list_niches()
    assert len(niches) > 0
    assert hasattr(niches[0], 'niche_id')
    assert hasattr(niches[0], 'name')


@pytest.mark.asyncio
async def test_get_niche():
    """Test getting a specific niche."""
    niches = await list_niches()
    niche = await get_niche(niches[0].niche_id)
    assert niche is not None
    assert niche.niche_id == niches[0].niche_id


@pytest.mark.asyncio
async def test_list_categories():
    """Test listing categories."""
    categories = await list_categories()
    assert len(categories) > 0


@pytest.mark.asyncio
async def test_seed_niches():
    """Test seeding niches."""
    count = await seed_niches()
    assert count > 0
