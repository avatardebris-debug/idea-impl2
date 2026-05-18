"""Margin analysis — estimate profit margins from supplier chains."""

import logging
from typing import List, Optional

from src.models.store_analysis import StoreAnalysis

logger = logging.getLogger(__name__)


# Industry-standard dropshipping cost multipliers (supplier -> estimated cost as fraction of retail)
SUPPLIER_COST_MULTIPLIERS = {
    "AliExpress": (0.30, 0.40),
    "CJ Dropshipping": (0.25, 0.35),
    "Spocket": (0.45, 0.55),
    "AliDrop": (0.30, 0.40),
    "DSers": (0.30, 0.40),
    "Zendrop": (0.40, 0.50),
    "Doba": (0.50, 0.60),
    "SaleHoo": (0.40, 0.50),
    "Wholesale88": (0.35, 0.45),
    "Banggood": (0.35, 0.45),
    "Temu": (0.30, 0.40),
    "DHgate": (0.35, 0.45),
}


class MarginEstimate:
    """Estimated margin for a product."""

    def __init__(
        self,
        product_name: str,
        retail_price: float,
        estimated_cost: float,
        margin_pct: float,
        supplier_source: str,
    ):
        self.product_name = product_name
        self.retail_price = retail_price
        self.estimated_cost = estimated_cost
        self.margin_pct = margin_pct
        self.supplier_source = supplier_source

    def to_dict(self) -> dict:
        return {
            "product_name": self.product_name,
            "retail_price": self.retail_price,
            "estimated_cost": self.estimated_cost,
            "margin_pct": round(self.margin_pct, 2),
            "supplier_source": self.supplier_source,
        }


class MarginAnalyzer:
    """Estimates profit margins for products across competitor stores."""

    def analyze(self, stores: List[StoreAnalysis]) -> List[dict]:
        """Analyze margins for all products across all stores.

        Args:
            stores: List of StoreAnalysis objects.

        Returns:
            List of MarginEstimate dicts.
        """
        estimates: List[MarginEstimate] = []

        for store in stores:
            for product in store.products:
                if isinstance(product, dict):
                    retail_price = product.get("price", 0)
                    name = product.get("name", "Unknown")
                else:
                    retail_price = getattr(product, "price", 0)
                    name = getattr(product, "name", "Unknown")
                    
                if not retail_price:
                    continue

                # Find supplier chain for this store
                supplier_source = self._find_best_supplier(store.supplier_info)

                if supplier_source:
                    low, high = SUPPLIER_COST_MULTIPLIERS.get(supplier_source, (0.30, 0.40))
                    # Use midpoint of range
                    cost_fraction = (low + high) / 2
                    estimated_cost = retail_price * cost_fraction
                    margin_pct = ((retail_price - estimated_cost) / retail_price) * 100 if retail_price > 0 else 0

                    estimate = MarginEstimate(
                        product_name=name,
                        retail_price=retail_price,
                        estimated_cost=round(estimated_cost, 2),
                        margin_pct=round(margin_pct, 2),
                        supplier_source=supplier_source,
                    )
                    estimates.append(estimate)
                else:
                    # No supplier detected — use generic estimate
                    generic_low, generic_high = SUPPLIER_COST_MULTIPLIERS.get("AliExpress", (0.30, 0.40))
                    cost_fraction = (generic_low + generic_high) / 2
                    estimated_cost = retail_price * cost_fraction
                    margin_pct = ((retail_price - estimated_cost) / retail_price) * 100 if retail_price > 0 else 0

                    estimate = MarginEstimate(
                        product_name=name,
                        retail_price=retail_price,
                        estimated_cost=round(estimated_cost, 2),
                        margin_pct=round(margin_pct, 2),
                        supplier_source="Unknown (generic estimate)",
                    )
                    estimates.append(estimate)

        logger.info(f"Generated {len(estimates)} margin estimates")
        return [e.to_dict() for e in estimates]

    def _find_best_supplier(self, supplier_info: List) -> Optional[str]:
        """Find the highest-confidence supplier source."""
        if not supplier_info:
            return None
        best = max(supplier_info, key=lambda s: s.confidence)
        return best.source if best.confidence > 0.5 else None
