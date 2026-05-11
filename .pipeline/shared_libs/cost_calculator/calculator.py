"""Routing cost calculator.

Cost formula (deterministic):
    base_cost = weight_kg * 2.50
    volume_m3 = (length_cm * width_cm * height_cm) / 1_000_000
    volume_cost = volume_m3 * 500.00
    distance_factor = 1.0 + (distance_km / 1000)   # $1 per 1000 km
    priority_multiplier:
        standard  -> 1.0
        express   -> 1.5
        overnight -> 2.5
    shipment_cost = (base_cost + volume_cost) * distance_factor * priority_multiplier

All distances are simulated via a simple hash-based lookup so the tool
works without external APIs.
"""

import hashlib
from typing import Any, Dict, List


# Priority multipliers
PRIORITY_MULTIPLIERS = {
    "standard": 1.0,
    "express": 1.5,
    "overnight": 2.5,
}

# Base cost per kg
BASE_COST_PER_KG = 2.50

# Volume cost per cubic meter
VOLUME_COST_PER_M3 = 500.00

# Distance cost per 1000 km
DISTANCE_COST_PER_1000KM = 1.0


def _simulate_distance_km(origin: str, destination: str) -> float:
    """Simulate a deterministic distance (km) between two locations.

    Uses a simple hash-based approach so the same pair always yields
    the same distance without external lookups.
    """
    # Normalize
    key = tuple(sorted([origin.lower().strip(), destination.lower().strip()]))
    # Deterministic hash-based distance between 50 and 5000 km
    h = int(hashlib.sha256(str(key).encode()).hexdigest(), 16)
    return 50.0 + h % 4951


class CostCalculator:
    """Calculate routing costs for a list of shipments."""

    @staticmethod
    def calculate(shipments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate costs for all shipments.

        Args:
            shipments: List of shipment dicts (as returned by Importer).

        Returns:
            Dict with keys:
                - per_shipment: list of dicts with cost details per shipment
                - total_cost: sum of all shipment costs
        """
        per_shipment: List[Dict[str, Any]] = []
        total_cost = 0.0

        for shipment in shipments:
            cost_details = CostCalculator._calculate_single(shipment)
            per_shipment.append(cost_details)
            total_cost += cost_details["cost"]

        return {
            "per_shipment": per_shipment,
            "total_cost": round(total_cost, 2),
        }

    @staticmethod
    def _calculate_single(shipment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost for a single shipment."""
        weight = shipment["weight"]
        length = shipment.get("length", 0) or 0
        width = shipment.get("width", 0) or 0
        height = shipment.get("height", 0) or 0
        priority = shipment["priority"]

        # Base cost
        base_cost = weight * BASE_COST_PER_KG

        # Volume cost
        volume_m3 = (length * width * height) / 1_000_000
        volume_cost = volume_m3 * VOLUME_COST_PER_M3

        # Distance factor
        distance_km = _simulate_distance_km(shipment["origin"], shipment["destination"])
        distance_factor = 1.0 + (distance_km / 1000) * DISTANCE_COST_PER_1000KM

        # Priority multiplier
        multiplier = PRIORITY_MULTIPLIERS.get(priority, 1.0)

        # Final cost
        cost = (base_cost + volume_cost) * distance_factor * multiplier

        return {
            "origin": shipment["origin"],
            "destination": shipment["destination"],
            "weight": weight,
            "priority": priority,
            "distance_km": round(distance_km, 2),
            "base_cost": round(base_cost, 2),
            "volume_cost": round(volume_cost, 2),
            "distance_factor": round(distance_factor, 4),
            "priority_multiplier": multiplier,
            "cost": round(cost, 2),
        }
