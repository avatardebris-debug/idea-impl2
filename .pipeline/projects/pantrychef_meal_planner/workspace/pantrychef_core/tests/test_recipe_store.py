"""Tests for RecipeStore."""

import pytest

from pantrychef_core.database import Database
from pantrychef_core.models import Recipe, RecipeIngredient
from pantrychef_core.recipe_store import RecipeStore


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture
def rs(db):
    return RecipeStore(db)


@pytest.fixture
def sample_ingredients():
    return [
        RecipeIngredient(name="eggs", quantity=3, unit="pieces"),
        RecipeIngredient(name="butter", quantity=1, unit="tbsp"),
    ]


class TestAddRecipe:
    def test_add_recipe_returns_recipe(self, rs, sample_ingredients):
        recipe = rs.add_recipe("Scrambled Eggs", 2, 10, sample_ingredients)
        assert isinstance(recipe, Recipe)
        assert recipe.name == "Scrambled Eggs"
        assert recipe.servings == 2
        assert recipe.prep_time == 10
        assert len(recipe.ingredients) == 2

    def test_add_recipe_stores_ingredients(self, rs, sample_ingredients):
        recipe = rs.add_recipe("Test Recipe", 1, 5, sample_ingredients)
        ing_names = {i.name for i in recipe.ingredients}
        assert "eggs" in ing_names
        assert "butter" in ing_names


class TestGetRecipe:
    def test_get_existing_recipe(self, rs, sample_ingredients):
        recipe = rs.add_recipe("Pancakes", 4, 15, sample_ingredients)
        fetched = rs.get_recipe(recipe.id)
        assert fetched is not None
        assert fetched.name == "Pancakes"
        assert len(fetched.ingredients) == 2

    def test_get_nonexistent_recipe(self, rs):
        assert rs.get_recipe(9999) is None


class TestListRecipes:
    def test_list_empty(self, rs):
        assert rs.list_recipes() == []

    def test_list_multiple_recipes(self, rs, sample_ingredients):
        rs.add_recipe("Recipe A", 1, 5, sample_ingredients)
        rs.add_recipe("Recipe B", 2, 10, sample_ingredients)
        recipes = rs.list_recipes()
        assert len(recipes) == 2
        names = {r.name for r in recipes}
        assert "Recipe A" in names
        assert "Recipe B" in names
