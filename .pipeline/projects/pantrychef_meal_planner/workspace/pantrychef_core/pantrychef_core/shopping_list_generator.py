"""ShoppingListGenerator — computes delta between pantry and recipe needs."""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from .models import PantryItem, Recipe, ShoppingItem


class ShoppingListGenerator:
    """Given a meal plan's recipes and current pantry, produce a shopping list."""

    @staticmethod
    def _normalize_quantity(
        pantry_qty: float,
        pantry_unit: str,
        recipe_qty: float,
        recipe_unit: str,
    ) -> float:
        """Return recipe_qty in pantry_unit terms for comparison.

        For simplicity we assume 1:1 unit equivalence (e.g. 'cup' == 'cup',
        'kg' == 'kg').  Different-unit conversion is a future enhancement.
        """
        if pantry_unit == recipe_unit:
            return recipe_qty
        # If units differ we cannot convert — treat as fully missing.
        return recipe_qty

    @classmethod
    def generate(
        cls,
        pantry_items: list[PantryItem],
        recipes: list[Recipe],
        servings_map: Optional[dict[int, float]] = None,
    ) -> list[ShoppingItem]:
        """Compute what is missing from the pantry to cook *all* given recipes.

        Parameters
        ----------
        pantry_items :
            Current pantry inventory.
        recipes :
            Recipes to cook (each recipe's ingredients are summed).
        servings_map :
            Optional mapping of recipe_id -> servings multiplier.  If a recipe
            is cooked for 2x servings the ingredient needs double.

        Returns
        -------
        list[ShoppingItem]
            Deduplicated shopping list grouped by ingredient name.
        """
        servings_map = servings_map or {}

        # Accumulate total needed per ingredient (keyed by lowercase name).
        needed: dict[str, float] = defaultdict(float)
        needed_unit: dict[str, str] = {}

        for recipe in recipes:
            multiplier = servings_map.get(recipe.id, 1.0)
            for ing in recipe.ingredients:
                key = ing.name.lower()
                needed[key] += ing.quantity * multiplier
                needed_unit[key] = ing.unit

        # Subtract what we already have in the pantry.
        pantry_map: dict[str, float] = {}
        pantry_unit_map: dict[str, str] = {}
        for item in pantry_items:
            key = item.name.lower()
            pantry_map[key] = pantry_map.get(key, 0.0) + item.quantity
            pantry_unit_map[key] = item.unit

        shopping: list[ShoppingItem] = []
        for key, total_needed in needed.items():
            have = pantry_map.get(key, 0.0)
            deficit = total_needed - have
            if deficit > 0:
                shopping.append(
                    ShoppingItem(
                        name=key.title(),
                        quantity=round(deficit, 2),
                        unit=needed_unit[key],
                        source_recipe_ids=[
                            r.id for r in recipes if any(
                                ing.name.lower() == key for ing in r.ingredients
                            )
                        ],
                    )
                )

        return shopping
