"""Margin optimization router."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from backend.services.margin_optimizer import MarginOptimizer, MarginApplyResult
from backend.models.margin_rule import MarginRule
from backend.utils.database import async_session_factory
from shared.schemas import CatalogSummary

router = APIRouter()


class CreateMarginRuleRequest(BaseModel):
    name: str
    description: str = ""
    markup_pct: float
    min_margin_pct: float = 0.0
    max_margin_pct: float = 200.0
    price_rounding: str = "none"
    applies_to_all: bool = False
    niche_filter: List[str] = []
    category_filter: List[str] = []


class UpdateMarginRuleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    markup_pct: Optional[float] = None
    min_margin_pct: Optional[float] = None
    max_margin_pct: Optional[float] = None
    price_rounding: Optional[str] = None
    is_active: Optional[bool] = None
    applies_to_all: Optional[bool] = None
    niche_filter: Optional[List[str]] = None
    category_filter: Optional[List[str]] = None


class ApplyRulesRequest(BaseModel):
    rule_ids: Optional[List[str]] = None


class RecommendedPriceRequest(BaseModel):
    landed_cost: float
    min_margin_pct: float = 0.0
    max_margin_pct: float = 100.0
    rounding: str = ".99"


@router.get("/margin/rules", response_model=list[dict])
async def list_margin_rules():
    """List all margin rules."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(MarginRule).order_by(MarginRule.created_at.desc()))
        rules = result.scalars().all()

    return [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "markup_pct": r.markup_pct,
            "min_margin_pct": r.min_margin_pct,
            "max_margin_pct": r.max_margin_pct,
            "price_rounding": r.price_rounding,
            "is_active": r.is_active,
            "applies_to_all": r.applies_to_all,
            "niche_filter": r.niche_filter,
            "category_filter": r.category_filter,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rules
    ]


@router.get("/margin/rules/{rule_id}", response_model=dict)
async def get_margin_rule(rule_id: str):
    """Get a specific margin rule."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(MarginRule).where(MarginRule.rule_id == rule_id))
        rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Margin rule not found")

    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "markup_pct": rule.markup_pct,
        "min_margin_pct": rule.min_margin_pct,
        "max_margin_pct": rule.max_margin_pct,
        "price_rounding": rule.price_rounding,
        "is_active": rule.is_active,
        "applies_to_all": rule.applies_to_all,
        "niche_filter": rule.niche_filter,
        "category_filter": rule.category_filter,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


@router.post("/margin/rules", response_model=dict)
async def create_margin_rule(request: CreateMarginRuleRequest):
    """Create a new margin rule."""
    import uuid
    from datetime import datetime, timezone

    rule = MarginRule(
        rule_id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        markup_pct=request.markup_pct,
        min_margin_pct=request.min_margin_pct,
        max_margin_pct=request.max_margin_pct,
        price_rounding=request.price_rounding,
        is_active=True,
        applies_to_all=request.applies_to_all,
        niche_filter=request.niche_filter,
        category_filter=request.category_filter,
        created_at=datetime.now(timezone.utc),
    )

    async with async_session_factory() as session:
        session.add(rule)
        await session.commit()

    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "markup_pct": rule.markup_pct,
        "is_active": rule.is_active,
    }


@router.put("/margin/rules/{rule_id}", response_model=dict)
async def update_margin_rule(rule_id: str, request: UpdateMarginRuleRequest):
    """Update a margin rule."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(MarginRule).where(MarginRule.rule_id == rule_id))
        rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Margin rule not found")

    # Update fields
    if request.name is not None:
        rule.name = request.name
    if request.description is not None:
        rule.description = request.description
    if request.markup_pct is not None:
        rule.markup_pct = request.markup_pct
    if request.min_margin_pct is not None:
        rule.min_margin_pct = request.min_margin_pct
    if request.max_margin_pct is not None:
        rule.max_margin_pct = request.max_margin_pct
    if request.price_rounding is not None:
        rule.price_rounding = request.price_rounding
    if request.is_active is not None:
        rule.is_active = request.is_active
    if request.applies_to_all is not None:
        rule.applies_to_all = request.applies_to_all
    if request.niche_filter is not None:
        rule.niche_filter = request.niche_filter
    if request.category_filter is not None:
        rule.category_filter = request.category_filter

    async with async_session_factory() as session:
        await session.commit()

    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "markup_pct": rule.markup_pct,
        "is_active": rule.is_active,
    }


@router.delete("/margin/rules/{rule_id}", response_model=dict)
async def delete_margin_rule(rule_id: str):
    """Delete a margin rule."""
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(MarginRule).where(MarginRule.rule_id == rule_id))
        rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Margin rule not found")

    async with async_session_factory() as session:
        await session.delete(rule)
        await session.commit()

    return {"success": True}


@router.post("/margin/apply", response_model=dict)
async def apply_margin_rules(request: ApplyRulesRequest):
    """Apply margin rules to catalog products and update prices."""
    optimizer = MarginOptimizer()

    if request.rule_ids:
        result = await optimizer.apply_rules_to_catalog(rule_ids=request.rule_ids)
    else:
        result = await optimizer.apply_active_rules_to_catalog()

    return {
        "products_updated": result.products_updated,
        "products_failed": result.products_failed,
        "total_cost_change": result.total_cost_change,
        "total_retail_change": result.total_retail_change,
        "avg_margin_before": result.avg_margin_before,
        "avg_margin_after": result.avg_margin_after,
    }


@router.post("/margin/recommend", response_model=dict)
async def recommend_price(request: RecommendedPriceRequest):
    """Get a recommended price for a product."""
    optimizer = MarginOptimizer()
    price = optimizer.calculate_price(
        landed_cost=request.landed_cost,
        min_margin_pct=request.min_margin_pct,
        max_margin_pct=request.max_margin_pct,
        rounding=request.rounding,
    )

    return {
        "landed_cost": request.landed_cost,
        "recommended_price": price,
        "margin_pct": ((price - request.landed_cost) / request.landed_cost * 100) if request.landed_cost > 0 else 0,
    }


@router.get("/margin/summary", response_model=dict)
async def get_margin_summary():
    """Get overall margin summary across all products."""
    optimizer = MarginOptimizer()
    summary = await optimizer.get_margin_summary()

    return {
        "total_products": summary["total_products"],
        "avg_margin_pct": summary["avg_margin_pct"],
        "min_margin_pct": summary["min_margin_pct"],
        "max_margin_pct": summary["max_margin_pct"],
        "products_below_min": summary["products_below_min"],
        "products_above_max": summary["products_above_max"],
    }
