"""NutritionTracker — aggregate nutritional info for recipes and meal plans."""

from __future__ import annotations

from typing import Optional

from .models import MealPlan, Recipe


class NutritionTracker:
    """Compute and aggregate nutrition for recipes and meal plans."""

    @staticmethod
    def recipe_nutrition(recipe: Recipe) -> dict[str, float]:
        """Return total nutrition for one recipe (all servings combined).

        Returns a dict of nutrient -> total value.
        """
        totals: dict[str, float] = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
        }
        for info in recipe.nutrition:
            totals["calories"] += info.calories
            totals["protein"] += info.protein
            totals["carbs"] += info.carbs
            totals["fat"] += info.fat
            totals["fiber"] += info.fiber
        return totals

    @staticmethod
    def per_serving_nutrition(recipe: Recipe) -> dict[str, float]:
        """Return per-serving nutrition for a recipe."""
        totals = NutritionTracker.recipe_nutrition(recipe)
        servings = recipe.servings or 1
        return {k: round(v / servings, 2) for k, v in totals.items()}

    @classmethod
    def meal_plan_nutrition(
        cls,
        meal_plan: list[MealPlan],
        recipe_map: dict[int, Recipe],
    ) -> dict[str, float]:
        """Aggregate nutrition across all meals in a plan.

        Parameters
        ----------
        meal_plan :
            List of MealPlan entries.
        recipe_map :
            Mapping of recipe_id -> Recipe object.

        Returns
        -------
        dict of nutrient -> total calories for the entire plan.
        """
        totals: dict[str, float] = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
        }
        for meal in meal_plan:
            recipe = recipe_map.get(meal.recipe_id)
            if recipe is None:
                continue
            per_serving = cls.per_serving_nutrition(recipe)
            servings = meal.servings or 1
            for nutrient, value in per_serving.items():
                totals[nutrient] += value * servings
        # Round final totals
        return {k: round(v, 2) for k, v in totals.items()}

    @classmethod
    def daily_summary(
        cls,
        meal_plan: list[MealPlan],
        recipe_map: dict[int, Recipe],
    ) -> dict[str, dict[str, float]]:
        """Return a per-meal-type summary of nutrition.

        Returns
        -------
        {meal_type: {nutrient: total}}
        """
        summary: dict[str, dict[str, float]] = {}
        for meal in meal_plan:
            recipe = recipe_map.get(meal.recipe_id)
            if recipe is None:
                continue
            per_serving = cls.per_serving_nutrition(recipe)
            servings = meal.servings or 1
            mt = meal.meal_type or "unknown"
            if mt not in summary:
                summary[mt] = {
                    "calories": 0.0,
                    "protein": 0.0,
                    "carbs": 0.0,
                    "fat": 0.0,
                    "fiber": 0.0,
                }
            for nutrient, value in per_serving.items():
                summary[mt][nutrient] += value * servings
        return {
            mt: {k: round(v, 2) for k, v in items.items()}
            for mt, items in summary.items()
        }
