"""Planner engine for DropGentic.

Core decision-making logic that evaluates products against suppliers,
ranks by profit margin, and generates a recommended action plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dropgentic.models.product import Product
from dropgentic.models.supplier import Supplier
from dropgentic.models.margin import MarginCalculator, MarginResult


@dataclass
class Recommendation:
    """A single sourcing recommendation.

    Attributes:
        product_id: Product identifier.
        supplier_id: Supplier identifier.
        margin_result: Margin calculation result.
        recommended_action: One of 'List', 'Review', 'Reject'.
        priority_score: Composite score for ranking (0-1).
    """
    product_id: str
    supplier_id: str
    margin_result: Optional[MarginResult] = None
    recommended_action: str = "List"
    priority_score: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        d = {
            "product_id": self.product_id,
            "supplier_id": self.supplier_id,
            "recommended_action": self.recommended_action,
            "priority_score": self.priority_score,
        }
        if self.margin_result is not None:
            d["margin_result"] = self.margin_result.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Recommendation":
        """Create from dictionary."""
        margin_result = None
        if "margin_result" in data and data["margin_result"] is not None:
            margin_result = MarginResult.from_dict(data["margin_result"])
        return cls(
            product_id=data["product_id"],
            supplier_id=data["supplier_id"],
            margin_result=margin_result,
            recommended_action=data.get("recommended_action", "List"),
            priority_score=data.get("priority_score", 0.0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Recommendation(product_id={self.product_id}, supplier_id={self.supplier_id}, "
            f"action={self.recommended_action}, score={self.priority_score})"
        )


@dataclass
class SourcingPlan:
    """A complete sourcing plan with ranked recommendations.

    Attributes:
        product_count: Number of products in the plan.
        supplier_count: Number of suppliers in the plan.
        total_cost: Total cost across all recommendations.
        total_revenue: Total revenue across all recommendations.
        total_profit: Total profit across all recommendations.
        total_fees: Total fees across all recommendations.
        avg_net_margin_pct: Average net margin percentage.
        recommendations: List of recommendations.
    """
    product_count: int = 0
    supplier_count: int = 0
    total_cost: float = 0.0
    total_revenue: float = 0.0
    total_profit: float = 0.0
    total_fees: float = 0.0
    avg_net_margin_pct: float = 0.0
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "product_count": self.product_count,
            "supplier_count": self.supplier_count,
            "total_cost": self.total_cost,
            "total_revenue": self.total_revenue,
            "total_profit": self.total_profit,
            "total_fees": self.total_fees,
            "avg_net_margin_pct": self.avg_net_margin_pct,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourcingPlan":
        """Create from dictionary."""
        recs = []
        for r_data in data.get("recommendations", []):
            recs.append(Recommendation.from_dict(r_data))
        return cls(
            product_count=data.get("product_count", 0),
            supplier_count=data.get("supplier_count", 0),
            total_cost=data.get("total_cost", 0.0),
            total_revenue=data.get("total_revenue", 0.0),
            total_profit=data.get("total_profit", 0.0),
            total_fees=data.get("total_fees", 0.0),
            avg_net_margin_pct=data.get("avg_net_margin_pct", 0.0),
            recommendations=recs,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SourcingPlan(products={self.product_count}, suppliers={self.supplier_count}, "
            f"revenue={self.total_revenue}, profit={self.total_profit}, "
            f"avg_margin={self.avg_net_margin_pct:.2%})"
        )


class PlannerEngine:
    """Core planning engine for dropshipping product-supplier matching.

    Evaluates products against suppliers, calculates margins,
    ranks recommendations, and generates sourcing plans.

    Attributes:
        margin_calculator: Margin calculator instance.
        min_net_margin_pct: Minimum net margin percentage to include.
        max_recommendations: Maximum recommendations to return.
        min_gross_margin_pct: Minimum gross margin percentage to include.
        min_supplier_rating: Minimum supplier rating to include.
        max_lead_time_days: Maximum lead time in days to include.
    """

    def __init__(
        self,
        margin_calculator: Optional[MarginCalculator] = None,
        min_net_margin_pct: float = 5.0,
        max_recommendations: int = 50,
        min_gross_margin_pct: float = 0.0,
        min_supplier_rating: float = 0.0,
        max_lead_time_days: int = 999,
        currency: str = "USD",
    ) -> None:
        """Initialize the planner engine.

        Args:
            margin_calculator: Margin calculator instance.
            min_net_margin_pct: Minimum net margin percentage to include.
            max_recommendations: Maximum recommendations to return.
            min_gross_margin_pct: Minimum gross margin percentage to include.
            min_supplier_rating: Minimum supplier rating to include.
            max_lead_time_days: Maximum lead time in days to include.
            currency: Currency code.
        """
        self.margin_calculator = margin_calculator or MarginCalculator(currency=currency)
        self.min_net_margin_pct = min_net_margin_pct / 100.0
        self.max_recommendations = max_recommendations
        self.min_gross_margin_pct = min_gross_margin_pct / 100.0
        self.min_supplier_rating = min_supplier_rating
        self.max_lead_time_days = max_lead_time_days
        self.currency = currency

    def evaluate_product_supplier_pair(
        self,
        product: Product,
        supplier: Supplier,
    ) -> Optional[MarginResult]:
        """Evaluate a single product-supplier pair.

        Args:
            product: Product to evaluate.
            supplier: Supplier to evaluate against.

        Returns:
            MarginResult if evaluation succeeds, None otherwise.
        """
        try:
            if not supplier.active:
                return None
            if supplier.rating < self.min_supplier_rating:
                return None
            if supplier.lead_time_days > self.max_lead_time_days:
                return None

            shipping_cost = self.margin_calculator.calculate_shipping(
                weight_kg=product.weight_kg,
                supplier_shipping_cost_per_unit=supplier.shipping_cost_per_unit,
                supplier_shipping_weight_factor=supplier.shipping_weight_factor,
            )

            result = self.margin_calculator.calculate(
                cost_price=product.cost_price,
                shipping_cost=shipping_cost,
                retail_price=product.retail_price,
            )
            result.product_id = product.product_id
            result.supplier_id = supplier.supplier_id
            return result
        except Exception:
            return None

    def generate_sourcing_plan(
        self,
        products: list,
        suppliers: list,
    ) -> SourcingPlan:
        """Generate a sourcing plan by evaluating all product-supplier pairs.

        Args:
            products: List of Product instances.
            suppliers: List of Supplier instances.

        Returns:
            SourcingPlan with ranked recommendations.
        """
        recommendations: list = []

        for product in products:
            for supplier in suppliers:
                margin_result = self.evaluate_product_supplier_pair(product, supplier)
                if margin_result is None:
                    continue

                # Check minimum margins
                if margin_result.gross_margin_pct < self.min_gross_margin_pct:
                    continue
                if margin_result.net_margin_pct < self.min_net_margin_pct:
                    continue

                # Calculate composite score: weighted combination of net margin,
                # supplier rating, and inverse lead time
                score = (
                    margin_result.net_margin_pct * 0.6
                    + supplier.rating * 10 * 0.25
                    + max(0, (30 - supplier.lead_time_days)) * 0.15
                )

                recommendations.append(
                    Recommendation(
                        product_id=product.product_id,
                        supplier_id=supplier.supplier_id,
                        margin_result=margin_result,
                        recommended_action=margin_result.recommended_action,
                        priority_score=round(score, 2),
                    )
                )

        # Sort by score descending
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)

        # Limit recommendations
        recommendations = recommendations[: self.max_recommendations]

        # Calculate plan totals
        total_cost = sum(r.margin_result.total_cost for r in recommendations)
        total_revenue = sum(r.margin_result.retail_price for r in recommendations)
        total_profit = sum(r.margin_result.net_profit for r in recommendations)
        total_fees = sum(r.margin_result.total_fees for r in recommendations)
        avg_net_margin = (
            sum(r.margin_result.net_margin_pct for r in recommendations) / len(recommendations)
            if recommendations else 0.0
        )

        # Get unique products and suppliers
        unique_products = set(r.product_id for r in recommendations)
        unique_suppliers = set(r.supplier_id for r in recommendations)

        return SourcingPlan(
            product_count=len(unique_products),
            supplier_count=len(unique_suppliers),
            total_cost=round(total_cost, 2),
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            total_fees=round(total_fees, 2),
            avg_net_margin_pct=round(avg_net_margin, 4),
            recommendations=recommendations,
        )

    def filter_by_margin(
        self,
        plan: SourcingPlan,
        min_net_margin_pct: Optional[float] = None,
    ) -> SourcingPlan:
        """Filter a plan by minimum net margin.

        Args:
            plan: SourcingPlan to filter.
            min_net_margin_pct: Minimum net margin percentage.

        Returns:
            Filtered SourcingPlan.
        """
        threshold = (min_net_margin_pct or self.min_net_margin_pct) / 100.0 if min_net_margin_pct else self.min_net_margin_pct
        filtered = [
            r for r in plan.recommendations
            if r.margin_result and r.margin_result.net_margin_pct >= threshold
        ]

        # Recalculate totals
        total_cost = sum(r.margin_result.total_cost for r in filtered)
        total_revenue = sum(r.margin_result.retail_price for r in filtered)
        total_profit = sum(r.margin_result.net_profit for r in filtered)
        total_fees = sum(r.margin_result.total_fees for r in filtered)
        avg_net_margin = (
            sum(r.margin_result.net_margin_pct for r in filtered) / len(filtered)
            if filtered else 0.0
        )
        unique_products = set(r.product_id for r in filtered)
        unique_suppliers = set(r.supplier_id for r in filtered)

        return SourcingPlan(
            product_count=len(unique_products),
            supplier_count=len(unique_suppliers),
            total_cost=round(total_cost, 2),
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            total_fees=round(total_fees, 2),
            avg_net_margin_pct=round(avg_net_margin, 4),
            recommendations=filtered,
        )

    def filter_by_supplier(
        self,
        plan: SourcingPlan,
        supplier_ids: list,
    ) -> SourcingPlan:
        """Filter a plan by supplier IDs.

        Args:
            plan: SourcingPlan to filter.
            supplier_ids: List of supplier IDs to include.

        Returns:
            Filtered SourcingPlan.
        """
        filtered = [
            r for r in plan.recommendations
            if r.supplier_id in supplier_ids
        ]

        # Recalculate totals
        total_cost = sum(r.margin_result.total_cost for r in filtered)
        total_revenue = sum(r.margin_result.retail_price for r in filtered)
        total_profit = sum(r.margin_result.net_profit for r in filtered)
        total_fees = sum(r.margin_result.total_fees for r in filtered)
        avg_net_margin = (
            sum(r.margin_result.net_margin_pct for r in filtered) / len(filtered)
            if filtered else 0.0
        )
        unique_products = set(r.product_id for r in filtered)
        unique_suppliers = set(r.supplier_id for r in filtered)

        return SourcingPlan(
            product_count=len(unique_products),
            supplier_count=len(unique_suppliers),
            total_cost=round(total_cost, 2),
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            total_fees=round(total_fees, 2),
            avg_net_margin_pct=round(avg_net_margin, 4),
            recommendations=filtered,
        )
