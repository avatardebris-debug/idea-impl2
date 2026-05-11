# Phase 1 Tasks

- [x] Task 1: Project scaffolding and data models
  - What: Create the `pantrychef_core` Python package with project structure, pyproject.toml, and Pydantic data models for all core entities (PantryItem, Recipe, RecipeIngredient, MealPlan).
  - Files: `pantrychef_core/pyproject.toml`, `pantrychef_core/pantrychef_core/__init__.py`, `pantrychef_core/pantrychef_core/models.py`, `pantrychef_core/README.md`
  - Done when: `pyproject.toml` declares the package with `click` and `pydantic` dependencies; `models.py` defines all five Pydantic models matching the master plan data schema; `python -m pytest --collect-only` runs without errors on an empty test suite.

- [x] Task 2: SQLite database layer and schema
  - What: Implement a `Database` helper class that creates the SQLite database on first use, runs schema-on-first-write (CREATE TABLE IF NOT EXISTS for all five tables), and provides a connection context.
  - Files: `pantrychef_core/pantrychef_core/database.py`
  - Done when: `Database.init_db()` creates all five tables (pantry_items, recipes, recipe_ingredients, meal_plans, shopping_items) with the exact schema from the master plan; `Database.get_connection()` returns a live connection; a test verifies tables exist after `init_db()` is called.

- [x] Task 3: PantryManager and RecipeStore CRUD services
  - What: Implement `PantryManager` (add, remove, list, get pantry items) and `RecipeStore` (add recipe with ingredients, get recipe by id, list all recipes) backed by the SQLite database.
  - Files: `pantrychef_core/pantrychef_core/pantry_manager.py`, `pantrychef_core/pantrychef_core/recipe_store.py`
  - Done when: `PantryManager.add_item(name, quantity, unit, category, expiry_date)` inserts and returns a PantryItem; `PantryManager.remove_item(id)` deletes; `PantryManager.list_items()` returns all items; `RecipeStore.add_recipe(name, servings, prep_time, ingredients)` inserts recipe + ingredients in a transaction; `RecipeStore.get_recipe(id)` returns recipe with ingredients; `RecipeStore.list_recipes()` returns all recipes; unit tests cover happy path and edge cases (e.g., add duplicate name, get nonexistent recipe).

- [x] Task 4: RecipeMatcher — scored ingredient overlap algorithm
  - What: Implement `RecipeMatcher` that scores each recipe against the current pantry by computing ingredient overlap percentage (≥80% = fully cookable, ≥60% = mostly cookable), returns a ranked list of matching recipes.
  - Files: `pantrychef_core/pantrychef_core/recipe_matcher.py`
  - Done when: `RecipeMatcher.match(pantry_items, recipes)` returns a list of `(recipe, score, status)` tuples sorted by score descending; score = fraction of recipe ingredients found in pantry (name-based match); status is "fully_cookable" (≥0.8), "mostly_cookable" (≥0.6), or "not_cookable" (<0.6); unit tests achieve ≥80% branch coverage covering: all ingredients present, partial overlap at 80% boundary, partial overlap at 60% boundary, zero overlap, case-insensitive name matching, and empty pantry/recipe edge cases.

- [x] Task 5: BasicMealPlanner and CLI entry point
  - What: Implement `BasicMealPlanner` that picks top-scoring recipes from `RecipeMatcher` into a single-day meal plan (breakfast, lunch, dinner), and build the CLI with `add-pantry-item`, `add-recipe`, and `plan` commands.
  - Files: `pantrychef_core/pantrychef_core/meal_planner.py`, `pantrychef_core/pantrychef_core/cli.py`
  - Done when: `BasicMealPlanner.generate_plan(pantry_items, recipes, date)` returns a MealPlan with breakfast, lunch, and dinner entries (or fewer if not enough recipes); CLI `pantrychef add-pantry-item --name X --quantity Y --unit Z --category C` works; CLI `pantrychef add-recipe --name X --servings N --prep-time M --ingredients "ing1:qty1:unit1,ing2:qty2:unit2"` works; CLI `pantrychef plan` outputs a formatted 1-day meal plan showing meal type, recipe name, score, and status; CLI commands exit with code 0 on success and non-zero on error.

- [x] Task 6: Unit tests and integration smoke test
  - What: Write comprehensive unit tests for all core classes (PantryManager, RecipeStore, RecipeMatcher, BasicMealPlanner) and a smoke test that exercises the full workflow via CLI.
  - Files: `pantrychef_core/tests/test_pantry_manager.py`, `pantrychef_core/tests/test_recipe_store.py`, `pantrychef_core/tests/test_recipe_matcher.py`, `pantrychef_core/tests/test_meal_planner.py`, `pantrychef_core/tests/test_cli.py`
  - Done when: All core classes have unit tests; `RecipeMatcher` tests achieve ≥80% branch coverage (verified via `pytest-cov`); smoke test adds ≥20 pantry items and ≥5 recipes via CLI, runs `pantrychef plan`, and verifies output contains breakfast, lunch, and dinner entries; `pytest --cov=pantrychef_core --cov-fail-under=80` passes; `python -m pytest` passes with zero failures.