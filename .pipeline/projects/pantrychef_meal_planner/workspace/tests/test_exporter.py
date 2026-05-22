"""Tests for Exporter."""

import pytest
import json
from pantrychef_core.models import MealPlan, ShoppingItem
from pantrychef_core.exporter import Exporter


@pytest.fixture
def meal_plans():
    from datetime import date
    return [
        MealPlan(date=date(2025, 1, 1), meal_type="breakfast", recipe_id=1,
                 recipe_name="Scrambled Eggs", score=0.85, status="available"),
        MealPlan(date=date(2025, 1, 1), meal_type="lunch", recipe_id=2,
                 recipe_name="Chicken Stir-Fry", score=0.72, status="partial"),
        MealPlan(date=date(2025, 1, 2), meal_type="dinner", recipe_id=3,
                 recipe_name="Vegan Buddha Bowl", score=0.91, status="available"),
    ]


@pytest.fixture
def shopping_items():
    return [
        ShoppingItem(name="Eggs", quantity=6, unit="pieces", source_recipe_ids=[1, 2]),
        ShoppingItem(name="Rice", quantity=400, unit="grams", source_recipe_ids=[2]),
        ShoppingItem(name="Tomato", quantity=4, unit="pieces", source_recipe_ids=[3]),
    ]


def test_meal_plan_to_csv(meal_plans):
    """Export meal plan to CSV."""
    csv_data = Exporter.meal_plan_to_csv(meal_plans)
    lines = csv_data.strip().split("\n")
    assert len(lines) == 4  # header + 3 rows
    assert "date" in lines[0]
    assert "recipe_name" in lines[0]
    assert "Scrambled Eggs" in lines[1]


def test_meal_plan_to_markdown(meal_plans):
    """Export meal plan to Markdown."""
    md_data = Exporter.meal_plan_to_markdown(meal_plans)
    assert "# Meal Plan" in md_data
    assert "## 2025-01-01" in md_data
    assert "## 2025-01-02" in md_data
    assert "Scrambled Eggs" in md_data
    assert "| Meal Type |" in md_data


def test_shopping_list_to_csv(shopping_items):
    """Export shopping list to CSV."""
    csv_data = Exporter.shopping_list_to_csv(shopping_items)
    lines = csv_data.strip().split("\n")
    assert len(lines) == 4  # header + 3 rows
    assert "name" in lines[0]
    assert "Eggs" in lines[1]


def test_shopping_list_to_markdown(shopping_items):
    """Export shopping list to Markdown."""
    md_data = Exporter.shopping_list_to_markdown(shopping_items)
    assert "# Shopping List" in md_data
    assert "Eggs" in md_data
    assert "Rice" in md_data
    assert "| Item |" in md_data


def test_meal_plan_to_json(meal_plans):
    """Export meal plan to JSON."""
    json_data = Exporter.meal_plan_to_json(meal_plans)
    data = json.loads(json_data)
    assert len(data) == 3
    assert data[0]["recipe_name"] == "Scrambled Eggs"
    assert data[0]["score"] == 0.85
