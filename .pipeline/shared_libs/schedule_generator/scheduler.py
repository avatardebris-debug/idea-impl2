"""Delivery schedule generator.

Produces an ordered delivery schedule sorted by priority (highest first)
with geographic grouping (shipments sharing the same destination are
grouped together).

Priority ordering (highest first):
    overnight > express > standard

Geographic grouping:
    Shipments with the same destination are grouped together.
    Within each group, shipments are sorted by priority (highest first),
    then by origin alphabetically for determinism.
"""

from typing import Any, Dict, List


# Priority rank: higher number = higher priority (comes first)
PRIORITY_RANK = {
    "overnight": 3,
    "express": 2,
    "standard": 1,
}


class ScheduleGenerator:
    """Generate an optimized delivery schedule from shipments."""

    @staticmethod
    def generate(shipments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a delivery schedule.

        Args:
            shipments: List of shipment dicts (as returned by Importer).

        Returns:
            List of scheduled delivery dicts, ordered by priority (highest
            first) with geographic grouping by destination.
        """
        if not shipments:
            return []

        # Group by destination
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for shipment in shipments:
            dest = shipment["destination"]
            groups.setdefault(dest, []).append(shipment)

        # Sort destinations alphabetically for determinism
        sorted_destinations = sorted(groups.keys())

        schedule: List[Dict[str, Any]] = []
        stop_number = 0

        for dest in sorted_destinations:
            group = groups[dest]
            # Sort within group: highest priority first, then origin alphabetically
            group.sort(
                key=lambda s: (
                    -PRIORITY_RANK.get(s["priority"], 0),
                    s["origin"].lower(),
                )
            )
            for shipment in group:
                stop_number += 1
                schedule.append({
                    "stop": stop_number,
                    "destination": dest,
                    "origin": shipment["origin"],
                    "priority": shipment["priority"],
                    "weight": shipment["weight"],
                    "length": shipment.get("length", 0),
                    "width": shipment.get("width", 0),
                    "height": shipment.get("height", 0),
                    "description": shipment.get("description", ""),
                })

        return schedule
