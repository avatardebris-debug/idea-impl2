"""CLI entry point for PantryChef."""

from __future__ import annotations

import sys
from datetime import date

import click

from .database import Database
from .models import RecipeIngredient
from .pantry_manager import PantryManager
from .recipe_store import RecipeStore
from .recipe_matcher import RecipeMatcher
from .meal_planner import BasicMealPlanner


@click.group()
def cli():
    """PantryChef — Pantry ingestion, recipe matching, and meal planning."""
    pass


@cli.command()
@click.option("--name", required=True, help="Item name")
@click.option("--quantity", required=True, type=float, help="Quantity")
@click.option("--unit", required=True, help="Unit of measurement")
@click.option("--category", required=True, help="Category (e.g. dairy, produce)")
@click.option("--expiry-date", default=None, help="Expiry date (YYYY-MM-DD)")
def add_pantry_item(name, quantity, unit, category, expiry_date):
    """Add an item to the pantry."""
    db = Database()
    pm = PantryManager(db)
    exp = date.fromisoformat(expiry_date) if expiry_date else None
    item = pm.add_item(name=name, quantity=quantity, unit=unit, category=category, expiry_date=exp)
    click.echo(f"Added pantry item: {item.name} ({item.quantity} {item.unit})")
    sys.exit(0)


@cli.command()
@click.option("--name", required=True, help="Recipe name")
@click.option("--servings", required=True, type=int, help="Number of servings")
@click.option("--prep-time", required=True, type=int, help="Prep time in minutes")
@click.option(
    "--ingredients",
    required=True,
    help='Comma-separated ingredients in format "name:quantity:unit" (e.g. "eggs:3:pieces,butter:1:tbsp")',
)
def add_recipe(name, servings, prep_time, ingredients):
    """Add a recipe with ingredients."""
    db = Database()
    rs = RecipeStore(db)
    ing_list = []
    for part in ingredients.split(","):
        parts = part.strip().split(":")
        if len(parts) != 3:
            click.echo(f"Error: invalid ingredient format '{part}'. Expected name:quantity:unit", err=True)
            sys.exit(1)
        ing_list.append(RecipeIngredient(name=parts[0], quantity=float(parts[1]), unit=parts[2]))
    recipe = rs.add_recipe(name=name, servings=servings, prep_time=prep_time, ingredients=ing_list)
    click.echo(f"Added recipe: {recipe.name} (id={recipe.id})")
    sys.exit(0)


@cli.command()
def plan():
    """Generate a 1-day meal plan based on pantry and recipes."""
    db = Database()
    pm = PantryManager(db)
    rs = RecipeStore(db)
    pantry_items = pm.list_items()
    recipes = rs.list_recipes()

    if not pantry_items:
        click.echo("Error: pantry is empty. Add items first.", err=True)
        sys.exit(1)
    if not recipes:
        click.echo("Error: no recipes available. Add recipes first.", err=True)
        sys.exit(1)

    planner = BasicMealPlanner()
    plans = planner.generate_plan(pantry_items, recipes, date.today())

    if not plans:
        click.echo("No cookable recipes found for today's plan.")
        sys.exit(0)

    click.echo("=" * 50)
    click.echo(f"  Meal Plan for {date.today()}")
    click.echo("=" * 50)
    for p in plans:
        click.echo(f"  {p.meal_type.capitalize():<12} | {p.recipe_name:<25} | score={p.score:.1f} | {p.status}")
    click.echo("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    cli()
