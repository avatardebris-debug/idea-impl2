"""Marketplace module for the dropshipping environment."""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional

from rl_dropshipping.src.agents.competitor import CompetitorAgent
from rl_dropshipping.src.agents.consumer import ConsumerAgent
from rl_dropshipping.src.agents.operator import OperatorAgent


class Marketplace:
    """Simulates the marketplace where operators, competitors, and consumers interact.

    The marketplace manages:
    - Product catalog
    - Competitor agents
    - Consumer agents
    - Market conditions
    """

    def __init__(
        self,
        n_competitors: int = 5,
        n_consumers: int = 1000,
        base_conversion_rate: float = 0.05,
        ad_effectiveness: float = 0.5,
        competition_intensity: float = 0.3,
        seed: Optional[int] = None,
    ):
        self.n_competitors = n_competitors
        self.n_consumers = n_consumers
        self.base_conversion_rate = base_conversion_rate
        self.ad_effectiveness = ad_effectiveness
        self.competition_intensity = competition_intensity
        self.np_random = np.random.RandomState(seed)

        # Product catalog
        self.product_catalog: List[Dict[str, Any]] = [
            {"name": "Phone Case", "category": "electronics", "cost": 5.0, "demand": 0.8},
            {"name": "LED Lamp", "category": "home", "cost": 12.0, "demand": 0.6},
            {"name": "Yoga Mat", "category": "fitness", "cost": 8.0, "demand": 0.7},
            {"name": "Water Bottle", "category": "kitchen", "cost": 6.0, "demand": 0.75},
            {"name": "Bluetooth Speaker", "category": "electronics", "cost": 20.0, "demand": 0.65},
            {"name": "Desk Organizer", "category": "office", "cost": 10.0, "demand": 0.5},
            {"name": "Sunglasses", "category": "fashion", "cost": 7.0, "demand": 0.85},
            {"name": "Backpack", "category": "fashion", "cost": 15.0, "demand": 0.55},
            {"name": "Face Mask Set", "category": "beauty", "cost": 3.0, "demand": 0.9},
            {"name": "Phone Charger", "category": "electronics", "cost": 4.0, "demand": 0.95},
        ]

        # Initialize competitors
        self.competitors: List[CompetitorAgent] = []
        for i in range(n_competitors):
            product = self.product_catalog[i % len(self.product_catalog)]
            competitor = CompetitorAgent(
                competitor_id=i,
                base_price=product["cost"] * 2.5,
                inventory=50,
                max_inventory=100,
                price_aggression=0.3 + self.np_random.uniform(0, 0.4),
                seed=self.np_random.randint(0, 10000),
            )
            self.competitors.append(competitor)

        # Initialize consumers
        self.consumers: List[ConsumerAgent] = []
        for i in range(n_consumers):
            preferences = {
                "electronics": self.np_random.uniform(0.3, 0.9),
                "home": self.np_random.uniform(0.3, 0.9),
                "fitness": self.np_random.uniform(0.3, 0.9),
                "kitchen": self.np_random.uniform(0.3, 0.9),
                "office": self.np_random.uniform(0.3, 0.9),
                "fashion": self.np_random.uniform(0.3, 0.9),
                "beauty": self.np_random.uniform(0.3, 0.9),
            }
            consumer = ConsumerAgent(
                consumer_id=i,
                budget=self.np_random.uniform(50, 500),
                preferences=preferences,
                seed=self.np_random.randint(0, 10000),
            )
            self.consumers.append(consumer)

    def get_market_conditions(self) -> Dict[str, float]:
        """Get current market conditions.

        Returns:
            Dictionary with market condition metrics.
        """
        return {
            "competition_intensity": self.competition_intensity,
            "seasonality": self.np_random.uniform(0.8, 1.2),
            "demand_trend": self.np_random.uniform(0.9, 1.1),
            "base_conversion_rate": self.base_conversion_rate,
            "ad_effectiveness": self.ad_effectiveness,
        }

    def get_competitor_prices(self, product_index: int) -> List[float]:
        """Get prices from all competitors for a given product.

        Args:
            product_index: Index of the product in the catalog.

        Returns:
            List of competitor prices for the product.
        """
        market_conditions = self.get_market_conditions()
        prices = []
        for competitor in self.competitors:
            product = self.product_catalog[product_index % len(self.product_catalog)]
            price = competitor.get_price(market_conditions)
            prices.append(price)
        return prices

    def simulate_sales(
        self,
        operator: OperatorAgent,
        product_index: int,
        ad_spend: float,
    ) -> Dict[str, Any]:
        """Simulate sales for the operator's product.

        Args:
            operator: The operator agent.
            product_index: Index of the product being sold.
            ad_spend: Amount spent on advertising.

        Returns:
            Dictionary with sales results.
        """
        product = self.product_catalog[product_index]
        market_conditions = self.get_market_conditions()

        # Get competitor prices
        competitor_prices = self.get_competitor_prices(product_index)
        avg_competitor_price = np.mean(competitor_prices) if competitor_prices else product["cost"] * 2.5

        # Operator's price (markup * cost)
        markup = 2.5
        operator_price = product["cost"] * markup

        # Calculate conversion rate
        price_competitiveness = max(0.0, 1.0 - (operator_price - avg_competitor_price) / (avg_competitor_price * 2.0))
        demand_factor = product["demand"]
        ad_factor = self.ad_effectiveness * (ad_spend / (operator.initial_budget * 0.1)) if operator.initial_budget > 0 else 0.0
        competition_factor = 1.0 - self.competition_intensity * 0.5

        conversion = self.base_conversion_rate * demand_factor * ad_factor * competition_factor * price_competitiveness

        # Simulate sales
        n_sales = int(self.n_consumers * conversion * self.np_random.uniform(0.5, 1.5))
        n_sales = min(n_sales, operator.inventory)

        # Calculate revenue
        revenue = n_sales * operator_price

        # Update operator
        operator.add_revenue(revenue)
        operator.reduce_inventory(n_sales)

        # Update competitors (they also get some sales)
        for competitor in self.competitors:
            comp_sales = int(n_sales * self.np_random.uniform(0.05, 0.2))
            competitor.update_inventory(comp_sales)

        return {
            "n_sales": n_sales,
            "revenue": revenue,
            "conversion_rate": conversion,
            "operator_price": operator_price,
            "avg_competitor_price": avg_competitor_price,
        }

    def get_state(self) -> Dict[str, Any]:
        """Get the marketplace state.

        Returns:
            Dictionary with marketplace state information.
        """
        return {
            "n_competitors": self.n_competitors,
            "n_consumers": self.n_consumers,
            "market_conditions": self.get_market_conditions(),
            "competitor_states": [c.get_state() for c in self.competitors],
            "product_catalog": self.product_catalog,
        }
