"""Tests for AdvancedMealPlanner."""

import pytest
from datetime import date

from pantrychef_core.models import PantryItem, Recipe, RecipeIngredient, MealPlan
from pantrychef_core.advanced_meal_planner import AdvancedMealPlanner


@pytest.fixture
def pantry():
    return [
        PantryItem(id=1, name="Eggs", quantity=12, unit="pieces", category="dairy"),
        PantryItem(id=2, name="Butter", quantity=200, unit="grams", category="dairy"),
        PantryItem(id=3, name="Milk", quantity=1, unit="liter", category="dairy"),
        PantryItem(id=4, name="Flour", quantity=500, unit="grams", category="grain"),
        PantryItem(id=5, name="Sugar", quantity=300, unit="grams", category="sweetener"),
        PantryItem(id=6, name="Bacon", quantity=200, unit="grams", category="meat"),
        PantryItem(id=7, name="Tomato", quantity=5, unit="pieces", category="vegetable"),
        PantryItem(id=8, name="Onion", quantity=3, unit="pieces", category="vegetable"),
        PantryItem(id=9, name="Chicken breast", quantity=500, unit="grams", category="meat"),
        PantryItem(id=10, name="Rice", quantity=1000, unit="grams", category="grain"),
    ]


@pytest.fixture
def recipes():
    return [
        Recipe(
            id=1, name="Scrambled Eggs", servings=2, prep_time=10,
            ingredients=[
                RecipeIngredient(name="Eggs", quantity=4, unit="pieces"),
                RecipeIngredient(name="Butter", quantity=20, unit="grams"),
                RecipeIngredient(name="Milk", quantity=50, unit="ml"),
            ],
            nutrition=[],
            dietary_tags=["vegetarian"],
        ),
        Recipe(
            id=2, name="Pancakes", servings=4, prep_time=20,
            ingredients=[
                RecipeIngredient(name="Flour", quantity=200, unit="grams"),
                RecipeIngredient(name="Eggs", quantity=2, unit="pieces"),
                RecipeIngredient(name="Milk", quantity=300, unit="ml"),
                RecipeIngredient(name="Sugar", quantity=30, unit="grams"),
                RecipeIngredient(name="Butter", quantity=30, unit="grams"),
            ],
            nutrition=[],
            dietary_tags=["vegetarian"],
        ),
        Recipe(
            id=3, name="Bacon & Eggs", servings=2, prep_time=15,
            ingredients=[
                RecipeIngredient(name="Bacon", quantity=150, unit="grams"),
                RecipeIngredient(name="Eggs", quantity=4, unit="pieces"),
            ],
            nutrition=[],
            dietary_tags=[],
        ),
        Recipe(
            id=4, name="Chicken Stir-Fry", servings=3, prep_time=25,
            ingredients=[
                RecipeIngredient(name="Chicken breast", quantity=300, unit="grams"),
                RecipeIngredient(name="Rice", quantity=200, unit="grams"),
                RecipeIngredient(name="Tomato", quantity=2, unit="pieces"),
                RecipeIngredient(name="Onion", quantity=1, unit="pieces"),
            ],
            nutrition=[],
            dietary_tags=["gluten-free", "dairy-free"],
        ),
        Recipe(
            id=5, name="Tomato Soup", servings=4, prep_time=30,
            ingredients=[
                RecipeIngredient(name="Tomato", quantity=6, unit="pieces"),
                RecipeIngredient(name="Onion", quantity=2, unit="pieces"),
                RecipeIngredient(name="Butter", quantity=30, unit="grams"),
            ],
            nutrition=[],
            dietary_tags=["vegetarian", "gluten-free"],
        ),
        Recipe(
            id=6, name="Vegan Buddha Bowl", servings=2, prep_time=20,
            ingredients=[
                RecipeIngredient(name="Rice", quantity=200, unit="grams"),
                RecipeIngredient(name="Tomato", quantity=2, unit="pieces"),
                RecipeIngredient(name="Onion", quantity=1, unit="pieces"),
            ],
            nutrition=[],
            dietary_tags=["vegan", "vegetarian", "gluten-free", "dairy-free"],
        ),
    ]


def test_generate_7_day_plan(pantry, recipes):
    """Generate a 7-day meal plan."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=7, seed=42
    )
    plans = planner.generate_plan()
    # 7 days * 3 meals = 21
    assert len(plans) == 21
    # Check meal types are present
    meal_types = {p.meal_type for p in plans}
    assert meal_types == {"breakfast", "lunch", "dinner"}


def test_generate_3_day_plan(pantry, recipes):
    """Generate a 3-day meal plan."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=3, seed=42
    )
    plans = planner.generate_plan()
    assert len(plans) == 9  # 3 days * 3 meals


def test_dietary_filter_vegetarian(pantry, recipes):
    """Filter to vegetarian recipes only."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=3,
        dietary_tags=["vegetarian"], seed=42
    )
    plans = planner.generate_plan()
    recipe_names = {p.recipe_name for p in plans}
    # All selected recipes should be vegetarian
    for r in recipes:
        if r.name in recipe_names:
            assert "vegetarian" in r.dietary_tags


def test_dietary_filter_vegan(pantry, recipes):
    """Filter to vegan recipes only."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=3,
        dietary_tags=["vegan"], seed=42
    )
    plans = planner.generate_plan()
    # Only recipe 6 is vegan
    recipe_names = {p.recipe_name for p in plans}
    for name in recipe_names:
        recipe = next(r for r in recipes if r.name == name)
        assert "vegan" in recipe.dietary_tags


def test_calorie_constraint(pantry, recipes):
    """Apply calorie constraints."""
    # Add nutrition data to recipes
    recipes_with_nutrition = []
    for r in recipes:
        r_copy = r.model_copy()
        r_copy.nutrition = [
            type('NutritionalInfo', (), {'calories': 300})()
        ]
        recipes_with_nutrition.append(r_copy)

    # Set max calories for lunch to 200 (should filter out 300-cal recipes)
    planner = AdvancedMealPlanner(
        recipes=recipes_with_nutrition, pantry_items=pantry, days=3,
        max_calories={"lunch": 200}, seed=42
    )
    plans = planner.generate_plan()
    lunch_plans = [p for p in plans if p.meal_type == "lunch"]
    # With 300-cal recipes and 200 max, lunch should have no recipes
    assert len(lunch_plans) == 0 or all(p.recipe_name == "" for p in lunch_plans)


def test_reproducibility(pantry, recipes):
    """Same seed produces same plan."""
    planner1 = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=3, seed=42
    )
    plans1 = planner1.generate_plan()

    planner2 = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=3, seed=42
    )
    plans2 = planner2.generate_plan()

    assert len(plans1) == len(plans2)
    for p1, p2 in zip(plans1, plans2):
        assert p1.recipe_name == p2.recipe_name


def test_empty_pantry(pantry, recipes):
    """Generate plan with empty pantry."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=[], days=3, seed=42
    )
    plans = planner.generate_plan()
    # Should still generate plans (status will indicate missing ingredients)
    assert len(plans) == 9


def test_single_day(pantry, recipes):
    """Generate a single day plan."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=1, seed=42
    )
    plans = planner.generate_plan()
    assert len(plans) == 3  # breakfast, lunch, dinner


def test_meal_plan_structure(pantry, recipes):
    """Check meal plan entry structure."""
    planner = AdvancedMealPlanner(
        recipes=recipes, pantry_items=pantry, days=1, seed=42
    )
    plans = planner.generate_plan()
    for plan in plans:
        assert isinstance(plan, MealPlan)
        assert plan.meal_type in ["breakfast", "lunch", "dinner"]
        assert isinstance(plan.score, float)
        assert plan.status in ["fully_cookable", "mostly_cookable", "not_cookable"]
