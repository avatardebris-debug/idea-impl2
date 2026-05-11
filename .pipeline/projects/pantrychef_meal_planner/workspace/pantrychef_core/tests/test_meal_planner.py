"""Tests for BasicMealPlanner."""

import pytest
from datetime import date

from pantrychef_core.models import PantryItem, Recipe, RecipeIngredient, MealPlan
from pantrychef_core.meal_planner import BasicMealPlanner


@pytest.fixture
def pantry():
    return [
        PantryItem(id=1, name="Eggs", quantity=12, unit="pieces", category="dairy"),
        PantryItem(id=2, name="Butter", quantity=200, unit="grams", category="dairy"),
        PantryItem(id=3, name="Milk", quantity=1, unit="liter", category="dairy"),
        PantryItem(id=4, name="Bread", quantity=1, unit="loaf", category="grains"),
        PantryItem(id=5, name="Tomato", quantity=3, unit="pieces", category="produce"),
        PantryItem(id=6, name="Chicken", quantity=500, unit="grams", category="meat"),
        PantryItem(id=7, name="Rice", quantity=1, unit="kg", category="grains"),
        PantryItem(id=8, name="Onion", quantity=2, unit="pieces", category="produce"),
        PantryItem(id=9, name="Garlic", quantity=5, unit="cloves", category="produce"),
        PantryItem(id=10, name="Salt", quantity=1, unit="kg", category="spice"),
    ]


@pytest.fixture
def recipes():
    return [
        Recipe(
            id=1, name="Scrambled Eggs", servings=2, prep_time=10,
            ingredients=[
                RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
                RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
                RecipeIngredient(name="milk", quantity=2, unit="tbsp"),
            ],
        ),
        Recipe(
            id=2, name="Tomato Soup", servings=4, prep_time=30,
            ingredients=[
                RecipeIngredient(name="tomato", quantity=3, unit="pieces"),
                RecipeIngredient(name="onion", quantity=1, unit="pieces"),
                RecipeIngredient(name="garlic", quantity=2, unit="cloves"),
            ],
        ),
        Recipe(
            id=3, name="Chicken Rice", servings=4, prep_time=45,
            ingredients=[
                RecipeIngredient(name="chicken", quantity=500, unit="grams"),
                RecipeIngredient(name="rice", quantity=2, unit="cups"),
                RecipeIngredient(name="onion", quantity=1, unit="pieces"),
                RecipeIngredient(name="garlic", quantity=2, unit="cloves"),
            ],
        ),
        Recipe(
            id=4, name="Toast", servings=1, prep_time=5,
            ingredients=[
                RecipeIngredient(name="bread", quantity=2, unit="slices"),
                RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
            ],
        ),
    ]


class TestGeneratePlan:
    def test_plan_has_three_meals(self, pantry, recipes):
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, recipes, date(2025, 6, 1))
        assert len(plans) == 3
        meal_types = [p.meal_type for p in plans]
        assert "breakfast" in meal_types
        assert "lunch" in meal_types
        assert "dinner" in meal_types

    def test_plan_entries_are_meal_plan_objects(self, pantry, recipes):
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, recipes, date(2025, 6, 1))
        for p in plans:
            assert isinstance(p, MealPlan)
            assert p.date == date(2025, 6, 1)

    def test_plan_uses_top_scoring_recipes(self, pantry, recipes):
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, recipes, date(2025, 6, 1))
        # All recipes should be fully cookable (score=1.0)
        for p in plans:
            assert p.score == pytest.approx(1.0)
            assert p.status == "fully_cookable"

    def test_no_duplicate_recipes(self, pantry, recipes):
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, recipes, date(2025, 6, 1))
        recipe_ids = [p.recipe_id for p in plans]
        assert len(recipe_ids) == len(set(recipe_ids))

    def test_empty_pantry(self, recipes):
        planner = BasicMealPlanner()
        plans = planner.generate_plan([], recipes, date(2025, 6, 1))
        assert plans == []

    def test_empty_recipes(self, pantry):
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, [], date(2025, 6, 1))
        assert plans == []

    def test_fewer_recipes_than_meals(self):
        pantry = [
            PantryItem(id=1, name="Eggs", quantity=1, unit="pieces", category="dairy"),
        ]
        recipes = [
            Recipe(
                id=1, name="Egg", servings=1, prep_time=5,
                ingredients=[RecipeIngredient(name="eggs", quantity=1, unit="pieces")],
            ),
        ]
        planner = BasicMealPlanner()
        plans = planner.generate_plan(pantry, recipes, date(2025, 6, 1))
        assert len(plans) == 1
        assert plans[0].meal_type == "breakfast"
