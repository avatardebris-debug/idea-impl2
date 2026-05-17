"""SourcingAgent — finds products matching the business specification."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentflow_drophip.agents.base import AgentResult, BaseAgent
from agentflow_drophip.models.business_spec import BusinessSpec, SupplierType


class SourcingAgent(BaseAgent):
    """Agent that finds products from suppliers matching the business spec."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        supplier_type: Optional[SupplierType] = None,
    ):
        """Initialize the sourcing agent.

        Args:
            config: Configuration dictionary.
            supplier_type: Type of supplier to use.
        """
        super().__init__(name="sourcing_agent", config=config)
        self.supplier_type = supplier_type or SupplierType.ALIEXPRESS
        self._mock_products = self._generate_mock_products()

    def execute(
        self,
        spec: Optional[BusinessSpec] = None,
        niche: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute product sourcing.

        Args:
            spec: Business specification.
            niche: Product niche to search for.
            max_price: Maximum product cost.
            limit: Maximum number of products to return.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with sourced products.
        """
        self.execution_count += 1

        # Determine search parameters
        search_niche = niche or (spec.niche if spec else "general")
        search_max_price = max_price or (spec.max_product_cost if spec else 50.0)

        # Filter mock products
        filtered_products = [
            p for p in self._mock_products
            if (not niche or search_niche.lower() in p["niche"].lower())
            and (not max_price or p["price"] <= search_max_price)
        ]

        # If no matches, return all mock products up to limit
        if not filtered_products:
            filtered_products = self._mock_products[:limit]

        # Limit results
        products = filtered_products[:limit]

        result = AgentResult(
            success=True,
            data={
                "supplier_type": self.supplier_type.value,
                "search_niche": search_niche,
                "max_price": search_max_price,
                "total_available": len(filtered_products),
                "returned": len(products),
            },
            products=products,
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        self.last_result = result
        return result

    def _generate_mock_products(self) -> List[Dict[str, Any]]:
        """Generate mock products for testing."""
        products = []
        niches = ["electronics", "home", "fashion", "beauty", "sports", "toys"]

        for i in range(100):
            niche = random.choice(niches)
            products.append({
                "id": f"prod_{i:04d}",
                "name": f"Mock Product {i}",
                "niche": niche,
                "price": round(random.uniform(5.0, 100.0), 2),
                "supplier": self.supplier_type.value,
                "rating": round(random.uniform(3.0, 5.0), 1),
                "stock": random.randint(0, 1000),
                "shipping_time": random.choice([3, 5, 7, 10, 14]),
                "image_url": f"https://example.com/images/prod_{i}.jpg",
            })

        return products
