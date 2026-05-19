"""Margin optimizer service."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.models.margin_rule import MarginRule
from backend.models.product import CatalogProduct
from backend.utils.database import async_session_factory
from sqlalchemy import select


class MarginApplyResult:
    """Result of applying margin rules to products."""
    def __init__(
        self,
        products_updated: int = 0,
        products_skipped: int = 0,
        products_failed: int = 0,
        error_messages: Optional[List[str]] = None,
    ):
        self.products_updated = products_updated
        self.products_skipped = products_skipped
        self.products_failed = products_failed
        self.error_messages = error_messages or []


class MarginOptimizer:
    """Rule-based pricing engine for margin optimization."""

    @staticmethod
    def apply_rounding(price: float, rounding: str) -> float:
        """Apply price rounding to a given price.

        Args:
            price: The original price.
            rounding: The rounding mode ('none', '.99', '.95', '.50', '.00').

        Returns:
            The rounded price.
        """
        if rounding == "none":
            return round(price, 2)
        elif rounding == ".99":
            return round(price - 0.01, 2)
        elif rounding == ".95":
            return round(price - 0.05, 2)
        elif rounding == ".50":
            return round(price * 2) / 2
        elif rounding == ".00":
            return round(price, 0)
        return round(price, 2)

    @staticmethod
    def calculate_margin(cost: float, price: float) -> float:
        """Calculate margin percentage from cost and price.

        Args:
            cost: The cost price.
            price: The selling price.

        Returns:
            The margin percentage.
        """
        if cost <= 0:
            return 0.0
        return ((price - cost) / cost) * 100

    @staticmethod
    def calculate_price_from_cost(cost: float, markup_pct: float) -> float:
        """Calculate selling price from cost and markup percentage.

        Args:
            cost: The cost price.
            markup_pct: The markup percentage.

        Returns:
            The calculated selling price.
        """
        return cost * (1 + markup_pct / 100)

    async def apply_rules_to_catalog(
        self,
        catalog_id: str,
        rule_ids: Optional[List[str]] = None,
    ) -> MarginApplyResult:
        """Apply margin rules to products in a catalog.

        Args:
            catalog_id: The catalog ID to apply rules to.
            rule_ids: Optional list of rule IDs to apply. If None, applies all active rules.

        Returns:
            MarginApplyResult with counts of updated, skipped, and failed products.
        """
        result = MarginApplyResult()

        # Get rules to apply
        async with async_session_factory() as session:
            if rule_ids:
                stmt = select(MarginRule).where(
                    MarginRule.rule_id.in_(rule_ids),
                    MarginRule.is_active == True,
                )
            else:
                stmt = select(MarginRule).where(MarginRule.is_active == True)
            rules_result = await session.execute(stmt)
            rules = rules_result.scalars().all()

        if not rules:
            return result

        # Get catalog products
        async with async_session_factory() as session:
            stmt = select(CatalogProduct).where(
                CatalogProduct.catalog_id == catalog_id,
            )
            products_result = await session.execute(stmt)
            products = products_result.scalars().all()

        if not products:
            return result

        for product in products:
            try:
                # Find the best matching rule
                best_rule = None
                for rule in rules:
                    if rule.applies_to_all:
                        best_rule = rule
                        break
                    if rule.niche_filter and product.niche_id and product.niche_id in rule.niche_filter:
                        best_rule = rule
                        break
                    if rule.category_filter and product.category and product.category in rule.category_filter:
                        best_rule = rule
                        break

                if not best_rule:
                    result.products_skipped += 1
                    continue

                # Calculate new price
                new_price = self.calculate_price_from_cost(product.landed_cost, best_rule.markup_pct)

                # Apply margin floor
                min_margin_price = product.landed_cost * (1 + best_rule.min_margin_pct / 100)
                if new_price < min_margin_price:
                    new_price = min_margin_price

                # Apply margin cap
                max_margin_price = product.landed_cost * (1 + best_rule.max_margin_pct / 100)
                if new_price > max_margin_price:
                    new_price = max_margin_price

                # Apply rounding
                new_price = self.apply_rounding(new_price, best_rule.rounding)

                # Update product
                product.retail_price = new_price
                product.margin_pct = self.calculate_margin(product.landed_cost, new_price)
                product.updated_at = datetime.now(timezone.utc)
                result.products_updated += 1

            except Exception as e:
                result.products_failed += 1
                result.error_messages.append(f"Failed to apply rules to product {product.supplier_product_id}: {str(e)}")

        # Save changes
        async with async_session_factory() as session:
            for product in products:
                if product.retail_price is not None:
                    session.add(product)
            await session.commit()

        return result

    async def get_recommended_price(
        self,
        landed_cost: float,
        min_margin_pct: float = 0.0,
        max_margin_pct: float = 100.0,
        rounding: str = ".99",
    ) -> float:
        """Get a recommended price based on cost and margin constraints.

        Args:
            landed_cost: The landed cost of the product.
            min_margin_pct: Minimum margin percentage.
            max_margin_pct: Maximum margin percentage.
            rounding: The rounding mode.

        Returns:
            The recommended price.
        """
        # Calculate price based on min margin
        price = self.calculate_price_from_cost(landed_cost, min_margin_pct)

        # Apply margin cap
        max_price = self.calculate_price_from_cost(landed_cost, max_margin_pct)
        if price > max_price:
            price = max_price

        # Apply rounding
        price = self.apply_rounding(price, rounding)

        return price
