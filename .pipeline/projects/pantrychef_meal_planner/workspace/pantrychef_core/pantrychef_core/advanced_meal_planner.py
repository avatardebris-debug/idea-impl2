"""AdvancedMealPlanner — multi-day meal plans with constraints."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

from .models import MealPlan, PantryItem, Recipe
from .recipe_matcher import MatchResult, RecipeMatcher
from .preference_filter import PreferenceFilter


_MEAL_TYPES = ["breakfast", "lunch", "dinner"]


class AdvancedMealPlanner:
    """Generate multi-day meal plans with dietary constraints and calorie limits."""

    def __init__(
        self,
        recipes: list[Recipe],
        pantry_items: list[PantryItem],
        days: int = 7,
        dietary_tags: Optional[list[str]] = None,
        max_calories: Optional[dict[str, int]] = None,
        seed: Optional[int] = None,
    ):
        """
        Args:
            recipes: All available recipes.
            pantry_items: Current pantry inventory.
            days: Number of days to plan (default 7).
            dietary_tags: Filter recipes to only those with ALL these tags.
            max_calories: Per-meal-type calorie cap, e.g. {"lunch": 500, "dinner": 700}.
            seed: Random seed for reproducibility.
        """
        self.recipes = recipes
        self.pantry_items = pantry_items
        self.days = days
        self.dietary_tags = dietary_tags or []
        self.max_calories = max_calories or {}
        if seed is not None:
            random.seed(seed)

    def generate_plan(self) -> list[MealPlan]:
        """Generate a multi-day meal plan.

        Returns a list of MealPlan entries, one per meal per day.
        """
        # Filter recipes by dietary tags
        filtered = self._filter_by_dietary_tags(self.recipes)

        # Score all recipes against pantry
        scored = RecipeMatcher.match(self.pantry_items, filtered)

        # Group by meal type and apply calorie constraints
        plans: list[MealPlan] = []
        start_date = date.today()

        for day_offset in range(self.days):
            current_date = start_date + timedelta(days=day_offset)
            for meal_type in _MEAL_TYPES:
                candidates = self._get_candidates(scored, meal_type)
                selected = self._select_recipe(candidates, meal_type)
                if selected:
                    recipe, score, status = selected
                    meal = MealPlan(
                        date=current_date,
                        meal_type=meal_type,
                        recipe_id=recipe.id or 0,
                        recipe_name=recipe.name,
                        score=score,
                        status=status,
                    )
                    plans.append(meal)

        return plans

    def _filter_by_dietary_tags(self, recipes: list[Recipe]) -> list[Recipe]:
        """Filter recipes that have ALL required dietary tags."""
        if not self.dietary_tags:
            return recipes
        required = set(self.dietary_tags)
        return [r for r in recipes if required.issubset(set(r.dietary_tags))]

    def _get_candidates(
        self, scored: list[MatchResult], meal_type: str
    ) -> list[MatchResult]:
        """Get candidates for a meal type, applying calorie constraints."""
        candidates = list(scored)
        max_cal = self.max_calories.get(meal_type)
        if max_cal is not None:
            candidates = [
                m for m in candidates
                if self._recipe_calories(m.recipe) <= max_cal
            ]
        return candidates

    def _select_recipe(
        self, candidates: list[MatchResult], meal_type: str
    ) -> Optional[MatchResult]:
        """Select a recipe for a meal, preferring higher scores."""
        if not candidates:
            return None
        # Sort by score descending, pick top 3, then random among them
        candidates.sort(key=lambda m: m.score, reverse=True)
        top_n = candidates[: min(3, len(candidates))]
        return random.choice(top_n)

    def _recipe_calories(self, recipe: Recipe) -> float:
        """Get total calories for a recipe."""
        for n in recipe.nutrition:
            return n.calories * recipe.servings
        return 0.0
