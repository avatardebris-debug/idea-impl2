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
        product_title: Product title.
        supplier_id: Supplier identifier.
        supplier_name: Supplier name.
        margin_result: Margin calculation result.
        rank: Rank position (1 = best).
        score: Composite score for ranking.
        recommended_action: Recommended action (List, Review, Reject).
        priority_score: Priority score for ranking.
    """
    product_id: str
    product_title: str = ""
    supplier_id: str = ""
    supplier_name: str = ""
    margin_result: Optional[MarginResult] = None
    rank: int = 1
    score: float = 0.0
    recommended_action: str = ""
    priority_score: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "product_id": self.product_id,
            "product_title": self.product_title,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "rank": self.rank,
            "score": self.score,
            "recommended_action": self.recommended_action,
            "priority_score": self.priority_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Recommendation:
        """Create from dictionary."""
        return cls(
            product_id=data.get("product_id", ""),
            product_title=data.get("product_title", ""),
            supplier_id=data.get("supplier_id", ""),
            supplier_name=data.get("supplier_name", ""),
            rank=data.get("rank", 1),
            score=data.get("score", 0.0),
            recommended_action=data.get("recommended_action", ""),
            priority_score=data.get("priority_score", 0.0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Recommendation(product_id={self.product_id}, supplier_id={self.supplier_id}, "
            f"action={self.recommended_action}, priority={self.priority_score})"
        )


@dataclass
class SourcingPlan:
    """A complete sourcing plan with ranked recommendations.

    Attributes:
        recommendations: List of ranked recommendations.
        total_products_evaluated: Number of products evaluated.
        total_supplier_matches: Total product-supplier pairs evaluated.
        best_margin_pct: Best net margin found.
        summary: Human-readable summary.
        product_count: Number of unique products.
        supplier_count: Number of unique suppliers.
        total_cost: Total cost.
        total_revenue: Total revenue.
        total_profit: Total profit.
        total_fees: Total fees.
        avg_net_margin_pct: Average net margin percentage.
    """
    recommendations: list = field(default_factory=list)
    total_products_evaluated: int = 0
    total_supplier_matches: int = 0
    best_margin_pct: float = 0.0
    summary: str = ""
    product_count: int = 0
    supplier_count: int = 0
    total_cost: float = 0.0
    total_revenue: float = 0.0
    total_profit: float = 0.0
    total_fees: float = 0.0
    avg_net_margin_pct: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "recommendations": [
                {
                    "product_id": r.product_id,
                    "product_title": r.product_title,
                    "supplier_id": r.supplier_id,
                    "supplier_name": r.supplier_name,
                    "rank": r.rank,
                    "score": r.score,
                    "recommended_action": r.recommended_action,
                    "priority_score": r.priority_score,
                }
            for r in self.recommendations
            ],
            "total_products_evaluated": self.total_products_evaluated,
            "total_supplier_matches": self.total_supplier_matches,
            "best_margin_pct": self.best_margin_pct,
            "summary": self.summary,
            "product_count": self.product_count,
            "supplier_count": self.supplier_count,
            "total_cost": self.total_cost,
            "total_revenue": self.total_revenue,
            "total_profit": self.total_profit,
            "total_fees": self.total_fees,
            "avg_net_margin_pct": self.avg_net_margin_pct,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SourcingPlan:
        """Create from dictionary."""
        recs_data = data.get("recommendations", [])
        recs = [
            Recommendation(
                product_id=r.get("product_id", ""),
                product_title=r.get("product_title", ""),
                supplier_id=r.get("supplier_id", ""),
                supplier_name=r.get("supplier_name", ""),
                rank=r.get("rank", 1),
                score=r.get("score", 0.0),
                recommended_action=r.get("recommended_action", ""),
                priority_score=r.get("priority_score", 0.0),
            )
            for r in recs_data
        ]
        return cls(
            recommendations=recs,
            total_products_evaluated=data.get("total_products_evaluated", 0),
            total_supplier_matches=data.get("total_supplier_matches", 0),
            best_margin_pct=data.get("best_margin_pct", 0.0),
            summary=data.get("summary", ""),
            product_count=data.get("product_count", 0),
            supplier_count=data.get("supplier_count", 0),
            total_cost=data.get("total_cost", 0.0),
            total_revenue=data.get("total_revenue", 0.0),
            total_profit=data.get("total_profit", 0.0),
            total_fees=data.get("total_fees", 0.0),
            avg_net_margin_pct=data.get("avg_net_margin_pct", 0.0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SourcingPlan(product_count={self.product_count}, supplier_count={self.supplier_count}, "
            f"total_revenue={self.total_revenue}, total_profit={self.total_profit})"
        )


class PlannerEngine:
    """Core planning engine for dropshipping product-supplier matching.

    Evaluates products against suppliers, calculates margins,
    ranks recommendations, and generates sourcing plans.
    """

    def __init__(
        self,
        margin_calculator: Optional[MarginCalculator] = None,
        min_net_margin_pct: float = 5.0,
        max_recommendations: int = 50,
        max_lead_time_days: int = 30,
        min_supplier_rating: float = 0.0,
        min_gross_margin_pct: float = 20.0,
        currency: str = "USD",
    ) -> None:
        """Initialize the planner engine.

        Args:
            margin_calculator: Margin calculator instance.
            min_net_margin_pct: Minimum net margin percentage to include.
            max_recommendations: Maximum recommendations to return.
            max_lead_time_days: Maximum lead time in days.
            min_supplier_rating: Minimum supplier rating.
            min_gross_margin_pct: Minimum gross margin percentage.
            currency: Currency code.
        """
        self.margin_calculator = margin_calculator or MarginCalculator()
        self.min_net_margin_pct = min_net_margin_pct
        self.max_recommendations = max_recommendations
        self.max_lead_time_days = max_lead_time_days
        self.min_supplier_rating = min_supplier_rating
        self.min_gross_margin_pct = min_gross_margin_pct
        self.currency = currency

    def evaluate_product_supplier(
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

    def evaluate_product_supplier_pair(
        self,
        product: Product,
        supplier: Supplier,
    ) -> Optional[MarginResult]:
        """Evaluate a single product-supplier pair (alias for evaluate_product_supplier).

        Args:
            product: Product to evaluate.
            supplier: Supplier to evaluate against.

        Returns:
            MarginResult if evaluation succeeds, None otherwise.
        """
        result = self.evaluate_product_supplier(product, supplier)
        if result is not None:
            if supplier.lead_time_days > self.max_lead_time_days:
                result.recommended_action = "Reject"
            elif getattr(supplier, "rating", 5.0) < self.min_supplier_rating:
                result.recommended_action = "Reject"
            elif getattr(result, "gross_margin_pct", 1.0) * 100 < getattr(self, "min_gross_margin_pct", 0):
                result.recommended_action = "Reject"
            else:
                result.recommended_action = self._get_recommended_action(result)
        return result

    def _get_recommended_action(self, margin_result: MarginResult) -> str:
        """Get recommended action based on margin result."""
        if margin_result.net_margin_pct * 100 >= 20:
            return "List"
        elif margin_result.net_margin_pct * 100 >= self.min_net_margin_pct:
            return "Review"
        else:
            return "Reject"

    def generate_plan(
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
                if not supplier.active:
                    continue

                margin_result = self.evaluate_product_supplier(product, supplier)
                if margin_result is None:
                    continue

                # Calculate composite score: weighted combination of net margin,
                # supplier rating, and inverse lead time
                score = (
                    margin_result.net_margin_pct * 0.6
                    + supplier.rating * 10 * 0.25
                    + max(0, (30 - supplier.lead_time_days)) * 0.15
                )

                # Only include if above minimum margin threshold
                if margin_result.net_margin_pct * 100 >= self.min_net_margin_pct:
                    recommended_action = self._get_recommended_action(margin_result)
                    recommendations.append(
                        Recommendation(
                            product_id=product.product_id,
                            product_title=product.title,
                            supplier_id=supplier.supplier_id,
                            supplier_name=supplier.name,
                            margin_result=margin_result,
                            score=round(score, 2),
                            recommended_action=recommended_action,
                            priority_score=round(score, 2),
                        )
                    )

        # Sort by score descending
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        for i, rec in enumerate(recommendations):
            rec.rank = i + 1

        # Limit recommendations
        recommendations = recommendations[: self.max_recommendations]

        best_margin = max(
            (r.margin_result.net_margin_pct for r in recommendations),
            default=0.0,
        )

        # Compute aggregate stats
        unique_products = set(r.product_id for r in recommendations)
        unique_suppliers = set(r.supplier_id for r in recommendations)
        total_cost = sum(r.margin_result.total_cost for r in recommendations)
        total_revenue = sum(r.margin_result.retail_price for r in recommendations)
        total_profit = sum(r.margin_result.net_profit for r in recommendations)
        total_fees = sum(r.margin_result.total_fees for r in recommendations)
        avg_net_margin_pct = (
            sum(r.margin_result.net_margin_pct for r in recommendations) / len(recommendations)
            if recommendations
            else 0.0
        )

        # Generate summary
        viable = sum(1 for r in recommendations if r.margin_result.net_margin_pct >= 15)
        summary = (
            f"Evaluated {len(products)} products against {len(suppliers)} suppliers. "
            f"Found {len(recommendations)} viable sourcing options "
            f"(net margin >= {self.min_net_margin_pct}%). "
            f"Best net margin: {best_margin:.1f}%. "
            f"Viable options (>=15% margin): {viable}."
        )

        return SourcingPlan(
            recommendations=recommendations,
            total_products_evaluated=len(products),
            total_supplier_matches=len(products) * len(suppliers),
            best_margin_pct=round(best_margin, 2),
            summary=summary,
            product_count=len(unique_products),
            supplier_count=len(unique_suppliers),
            total_cost=round(total_cost, 2),
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            total_fees=round(total_fees, 2),
            avg_net_margin_pct=round(avg_net_margin_pct * 100, 2),
        )

    def generate_sourcing_plan(
        self,
        products: list,
        suppliers: list,
    ) -> SourcingPlan:
        """Generate a sourcing plan (alias for generate_plan).

        Args:
            products: List of Product instances.
            suppliers: List of Supplier instances.

        Returns:
            SourcingPlan with ranked recommendations.
        """
        return self.generate_plan(products, suppliers)

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
        threshold = min_net_margin_pct or self.min_net_margin_pct
        filtered = [
            r for r in plan.recommendations
            if r.margin_result.net_margin_pct >= threshold
        ]
        for i, rec in enumerate(filtered):
            rec.rank = i + 1

        best_margin = max(
            (r.margin_result.net_margin_pct for r in filtered),
            default=0.0,
        )

        return SourcingPlan(
            recommendations=filtered,
            total_products_evaluated=plan.total_products_evaluated,
            total_supplier_matches=plan.total_supplier_matches,
            best_margin_pct=round(best_margin, 2),
            summary=f"Filtered to net margin >= {threshold}%. "
                    f"{len(filtered)} recommendations remaining.",
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
        for i, rec in enumerate(filtered):
            rec.rank = i + 1

        best_margin = max(
            (r.margin_result.net_margin_pct for r in filtered),
            default=0.0,
        )

        return SourcingPlan(
            recommendations=filtered,
            total_products_evaluated=plan.total_products_evaluated,
            total_supplier_matches=plan.total_supplier_matches,
            best_margin_pct=round(best_margin, 2),
            summary=f"Filtered to suppliers: {', '.join(supplier_ids)}. "
                    f"{len(filtered)} recommendations remaining.",
        )
