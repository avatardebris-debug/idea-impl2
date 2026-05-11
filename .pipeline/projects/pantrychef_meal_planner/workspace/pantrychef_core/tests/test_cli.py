"""Tests for CLI commands."""

import subprocess
import sys
import tempfile
import os

from click.testing import CliRunner

from pantrychef_core.cli import cli


def _run_cli(*args):
    """Run the CLI as a subprocess and return (stdout, stderr, returncode)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "pantrychef_test.db")
        result = subprocess.run(
            [sys.executable, "-m", "pantrychef_core.cli"] + list(args),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env={**os.environ, "PANTRYCHEF_DB": db_path},
        )
        return result.stdout, result.stderr, result.returncode


class TestCLIPantryItem:
    def test_add_pantry_item_success(self):
        """Adding a pantry item should succeed."""
        stdout, stderr, rc = _run_cli(
            "add-pantry-item",
            "--name", "Eggs",
            "--quantity", "12",
            "--unit", "pieces",
            "--category", "dairy",
        )
        assert rc == 0
        assert "Added pantry item: Eggs" in stdout

    def test_add_pantry_item_with_expiry(self):
        """Adding a pantry item with expiry date should succeed."""
        stdout, stderr, rc = _run_cli(
            "add-pantry-item",
            "--name", "Milk",
            "--quantity", "1",
            "--unit", "liter",
            "--category", "dairy",
            "--expiry-date", "2025-12-31",
        )
        assert rc == 0
        assert "Added pantry item: Milk" in stdout

    def test_add_pantry_item_missing_name(self):
        """Missing required --name should fail."""
        result = CliRunner().invoke(
            cli,
            ["add-pantry-item", "--quantity", "1", "--unit", "pieces", "--category", "dairy"],
        )
        assert result.exit_code != 0


class CLIRecipe:
    def test_add_recipe_success(self):
        """Adding a recipe should succeed."""
        stdout, stderr, rc = _run_cli(
            "add-recipe",
            "--name", "Scrambled Eggs",
            "--servings", "2",
            "--prep-time", "10",
            "--ingredients", "eggs:3:pieces,butter:1:tbsp,milk:2:tbsp",
        )
        assert rc == 0
        assert "Added recipe: Scrambled Eggs" in stdout

    def test_add_recipe_invalid_ingredient_format(self):
        """Invalid ingredient format should fail."""
        stdout, stderr, rc = _run_cli(
            "add-recipe",
            "--name", "Bad Recipe",
            "--servings", "1",
            "--prep-time", "5",
            "--ingredients", "bad_format",
        )
        assert rc == 1
        assert "Error: invalid ingredient format" in stderr


class CLIPlan:
    def test_plan_empty_pantry(self):
        """Planning with empty pantry should show error."""
        stdout, stderr, rc = _run_cli("plan")
        assert rc == 1
        assert "pantry is empty" in stderr.lower()

    def test_plan_no_recipes(self):
        """Planning with no recipes should show error."""
        # First add a pantry item
        _run_cli(
            "add-pantry-item",
            "--name", "Eggs",
            "--quantity", "12",
            "--unit", "pieces",
            "--category", "dairy",
        )
        stdout, stderr, rc = _run_cli("plan")
        assert rc == 1
        assert "no recipes available" in stderr.lower()

    def test_plan_with_data(self):
        """Planning with pantry items and recipes should succeed."""
        # Add pantry items
        _run_cli(
            "add-pantry-item",
            "--name", "Eggs",
            "--quantity", "12",
            "--unit", "pieces",
            "--category", "dairy",
        )
        _run_cli(
            "add-pantry-item",
            "--name", "Butter",
            "--quantity", "200",
            "--unit", "grams",
            "--category", "dairy",
        )
        # Add recipe
        _run_cli(
            "add-recipe",
            "--name", "Scrambled Eggs",
            "--servings", "2",
            "--prep-time", "10",
            "--ingredients", "eggs:3:pieces,butter:1:tbsp",
        )
        stdout, stderr, rc = _run_cli("plan")
        assert rc == 0
        assert "Breakfast" in stdout or "breakfast" in stdout
        assert "Lunch" in stdout or "lunch" in stdout
        assert "Dinner" in stdout or "dinner" in stdout


class CLIMain:
    def test_cli_help(self):
        """CLI should show help when invoked with --help."""
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PantryChef" in result.output

    def test_cli_group_commands(self):
        """CLI should list available commands."""
        result = CliRunner().invoke(cli, ["--help"])
        assert "add-pantry-item" in result.output
        assert "add-recipe" in result.output
        assert "plan" in result.output
