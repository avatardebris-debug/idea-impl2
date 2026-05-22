"""Tests for PreferenceFilter."""

import pytest
from pantrychef_core.models import Recipe, RecipeIngredient
from pantrychef_core.preference_filter import PreferenceFilter


@pytest.fixture
def recipes():
    return [
        Recipe(
            id=1, name="Scrambled Eggs", servings=2, prep_time=10,
            ingredients=[], nutrition=[], dietary_tags=["vegetarian"],
        ),
        Recipe(
            id=2, name="Vegan Buddha Bowl", servings=2, prep_time=20,
            ingredients=[], nutrition=[],
            dietary_tags=["vegan", "vegetarian", "gluten-free", "dairy-free"],
        ),
        Recipe(
            id=3, name="Bacon & Eggs", servings=2, prep_time=15,
            ingredients=[], nutrition=[], dietary_tags=[],
        ),
        Recipe(
            id=4, name="Keto Chicken", servings=2, prep_time=25,
            ingredients=[], nutrition=[], dietary_tags=["keto", "gluten-free"],
        ),
        Recipe(
            id=5, name="Pasta Primavera", servings=4, prep_time=30,
            ingredients=[], nutrition=[], dietary_tags=["vegetarian"],
        ),
    ]


def test_filter_by_required_tags(recipes):
    """Filter recipes that have ALL required tags."""
    result = PreferenceFilter.filter_by_tags(
        recipes, required_tags=["vegetarian"]
    )
    names = {r.name for r in result}
    assert "Scrambled Eggs" in names
    assert "Vegan Buddha Bowl" in names
    assert "Pasta Primavera" in names
    assert "Bacon & Eggs" not in names
    assert "Keto Chicken" not in names


def test_filter_by_multiple_required_tags(recipes):
    """Filter recipes that have ALL required tags."""
    result = PreferenceFilter.filter_by_tags(
        recipes, required_tags=["vegan", "vegetarian"]
    )
    names = {r.name for r in result}
    assert names == {"Vegan Buddha Bowl"}


def test_filter_by_excluded_tags(recipes):
    """Filter recipes that have NONE of the excluded tags."""
    result = PreferenceFilter.filter_by_tags(
        recipes, excluded_tags=["vegetarian"]
    )
    names = {r.name for r in result}
    assert "Bacon & Eggs" in names
    assert "Keto Chicken" in names
    assert "Scrambled Eggs" not in names
    assert "Vegan Buddha Bowl" not in names
    assert "Pasta Primavera" not in names


def test_filter_by_both_required_and_excluded(recipes):
    """Filter with both required and excluded tags."""
    result = PreferenceFilter.filter_by_tags(
        recipes,
        required_tags=["gluten-free"],
        excluded_tags=["vegetarian"],
    )
    names = {r.name for r in result}
    assert names == {"Keto Chicken"}


def test_filter_no_tags(recipes):
    """No filter returns all recipes."""
    result = PreferenceFilter.filter_by_tags(recipes)
    assert len(result) == 5


def test_filter_empty_recipes():
    """Filter on empty list returns empty."""
    result = PreferenceFilter.filter_by_tags([], required_tags=["vegan"])
    assert result == []


def test_validate_tags():
    """Validate returns only known tags."""
    tags = ["vegan", "vegetarian", "unknown-tag", "gluten-free"]
    result = PreferenceFilter.validate_tags(tags)
    assert "vegan" in result
    assert "vegetarian" in result
    assert "gluten-free" in result
    assert "unknown-tag" not in result


def test_get_available_tags(recipes):
    """Get all available tags."""
    tags = PreferenceFilter.get_available_tags(recipes)
    assert "vegetarian" in tags
    assert "vegan" in tags
    assert "gluten-free" in tags
    assert "keto" in tags


def test_get_tag_counts(recipes):
    """Count recipes per tag."""
    counts = PreferenceFilter.get_tag_counts(recipes)
    assert counts["vegetarian"] == 3  # Eggs, Buddha Bowl, Pasta
    assert counts["vegan"] == 1
    assert counts["gluten-free"] == 2
    assert counts["keto"] == 1
