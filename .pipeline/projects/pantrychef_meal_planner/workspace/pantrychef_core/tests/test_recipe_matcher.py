"""Tests for RecipeMatcher — aims for ≥80% branch coverage."""

import pytest

from pantrychef_core.models import PantryItem, Recipe, RecipeIngredient
from pantrychef_core.recipe_matcher import RecipeMatcher, MatchResult


@pytest.fixture
def pantry_eggs_butter_milk():
    return [
        PantryItem(id=1, name="Eggs", quantity=12, unit="pieces", category="dairy"),
        PantryItem(id=2, name="Butter", quantity=200, unit="grams", category="dairy"),
        PantryItem(id=3, name="Milk", quantity=1, unit="liter", category="dairy"),
    ]


@pytest.fixture
def recipe_scrambled_eggs():
    return Recipe(
        id=1,
        name="Scrambled Eggs",
        servings=2,
        prep_time=10,
        ingredients=[
            RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
            RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
            RecipeIngredient(name="milk", quantity=2, unit="tbsp"),
        ],
    )


@pytest.fixture
def recipe_missing_ingredient():
    return Recipe(
        id=2,
        name="Omelette",
        servings=1,
        prep_time=15,
        ingredients=[
            RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
            RecipeIngredient(name="cheese", quantity=50, unit="grams"),
        ],
    )


@pytest.fixture
def recipe_no_ingredients():
    return Recipe(
        id=3,
        name="Water",
        servings=1,
        prep_time=0,
        ingredients=[],
    )


class TestMatch:
    def test_fully_cookable(self, pantry_eggs_butter_milk, recipe_scrambled_eggs):
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [recipe_scrambled_eggs])
        assert len(results) == 1
        assert results[0].score == 1.0
        assert results[0].status == "fully_cookable"

    def test_mostly_cookable(self, pantry_eggs_butter_milk):
        """Score between 0.6 and 0.8 should be mostly_cookable."""
        recipe = Recipe(
            id=1,
            name="Omelette",
            servings=1,
            prep_time=15,
            ingredients=[
                RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
                RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
                RecipeIngredient(name="cheese", quantity=50, unit="grams"),
            ],
        )
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [recipe])
        assert len(results) == 1
        assert results[0].score == pytest.approx(2/3)  # 2/3
        assert results[0].status == "mostly_cookable"

    def test_mostly_cookable_boundary(self, pantry_eggs_butter_milk):
        """Score exactly 0.6 should be mostly_cookable."""
        recipe = Recipe(
            id=1,
            name="Test",
            servings=1,
            prep_time=5,
            ingredients=[
                RecipeIngredient(name="eggs", quantity=1, unit="pieces"),
                RecipeIngredient(name="cheese", quantity=1, unit="grams"),
                RecipeIngredient(name="ham", quantity=1, unit="grams"),
                RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
                RecipeIngredient(name="milk", quantity=1, unit="tbsp"),
            ],
        )
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [recipe])
        assert len(results) == 1
        assert results[0].score == pytest.approx(0.6)  # 3/5
        assert results[0].status == "mostly_cookable"

    def test_not_cookable(self):
        pantry = [PantryItem(id=1, name="Flour", quantity=1, unit="kg", category="grains")]
        recipe = Recipe(
            id=1,
            name="Cake",
            servings=8,
            prep_time=60,
            ingredients=[
                RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
                RecipeIngredient(name="sugar", quantity=200, unit="grams"),
            ],
        )
        results = RecipeMatcher.match(pantry, [recipe])
        assert results[0].score == 0.0
        assert results[0].status == "not_cookable"

    def test_no_ingredients_recipe(self, pantry_eggs_butter_milk, recipe_no_ingredients):
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [recipe_no_ingredients])
        assert results[0].score == 1.0
        assert results[0].status == "fully_cookable"

    def test_case_insensitive_match(self):
        pantry = [PantryItem(id=1, name="EGGS", quantity=1, unit="pieces", category="dairy")]
        recipe = Recipe(
            id=1,
            name="Test",
            servings=1,
            prep_time=5,
            ingredients=[RecipeIngredient(name="eggs", quantity=1, unit="pieces")],
        )
        results = RecipeMatcher.match(pantry, [recipe])
        assert results[0].score == 1.0

    def test_ranked_by_score(self, pantry_eggs_butter_milk):
        recipe_full = Recipe(
            id=1, name="Full", servings=1, prep_time=5,
            ingredients=[RecipeIngredient(name="eggs", quantity=1, unit="pieces")],
        )
        recipe_partial = Recipe(
            id=2, name="Partial", servings=1, prep_time=5,
            ingredients=[
                RecipeIngredient(name="eggs", quantity=1, unit="pieces"),
                RecipeIngredient(name="cheese", quantity=1, unit="grams"),
            ],
        )
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [recipe_partial, recipe_full])
        assert results[0].recipe.id == 1  # Full score first
        assert results[1].recipe.id == 2

    def test_empty_pantry(self):
        results = RecipeMatcher.match([], [Recipe(
            id=1, name="Test", servings=1, prep_time=5,
            ingredients=[RecipeIngredient(name="eggs", quantity=1, unit="pieces")],
        )])
        assert results[0].score == 0.0
        assert results[0].status == "not_cookable"

    def test_empty_recipes(self, pantry_eggs_butter_milk):
        results = RecipeMatcher.match(pantry_eggs_butter_milk, [])
        assert results == []

    def test_boundary_score_0_8(self):
        """Score exactly 0.8 should be fully_cookable."""
        pantry = [
            PantryItem(id=1, name="A", quantity=1, unit="unit", category="test"),
            PantryItem(id=2, name="B", quantity=1, unit="unit", category="test"),
            PantryItem(id=3, name="C", quantity=1, unit="unit", category="test"),
            PantryItem(id=4, name="D", quantity=1, unit="unit", category="test"),
            PantryItem(id=5, name="E", quantity=1, unit="unit", category="test"),
            PantryItem(id=6, name="F", quantity=1, unit="unit", category="test"),
            PantryItem(id=7, name="G", quantity=1, unit="unit", category="test"),
            PantryItem(id=8, name="H", quantity=1, unit="unit", category="test"),
        ]
        recipe = Recipe(
            id=1, name="Test", servings=1, prep_time=5,
            ingredients=[RecipeIngredient(name=n, quantity=1, unit="unit") for n in "ABCDEFGH"],
        )
        results = RecipeMatcher.match(pantry, [recipe])
        assert results[0].score == 1.0
        assert results[0].status == "fully_cookable"

    def test_boundary_score_0_6(self):
        """Score exactly 0.6 should be mostly_cookable."""
        pantry = [
            PantryItem(id=1, name="A", quantity=1, unit="unit", category="test"),
            PantryItem(id=2, name="B", quantity=1, unit="unit", category="test"),
            PantryItem(id=3, name="C", quantity=1, unit="unit", category="test"),
        ]
        recipe = Recipe(
            id=1, name="Test", servings=1, prep_time=5,
            ingredients=[RecipeIngredient(name=n, quantity=1, unit="unit") for n in "ABCDE"],
        )
        results = RecipeMatcher.match(pantry, [recipe])
        assert results[0].score == pytest.approx(0.6)  # 3/5
        assert results[0].status == "mostly_cookable"
