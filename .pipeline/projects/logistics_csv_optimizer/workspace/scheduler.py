"""Schedule generator for logistics shipments.

Generates optimized schedules by:
- Grouping shipments by destination
- Sorting within groups by priority (overnight > express > standard)
- Sorting groups alphabetically by destination
"""


class ScheduleGenerator:
    """Generate optimized shipping schedules."""

    PRIORITY_ORDER = {
        "overnight": 0,
        "express": 1,
        "standard": 2,
    }

    @classmethod
    def generate(cls, entries: list[dict] | None) -> list[dict]:
        """Generate a schedule from a list of shipment entries.

        Args:
            entries: List of shipment dicts, or None.

        Returns:
            List of schedule entries sorted by destination (alphabetical),
            then by priority (overnight > express > standard).
        """
        if not entries:
            return []

        # Group by destination
        groups: dict[str, list[dict]] = {}
        for entry in entries:
            dest = entry.get("destination", "Unknown")
            if dest not in groups:
                groups[dest] = []
            groups[dest].append(entry)

        # Sort destinations alphabetically (case-insensitive)
        sorted_destinations = sorted(groups.keys(), key=str.lower)

        result = []
        for dest in sorted_destinations:
            group = groups[dest]
            # Sort within group by priority, then preserve original order for same priority
            group.sort(key=lambda e: cls.PRIORITY_ORDER.get(e.get("priority", "standard"), 99))
            result.extend(group)

        return result
