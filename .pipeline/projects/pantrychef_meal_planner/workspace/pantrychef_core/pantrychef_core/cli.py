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
from .advanced_meal_planner import AdvancedMealPlanner
from .preference_filter import PreferenceFilter
from .exporter import Exporter


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


@cli.command()
@click.option("--days", default=7, type=int, help="Number of days to plan (default: 7)")
@click.option("--dietary-tag", default=None, help="Filter by dietary tag (e.g. vegetarian, vegan, keto)")
@click.option("--max-cal-lunch", default=None, type=int, help="Max calories for lunch")
@click.option("--max-cal-dinner", default=None, type=int, help="Max calories for dinner")
@click.option("--exclude-ingredient", default=None, help="Comma-separated ingredients to exclude")
def advanced_plan(days, dietary_tag, max_cal_lunch, max_cal_dinner, exclude_ingredient):
    """Generate a multi-day meal plan with dietary constraints."""
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

    planner = AdvancedMealPlanner()
    exclude_list = [e.strip() for e in exclude_ingredient.split(",")] if exclude_ingredient else None
    plans = planner.generate_plan(
        pantry_items, recipes, days,
        dietary_tag=dietary_tag,
        max_cal_lunch=max_cal_lunch,
        max_cal_dinner=max_cal_dinner,
        exclude_ingredients=exclude_list,
    )

    if not plans:
        click.echo("No meal plan could be generated with the given constraints.")
        sys.exit(0)

    click.echo("=" * 60)
    click.echo(f"  Advanced Meal Plan for {days} days")
    click.echo("=" * 60)
    for p in plans:
        click.echo(f"  {p.date} | {p.meal_type.capitalize():<10} | {p.recipe_name:<25} | score={p.score:.1f} | {p.status}")
    click.echo("=" * 60)
    sys.exit(0)


@cli.command()
@click.option("--tag", required=True, help="Dietary tag to filter by (e.g. vegetarian, vegan, keto)")
def dietary_filter(tag):
    """List recipes matching a dietary preference."""
    db = Database()
    rs = RecipeStore(db)
    recipes = rs.list_recipes()

    if not recipes:
        click.echo("Error: no recipes available. Add recipes first.", err=True)
        sys.exit(1)

    filtered = PreferenceFilter.filter_by_tags(recipes, required_tags=[tag])
    if not filtered:
        click.echo(f"No recipes found with dietary tag: {tag}")
        sys.exit(0)

    click.echo(f"Recipes with tag '{tag}':")
    for r in filtered:
        click.echo(f"  - {r.name} (tags: {', '.join(r.dietary_tags)})")
    sys.exit(0)


@cli.command()
@click.option("--format", "fmt", default="csv", type=click.Choice(["csv", "markdown"]), help="Export format (csv or markdown)")
@click.option("--output", default=None, help="Output file path (default: stdout)")
def export(fmt, output):
    """Export meal plans to CSV or Markdown."""
    db = Database()
    pm = PantryManager(db)
    rs = RecipeStore(db)
    pantry_items = pm.list_items()
    recipes = rs.list_recipes()

    if not pantry_items or not recipes:
        click.echo("Error: pantry or recipes are empty. Add items first.", err=True)
        sys.exit(1)

    planner = AdvancedMealPlanner()
    plans = planner.generate_plan(pantry_items, recipes, 7)

    if not plans:
        click.echo("No meal plan to export.")
        sys.exit(0)

    if fmt == "csv":
        content = Exporter.meal_plan_to_csv(plans)
    else:
        content = Exporter.meal_plan_to_markdown(plans)

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Exported meal plan to {output}")
    else:
        click.echo(content)
    sys.exit(0)


if __name__ == "__main__":
    cli()
