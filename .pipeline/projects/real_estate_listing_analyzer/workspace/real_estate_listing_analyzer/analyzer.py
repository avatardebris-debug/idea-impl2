"""
real_estate_listing_analyzer/analyzer.py
Price trend analysis and comparable property scoring.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fetcher import Listing


@dataclass
class TrendResult:
    zip_code: str
    listing_count: int
    median_price: float
    median_price_per_sqft: float
    price_slope_30d: float      # $/sqft change per day (30-day linear trend)
    median_dom: float           # median days-on-market
    dom_stddev: float
    list_to_sale_ratio: float   # avg list price / Zestimate
    neighborhood_score: float   # 0-100 composite


def linear_slope(ys: list[float]) -> float:
    """Slope of a simple linear regression over equally-spaced x=[0..n-1]."""
    n = len(ys)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2
    y_mean = statistics.mean(ys)
    num = sum((i - x_mean) * (ys[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


class TrendAnalyzer:
    """Compute price trends and neighborhood metrics from a listing set."""

    def analyze(self, listings: "list[Listing]", zip_code: str = "") -> TrendResult:
        if not listings:
            return TrendResult(
                zip_code=zip_code, listing_count=0, median_price=0,
                median_price_per_sqft=0, price_slope_30d=0, median_dom=0,
                dom_stddev=0, list_to_sale_ratio=1.0, neighborhood_score=0,
            )

        prices     = [l.price for l in listings if l.price > 0]
        ppsf       = [l.price_per_sqft for l in listings if l.price_per_sqft > 0]
        doms       = [l.days_on_market for l in listings]
        zestimates = [l.zestimate for l in listings if l.zestimate > 0 and l.price > 0]

        # List-to-Zestimate ratio: 1.0 = fairly priced, >1 = overpriced
        ltz_ratios = [l.price / l.zestimate for l in listings
                      if l.zestimate > 0 and l.price > 0]

        return TrendResult(
            zip_code=zip_code,
            listing_count=len(listings),
            median_price=statistics.median(prices) if prices else 0,
            median_price_per_sqft=statistics.median(ppsf) if ppsf else 0,
            price_slope_30d=linear_slope(ppsf[-30:]) if len(ppsf) >= 2 else 0.0,
            median_dom=statistics.median(doms) if doms else 0,
            dom_stddev=statistics.stdev(doms) if len(doms) >= 2 else 0.0,
            list_to_sale_ratio=statistics.mean(ltz_ratios) if ltz_ratios else 1.0,
            neighborhood_score=self._neighborhood_score(listings),
        )

    def _neighborhood_score(self, listings: "list[Listing]") -> float:
        """
        Heuristic 0-100 score based on available signals.
        Real implementation would incorporate census + school + crime APIs.
        """
        if not listings:
            return 0.0
        # Proxy: lower days-on-market and higher price/sqft → desirable area
        avg_dom  = statistics.mean([l.days_on_market for l in listings]) or 1
        avg_ppsf = statistics.mean([l.price_per_sqft for l in listings if l.price_per_sqft > 0]) or 1
        dom_score  = max(0, 100 - avg_dom)           # 0 DOM = 100, 100 DOM = 0
        ppsf_score = min(100, avg_ppsf / 10)         # very rough normalization
        return round((dom_score * 0.5 + ppsf_score * 0.5), 1)


class ComparablesFinder:
    """Find similar listings using k-NN on key property features."""

    def find(
        self,
        target: "Listing",
        pool: "list[Listing]",
        k: int = 5,
    ) -> "list[Listing]":
        """Return k closest listings to target by Euclidean distance."""
        def dist(l: "Listing") -> float:
            return math.sqrt(
                ((l.bedrooms - target.bedrooms) * 20) ** 2 +
                ((l.bathrooms - target.bathrooms) * 15) ** 2 +
                ((l.sqft - target.sqft) / 100) ** 2 +
                ((l.price - target.price) / 50_000) ** 2
            )
        scored = [(dist(l), l) for l in pool if l.zpid != target.zpid]
        scored.sort(key=lambda x: x[0])
        return [l for _, l in scored[:k]]
