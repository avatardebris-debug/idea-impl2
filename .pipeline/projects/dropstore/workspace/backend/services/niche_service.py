"""Niche discovery and validation service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.niche import Niche, NicheProduct
from backend.utils.database import async_session_factory


def _generate_niche_id() -> str:
    """Generate a unique niche ID."""
    return f"niche_{uuid.uuid4().hex[:12]}"


def _generate_niche_product_id() -> str:
    """Generate a unique niche product ID."""
    return f"niche_prod_{uuid.uuid4().hex[:12]}"


async def create_niche(
    name: str,
    description: str = "",
    target_audience: str = "",
    competition_level: str = "unknown",
    growth_potential: str = "unknown",
    estimated_market_size: str = "",
    is_active: bool = True,
) -> Niche:
    """Create a new niche."""
    niche_id = _generate_niche_id()

    niche = Niche(
        niche_id=niche_id,
        name=name,
        description=description,
        target_audience=target_audience,
        competition_level=competition_level,
        growth_potential=growth_potential,
        estimated_market_size=estimated_market_size,
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(niche)
        await session.commit()
        await session.refresh(niche)
    return niche


async def get_niche(niche_id: str) -> Optional[Niche]:
    """Get a niche by ID."""
    async with async_session_factory() as session:
        niche = await session.get(Niche, niche_id)
        return niche


async def list_niches(
    competition_level: Optional[str] = None,
    growth_potential: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
) -> List[Niche]:
    """List niches with optional filters."""
    async with async_session_factory() as session:
        query = Niche.__table__.select()
        if competition_level:
            query = query.where(Niche.competition_level == competition_level)
        if growth_potential:
            query = query.where(Niche.growth_potential == growth_potential)
        if is_active is not None:
            query = query.where(Niche.is_active == is_active)
        query = query.order_by(Niche.name).limit(limit)
        niches = await session.execute(query)
        return list(niches.scalars().all())


async def update_niche(niche_id: str, **kwargs) -> Optional[Niche]:
    """Update niche information."""
    async with async_session_factory() as session:
        niche = await session.get(Niche, niche_id)
        if niche:
            for key, value in kwargs.items():
                if hasattr(niche, key):
                    setattr(niche, key, value)
            await session.commit()
            await session.refresh(niche)
        return niche


async def create_niche_product(
    niche_id: str,
    product_id: str,
    product_title: str,
    price: float,
    estimated_profit: float = 0.0,
    estimated_sales_volume: int = 0,
    competition_score: float = 0.0,
    demand_score: float = 0.0,
    is_active: bool = True,
) -> NicheProduct:
    """Create a new niche product."""
    product_entry_id = _generate_niche_product_id()

    product_entry = NicheProduct(
        product_id=product_entry_id,
        niche_id=niche_id,
        product_id=product_id,
        product_title=product_title,
        price=price,
        estimated_profit=estimated_profit,
        estimated_sales_volume=estimated_sales_volume,
        competition_score=competition_score,
        demand_score=demand_score,
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(product_entry)
        await session.commit()
        await session.refresh(product_entry)
    return product_entry


async def get_niche_product(product_id: str) -> Optional[NicheProduct]:
    """Get a niche product by ID."""
    async with async_session_factory() as session:
        product = await session.get(NicheProduct, product_id)
        return product


async def list_niche_products(
    niche_id: Optional[str] = None,
    min_demand_score: Optional[float] = None,
    max_competition_score: Optional[float] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
) -> List[NicheProduct]:
    """List niche products with optional filters."""
    async with async_session_factory() as session:
        query = NicheProduct.__table__.select()
        if niche_id:
            query = query.where(NicheProduct.niche_id == niche_id)
        if min_demand_score is not None:
            query = query.where(NicheProduct.demand_score >= min_demand_score)
        if max_competition_score is not None:
            query = query.where(NicheProduct.competition_score <= max_competition_score)
        if is_active is not None:
            query = query.where(NicheProduct.is_active == is_active)
        query = query.order_by(NicheProduct.demand_score.desc(), NicheProduct.competition_score.asc()).limit(limit)
        products = await session.execute(query)
        return list(products.scalars().all())


async def update_niche_product(product_id: str, **kwargs) -> Optional[NicheProduct]:
    """Update niche product information."""
    async with async_session_factory() as session:
        product = await session.get(NicheProduct, product_id)
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            await session.commit()
            await session.refresh(product)
        return product


async def get_niche_stats(niche_id: str) -> Dict[str, Any]:
    """Get statistics for a niche."""
    async with async_session_factory() as session:
        products = await session.execute(
            NicheProduct.__table__.select().where(NicheProduct.niche_id == niche_id)
        )
        product_list = list(products.scalars().all())

        if not product_list:
            return {
                "total_products": 0,
                "avg_price": 0.0,
                "avg_profit": 0.0,
                "avg_demand_score": 0.0,
                "avg_competition_score": 0.0,
                "total_estimated_sales": 0,
            }

        total_products = len(product_list)
        avg_price = sum(p.price for p in product_list) / total_products
        avg_profit = sum(p.estimated_profit for p in product_list) / total_products
        avg_demand_score = sum(p.demand_score for p in product_list) / total_products
        avg_competition_score = sum(p.competition_score for p in product_list) / total_products
        total_estimated_sales = sum(p.estimated_sales_volume for p in product_list)

        return {
            "total_products": total_products,
            "avg_price": avg_price,
            "avg_profit": avg_profit,
            "avg_demand_score": avg_demand_score,
            "avg_competition_score": avg_competition_score,
            "total_estimated_sales": total_estimated_sales,
        }
