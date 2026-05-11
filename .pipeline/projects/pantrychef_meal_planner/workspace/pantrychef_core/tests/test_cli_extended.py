"""Extended CLI tests covering all code paths in cli.py."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from pantrychef_core.cli import cli
from pantrychef_core.database import Database
from pantrychef_core.pantry_manager import PantryManager
from pantrychef_core.recipe_store import RecipeStore


class TestAddPantryItemCLI:
    """Test the add-pantry-item CLI command."""

    def test_add_pantry_item_no_expiry(self):
        """Add item without expiry date — covers expiry_date=None branch."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_db = MockDB.return_value
            mock_pm = MagicMock()
            mock_item = MagicMock()
            mock_item.name = "Flour"
            mock_item.quantity = 5.0
            mock_item.unit = "kg"
            mock_pm.add_item.return_value = mock_item
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                result = runner.invoke(cli, [
                    "add-pantry-item",
                    "--name", "Flour",
                    "--quantity", "5",
                    "--unit", "kg",
                    "--category", "grains",
                ])
        assert result.exit_code == 0
        assert "Added pantry item: Flour" in result.output

    def test_add_pantry_item_with_expiry(self):
        """Add item with expiry date — covers expiry_date=fromisoformat branch."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_db = MockDB.return_value
            mock_pm = MagicMock()
            mock_item = MagicMock()
            mock_item.name = "Yogurt"
            mock_item.quantity = 2.0
            mock_item.unit = "cups"
            mock_pm.add_item.return_value = mock_item
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                result = runner.invoke(cli, [
                    "add-pantry-item",
                    "--name", "Yogurt",
                    "--quantity", "2",
                    "--unit", "cups",
                    "--category", "dairy",
                    "--expiry-date", "2025-08-15",
                ])
        assert result.exit_code == 0
        assert "Added pantry item: Yogurt" in result.output

    def test_add_pantry_item_missing_required_name(self):
        """Missing --name should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-pantry-item", "--quantity", "1", "--unit", "kg", "--category", "grains"
        ])
        assert result.exit_code != 0

    def test_add_pantry_item_missing_required_quantity(self):
        """Missing --quantity should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-pantry-item", "--name", "Flour", "--unit", "kg", "--category", "grains"
        ])
        assert result.exit_code != 0

    def test_add_pantry_item_missing_required_unit(self):
        """Missing --unit should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-pantry-item", "--name", "Flour", "--quantity", "1", "--category", "grains"
        ])
        assert result.exit_code != 0

    def test_add_pantry_item_missing_required_category(self):
        """Missing --category should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-pantry-item", "--name", "Flour", "--quantity", "1", "--unit", "kg"
        ])
        assert result.exit_code != 0

    def test_add_pantry_item_invalid_quantity(self):
        """Invalid quantity should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-pantry-item", "--name", "Flour", "--quantity", "abc",
            "--unit", "kg", "--category", "grains"
        ])
        assert result.exit_code != 0

    def test_add_pantry_item_calls_database(self):
        """Verify Database is instantiated."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_pm = MagicMock()
            mock_item = MagicMock()
            mock_item.name = "Rice"
            mock_item.quantity = 10.0
            mock_item.unit = "kg"
            mock_pm.add_item.return_value = mock_item
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                runner.invoke(cli, [
                    "add-pantry-item", "--name", "Rice", "--quantity", "10",
                    "--unit", "kg", "--category", "grains"
                ])
            MockDB.assert_called_once()


class TestAddRecipeCLI:
    """Test the add-recipe CLI command."""

    def test_add_recipe_success(self):
        """Add a valid recipe."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_rs = MagicMock()
            mock_recipe = MagicMock()
            mock_recipe.name = "Pasta"
            mock_recipe.id = 1
            mock_rs.add_recipe.return_value = mock_recipe
            with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                result = runner.invoke(cli, [
                    "add-recipe",
                    "--name", "Pasta",
                    "--servings", "4",
                    "--prep-time", "20",
                    "--ingredients", "pasta:500:grams,tomato_sauce:2:cups,garlic:3:cloves",
                ])
        assert result.exit_code == 0
        assert "Added recipe: Pasta" in result.output

    def test_add_recipe_single_ingredient(self):
        """Add a recipe with a single ingredient."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_rs = MagicMock()
            mock_recipe = MagicMock()
            mock_recipe.name = "Simple Salad"
            mock_recipe.id = 2
            mock_rs.add_recipe.return_value = mock_recipe
            with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                result = runner.invoke(cli, [
                    "add-recipe",
                    "--name", "Simple Salad",
                    "--servings", "1",
                    "--prep-time", "5",
                    "--ingredients", "lettuce:1:head",
                ])
        assert result.exit_code == 0
        assert "Added recipe: Simple Salad" in result.output

    def test_add_recipe_invalid_ingredient_format(self):
        """Invalid ingredient format should exit with code 1."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe",
            "--name", "Bad Recipe",
            "--servings", "1",
            "--prep-time", "5",
            "--ingredients", "bad_format",
        ])
        assert result.exit_code == 1
        assert "Error: invalid ingredient format" in result.output

    def test_add_recipe_missing_name(self):
        """Missing --name should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe", "--servings", "1", "--prep-time", "5",
            "--ingredients", "a:1:b"
        ])
        assert result.exit_code != 0

    def test_add_recipe_missing_servings(self):
        """Missing --servings should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe", "--name", "Test", "--prep-time", "5",
            "--ingredients", "a:1:b"
        ])
        assert result.exit_code != 0

    def test_add_recipe_missing_prep_time(self):
        """Missing --prep-time should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe", "--name", "Test", "--servings", "1",
            "--ingredients", "a:1:b"
        ])
        assert result.exit_code != 0

    def test_add_recipe_missing_ingredients(self):
        """Missing --ingredients should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe", "--name", "Test", "--servings", "1", "--prep-time", "5"
        ])
        assert result.exit_code != 0

    def test_add_recipe_invalid_servings_type(self):
        """Non-integer servings should cause Click to error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add-recipe", "--name", "Test", "--servings", "abc",
            "--prep-time", "5", "--ingredients", "a:1:b"
        ])
        assert result.exit_code != 0

    def test_add_recipe_calls_database(self):
        """Verify Database is instantiated."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_rs = MagicMock()
            mock_recipe = MagicMock()
            mock_recipe.name = "Omelette"
            mock_recipe.id = 3
            mock_rs.add_recipe.return_value = mock_recipe
            with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                runner.invoke(cli, [
                    "add-recipe", "--name", "Omelette", "--servings", "2",
                    "--prep-time", "15", "--ingredients", "eggs:4:pieces,cheese:50:grams"
                ])
            MockDB.assert_called_once()


class TestPlanCLI:
    """Test the plan CLI command."""

    def test_plan_empty_pantry(self):
        """Plan with empty pantry should error."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_pm = MagicMock()
            mock_pm.list_items.return_value = []
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                result = runner.invoke(cli, ["plan"])
        assert result.exit_code == 1
        assert "pantry is empty" in result.output.lower()

    def test_plan_no_recipes(self):
        """Plan with pantry but no recipes should error."""
        runner = CliRunner()
        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_pm = MagicMock()
            mock_pm.list_items.return_value = [MagicMock()]
            mock_rs = MagicMock()
            mock_rs.list_recipes.return_value = []
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                    result = runner.invoke(cli, ["plan"])
        assert result.exit_code == 1
        assert "no recipes available" in result.output.lower()

    def test_plan_with_data(self):
        """Plan with pantry and recipes should succeed."""
        runner = CliRunner()
        mock_pantry_item = MagicMock()
        mock_recipe = MagicMock()
        mock_recipe.name = "Scrambled Eggs"
        mock_recipe.ingredients = [
            MagicMock(name="eggs", quantity=3, unit="pieces"),
            MagicMock(name="butter", quantity=1, unit="tbsp"),
        ]
        mock_plan = MagicMock()
        mock_plan.meal_type = "breakfast"
        mock_plan.recipe_name = "Scrambled Eggs"
        mock_plan.score = 1.0
        mock_plan.status = "fully_cookable"

        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_pm = MagicMock()
            mock_pm.list_items.return_value = [mock_pantry_item]
            mock_rs = MagicMock()
            mock_rs.list_recipes.return_value = [mock_recipe]
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                    with patch("pantrychef_core.cli.BasicMealPlanner") as MockPlanner:
                        mock_planner = MagicMock()
                        mock_planner.generate_plan.return_value = [mock_plan]
                        MockPlanner.return_value = mock_planner
                        result = runner.invoke(cli, ["plan"])
        assert result.exit_code == 0
        assert "Meal Plan" in result.output
        assert "Scrambled Eggs" in result.output

    def test_plan_no_cookable_recipes(self):
        """Plan with pantry and recipes but no match should show message."""
        runner = CliRunner()
        mock_pantry_item = MagicMock()
        mock_recipe = MagicMock()
        mock_recipe.name = "Pasta"
        mock_recipe.ingredients = [
            MagicMock(name="pasta", quantity=500, unit="grams"),
        ]

        with patch("pantrychef_core.cli.Database") as MockDB:
            mock_pm = MagicMock()
            mock_pm.list_items.return_value = [mock_pantry_item]
            mock_rs = MagicMock()
            mock_rs.list_recipes.return_value = [mock_recipe]
            with patch("pantrychef_core.cli.PantryManager", return_value=mock_pm):
                with patch("pantrychef_core.cli.RecipeStore", return_value=mock_rs):
                    with patch("pantrychef_core.cli.BasicMealPlanner") as MockPlanner:
                        mock_planner = MagicMock()
                        mock_planner.generate_plan.return_value = []
                        MockPlanner.return_value = mock_planner
                        result = runner.invoke(cli, ["plan"])
        assert result.exit_code == 0
        assert "No cookable recipes found" in result.output


class TestCLIMain:
    """Test the main CLI entry point."""

    def test_cli_help(self):
        """--help should show usage info."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PantryChef" in result.output
        assert "add-pantry-item" in result.output
        assert "add-recipe" in result.output
        assert "plan" in result.output

    def test_cli_add_pantry_item_help(self):
        """add-pantry-item --help should show options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-pantry-item", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--quantity" in result.output
        assert "--unit" in result.output
        assert "--category" in result.output
        assert "--expiry-date" in result.output

    def test_cli_add_recipe_help(self):
        """add-recipe --help should show options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-recipe", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--servings" in result.output
        assert "--prep-time" in result.output
        assert "--ingredients" in result.output

    def test_cli_plan_help(self):
        """plan --help should show options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["plan", "--help"])
        assert result.exit_code == 0

    def test_cli_unknown_command(self):
        """Unknown command should error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["unknown-command"])
        assert result.exit_code != 0

    def test_cli_main_entry_point(self):
        """Verify __main__ entry point exists."""
        import pantrychef_core.cli as cli_module
        assert hasattr(cli_module, "cli")
        assert callable(cli_module.cli)
