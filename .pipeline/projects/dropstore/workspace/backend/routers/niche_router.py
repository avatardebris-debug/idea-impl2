"""Niche discovery router."""

from fastapi import APIRouter, HTTPException
from backend.services import niche_service
from shared.schemas import NicheScore, NicheCategory

router = APIRouter()


@router.get("/niches", response_model=list[NicheScore])
async def list_niches(category: str = None):
    """List niches, optionally filtered by category."""
    niches = await niche_service.list_niches(category)
    return niches


@router.get("/niches/{niche_id}", response_model=NicheScore)
async def get_niche(niche_id: str):
    """Get a specific niche."""
    niche = await niche_service.get_niche(niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    return niche


@router.get("/niches/categories", response_model=list[NicheCategory])
async def list_categories():
    """List all niche categories."""
    return await niche_service.list_categories()


@router.post("/niches/{niche_id}/products", response_model=list[dict])
async def find_products(niche_id: str):
    """Find products for a niche."""
    products = await niche_service.find_products_for_niche(niche_id)
    return products
