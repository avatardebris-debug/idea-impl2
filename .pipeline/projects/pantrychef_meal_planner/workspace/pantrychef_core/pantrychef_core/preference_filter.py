"""PreferenceFilter — dietary tag filtering for recipes."""

from __future__ import annotations

from typing import Optional

from .models import Recipe


# Valid dietary tags
VALID_TAGS = {
    "vegan",
    "vegetarian",
    "gluten-free",
    "dairy-free",
    "nut-free",
    "keto",
    "paleo",
    "low-carb",
    "high-protein",
    "pescatarian",
}


class PreferenceFilter:
    """Filter recipes by dietary preferences and other constraints."""

    @staticmethod
    def filter_by_tags(
        recipes: list[Recipe],
        required_tags: Optional[list[str]] = None,
        excluded_tags: Optional[list[str]] = None,
    ) -> list[Recipe]:
        """Filter recipes by required and excluded dietary tags.

        Args:
            recipes: All recipes to filter.
            required_tags: Recipe must have ALL of these tags.
            excluded_tags: Recipe must have NONE of these tags.

        Returns:
            Filtered list of recipes.
        """
        result = recipes

        if required_tags:
            required = set(required_tags)
            result = [r for r in result if required.issubset(set(r.dietary_tags))]

        if excluded_tags:
            excluded = set(excluded_tags)
            result = [r for r in result if not excluded.intersection(set(r.dietary_tags))]

        return result

    @staticmethod
    def validate_tags(tags: list[str]) -> list[str]:
        """Validate dietary tags, returning only known tags."""
        return [t for t in tags if t in VALID_TAGS]

    @staticmethod
    def get_available_tags(recipes: list[Recipe]) -> set[str]:
        """Get all dietary tags available across recipes."""
        tags = set()
        for r in recipes:
            tags.update(r.dietary_tags)
        return tags

    @staticmethod
    def get_tag_counts(recipes: list[Recipe]) -> dict[str, int]:
        """Count how many recipes have each dietary tag."""
        counts: dict[str, int] = {}
        for r in recipes:
            for tag in r.dietary_tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts
