"""Cost calculator for logistics shipments."""

import math


# Priority multipliers
PRIORITY_MULTIPLIERS = {
    "standard": 1.0,
    "express": 1.5,
    "overnight": 2.0,
}

# Base cost per unit distance
BASE_COST_PER_UNIT = 0.5

# Volume factor
VOLUME_FACTOR = 0.01


class CostCalculator:
    """Calculate shipping costs for a list of shipments."""

    @classmethod
    def calculate_costs(cls, shipments: list[dict]) -> list[dict]:
        """Calculate costs for all shipments.

        Args:
            shipments: List of shipment dicts (may include origin, destination,
                       priority, weight, length, width, height).

        Returns:
            List of shipment dicts augmented with 'cost' and 'distance_factor'.
        """
        if not shipments:
            return []

        result = []
        for shipment in shipments:
            cost, distance_factor = cls._calculate_single_cost(shipment)
            entry = dict(shipment)
            entry["cost"] = cost
            entry["distance_factor"] = distance_factor
            result.append(entry)
        return result

    @classmethod
    def _calculate_single_cost(cls, shipment: dict) -> tuple[float, float]:
        """Calculate cost and distance factor for a single shipment.

        Uses origin/destination as a proxy for distance (hash-based).
        """
        origin = shipment.get("origin", "")
        destination = shipment.get("destination", "")

        # Simple distance proxy based on city name hashes
        distance = cls._hash_distance(origin, destination)
        distance_factor = round(distance / 1000.0, 2)

        # Weight factor
        weight = shipment.get("weight", 0)
        weight_factor = 1.0 + (weight / 100.0)

        # Volume factor
        length = shipment.get("length", 0)
        width = shipment.get("width", 0)
        height = shipment.get("height", 0)
        volume = length * width * height
        volume_factor = 1.0 + (volume * VOLUME_FACTOR / 10000.0)

        # Priority multiplier
        priority = shipment.get("priority", "standard")
        priority_mult = PRIORITY_MULTIPLIERS.get(priority, 1.0)

        cost = BASE_COST_PER_UNIT * distance_factor * weight_factor * volume_factor * priority_mult
        cost = round(cost, 2)

        return cost, distance_factor

    @staticmethod
    def _hash_distance(origin: str, destination: str) -> float:
        """Generate a deterministic distance proxy from city names."""
        # Simple hash-based distance (0-1000 range)
        h1 = sum(ord(c) for c in origin)
        h2 = sum(ord(c) for c in destination)
        distance = abs(h1 - h2) + (h1 * h2) % 500 + 50
        return min(distance, 1000.0)

    @classmethod
    def total_cost(cls, shipments: list[dict]) -> float:
        """Calculate total cost for all shipments.

        Args:
            shipments: List of shipment dicts (must include 'cost' field).

        Returns:
            Total cost as a float.
        """
        return sum(s.get("cost", 0) for s in shipments)
