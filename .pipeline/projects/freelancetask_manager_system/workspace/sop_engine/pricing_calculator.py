"""Pricing Calculator — Compute tiered pricing from SOP inputs."""

from __future__ import annotations

from typing import Any

from core.service_offering import ServiceOffering, PricingTier


class PricingCalculator:
    """
    Computes and analyzes tiered pricing from a ServiceOffering.
    """

    def calculate(self, offering: ServiceOffering) -> dict[str, Any]:
        """
        Calculate pricing summary for an SOP.

        Returns:
            dict with keys:
              - tiers: list[dict] — each tier's data
              - min_price: float
              - max_price: float
              - avg_price: float
              - total_value: float
        """
        tiers = [t.to_dict() for t in offering.pricing]
        prices = [t.price for t in offering.pricing]

        return {
            "tiers": tiers,
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "total_value": sum(prices),
        }

    def get_tier(self, offering: ServiceOffering, tier_name: str) -> PricingTier | None:
        """Get a specific pricing tier by name."""
        for tier in offering.pricing:
            if tier.name.lower() == tier_name.lower():
                return tier
        return None

    def get_price_range(self, offering: ServiceOffering) -> tuple[float, float]:
        """Return (min_price, max_price) tuple."""
        prices = [t.price for t in offering.pricing]
        return (min(prices), max(prices))

    def recommend_tier(self, offering: ServiceOffering, budget: float) -> PricingTier | None:
        """
        Recommend the best pricing tier for a given budget.
        Picks the highest tier where price <= budget.
        """
        best = None
        for tier in offering.pricing:
            if tier.price <= budget:
                best = tier
        return best
