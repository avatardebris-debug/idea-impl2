"""RecipeMatcher — scored ingredient overlap algorithm."""

from __future__ import annotations

from typing import NamedTuple

from .models import PantryItem, Recipe


class MatchResult(NamedTuple):
    """A single recipe match result."""

    recipe: Recipe
    score: float
    status: str  # "fully_cookable", "mostly_cookable", "not_cookable"


class RecipeMatcher:
    """Score recipes against pantry items by ingredient overlap."""

    @staticmethod
    def match(
        pantry_items: list[PantryItem],
        recipes: list[Recipe],
    ) -> list[MatchResult]:
        """Return ranked list of (recipe, score, status) tuples.

        Score = fraction of recipe ingredients found in pantry (case-insensitive name match).
        Status thresholds:
          - >= 0.8: fully_cookable
          - >= 0.6: mostly_cookable
          - <  0.6: not_cookable
        """
        pantry_names = {item.name.lower() for item in pantry_items}
        results = []

        for recipe in recipes:
            if not recipe.ingredients:
                # Recipe with no ingredients is trivially fully cookable
                score = 1.0
            else:
                found = sum(
                    1 for ing in recipe.ingredients
                    if ing.name.lower() in pantry_names
                )
                score = found / len(recipe.ingredients)

            if score >= 0.8:
                status = "fully_cookable"
            elif score >= 0.6:
                status = "mostly_cookable"
            else:
                status = "not_cookable"

            results.append(MatchResult(recipe=recipe, score=score, status=status))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results
