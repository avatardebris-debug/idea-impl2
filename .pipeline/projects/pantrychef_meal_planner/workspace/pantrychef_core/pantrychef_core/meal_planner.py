"""BasicMealPlanner — picks top-scoring recipes into a single-day meal plan."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .models import MealPlan, PantryItem, Recipe
from .recipe_matcher import RecipeMatcher


_MEAL_TYPES = ["breakfast", "lunch", "dinner"]


class BasicMealPlanner:
    """Generate a single-day meal plan from pantry-matched recipes."""

    def generate_plan(
        self,
        pantry_items: list[PantryItem],
        recipes: list[Recipe],
        plan_date: date,
    ) -> list[MealPlan]:
        """Return a list of MealPlan entries for the day.

        Picks top-scoring recipes from RecipeMatcher into breakfast, lunch, dinner.
        If fewer recipes are available, fewer meal slots are filled.
        """
        matches = RecipeMatcher.match(pantry_items, recipes)

        # Filter to fully_cookable and mostly_cookable, ranked by score
        cookable = [m for m in matches if m.status in ("fully_cookable", "mostly_cookable")]

        plans: list[MealPlan] = []
        used_recipe_ids: set[int] = set()

        for meal_type in _MEAL_TYPES:
            # Find the best available recipe for this meal
            for match in cookable:
                if match.recipe.id not in used_recipe_ids:
                    plan = MealPlan(
                        date=plan_date,
                        meal_type=meal_type,
                        recipe_id=match.recipe.id,
                        recipe_name=match.recipe.name,
                        servings=match.recipe.servings,
                        score=match.score,
                        status=match.status,
                    )
                    plans.append(plan)
                    used_recipe_ids.add(match.recipe.id)
                    break

        return plans
