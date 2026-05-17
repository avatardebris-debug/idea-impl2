"""Consumer agent for the dropshipping environment."""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional


class ConsumerAgent:
    """Simulates an individual consumer in the dropshipping market.

    Consumers have preferences, budgets, and purchasing behavior
    influenced by product attributes, pricing, and advertising.
    """

    def __init__(
        self,
        consumer_id: int,
        budget: float,
        preferences: Dict[str, float],
        seed: Optional[int] = None,
    ):
        self.consumer_id = consumer_id
        self.budget = budget
        self.preferences = preferences  # category -> preference weight
        self.purchase_history: List[Dict[str, Any]] = []
        self.np_random = np.random.RandomState(seed)

    def evaluate_product(
        self,
        product: Dict[str, Any],
        price: float,
        ad_exposure: float = 0.0,
    ) -> float:
        """Evaluate a product and return a purchase likelihood score.

        Args:
            product: Product dictionary with 'category', 'cost', 'demand'.
            price: Current price of the product.
            ad_exposure: Level of advertising exposure (0.0 to 1.0).

        Returns:
            Purchase likelihood score between 0.0 and 1.0.
        """
        category = product.get("category", "general")
        preference = self.preferences.get(category, 0.5)

        # Price sensitivity (lower price = higher likelihood)
        price_factor = max(0.0, 1.0 - (price / (product.get("cost", 10.0) * 5.0)))

        # Demand factor
        demand_factor = product.get("demand", 0.5)

        # Ad exposure factor
        ad_factor = ad_exposure * 0.3

        # Combined purchase likelihood
        likelihood = preference * 0.4 + price_factor * 0.3 + demand_factor * 0.2 + ad_factor

        return min(max(likelihood, 0.0), 1.0)

    def purchase(self, product: Dict[str, Any], price: float) -> bool:
        """Attempt to purchase a product.

        Args:
            product: Product dictionary.
            price: Price to pay.

        Returns:
            True if purchase was successful, False otherwise.
        """
        if self.budget >= price:
            self.budget -= price
            self.purchase_history.append({
                "product": product.get("name", "unknown"),
                "price": price,
                "timestamp": len(self.purchase_history),
            })
            return True
        return False

    def get_state(self) -> Dict[str, Any]:
        """Get the consumer's current state.

        Returns:
            Dictionary with consumer state information.
        """
        return {
            "consumer_id": self.consumer_id,
            "budget": self.budget,
            "preferences": self.preferences,
            "n_purchases": len(self.purchase_history),
        }
