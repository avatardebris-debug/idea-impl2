"""Web UI — FastAPI backend for PantryChef."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .advanced_meal_planner import AdvancedMealPlanner
from .exporter import Exporter
from .models import MealPlan, PantryItem, Recipe, RecipeIngredient, ShoppingItem
from .preference_filter import PreferenceFilter
from .shopping_list_generator import ShoppingListGenerator


# --- Pydantic request/response models ---

class AddPantryItemRequest(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    expiry_date: Optional[str] = None


class AddRecipeRequest(BaseModel):
    name: str
    servings: int
    prep_time: int
    ingredients: list[dict]
    nutrition: list[dict] = Field(default_factory=list)
    dietary_tags: list[str] = Field(default_factory=list)


class GenerateMealPlanRequest(BaseModel):
    days: int = 7
    dietary_tags: list[str] = Field(default_factory=list)
    max_calories: dict[str, int] = Field(default_factory=dict)
    seed: Optional[int] = None


class GenerateShoppingListRequest(BaseModel):
    recipe_ids: list[int]


class FilterRecipesRequest(BaseModel):
    required_tags: list[str] = Field(default_factory=list)
    excluded_tags: list[str] = Field(default_factory=list)


# --- App setup ---

app = FastAPI(title="PantryChef API", version="0.3.0")

# In-memory stores (for demo; replace with DB in production)
pantry_items: list[PantryItem] = []
recipes: list[Recipe] = []


# --- Pantry endpoints ---

@app.post("/pantry/items")
def add_pantry_item(req: AddPantryItemRequest):
    """Add an item to the pantry."""
    expiry = None
    if req.expiry_date:
        expiry = date.fromisoformat(req.expiry_date)
    item = PantryItem(
        name=req.name,
        quantity=req.quantity,
        unit=req.unit,
        category=req.category,
        expiry_date=expiry,
    )
    pantry_items.append(item)
    return {"id": item.id, "message": "Item added"}


@app.get("/pantry/items")
def list_pantry_items():
    """List all pantry items."""
    return [i.model_dump() for i in pantry_items]


# --- Recipe endpoints ---

@app.post("/recipes")
def add_recipe(req: AddRecipeRequest):
    """Add a recipe."""
    ingredients = [
        RecipeIngredient(**ing) for ing in req.ingredients
    ]
    nutrition = [
        RecipeIngredient(**n) for n in req.nutrition
    ] if req.nutrition else []
    recipe = Recipe(
        name=req.name,
        servings=req.servings,
        prep_time=req.prep_time,
        ingredients=ingredients,
        nutrition=nutrition,
        dietary_tags=req.dietary_tags,
    )
    recipes.append(recipe)
    return {"id": recipe.id, "message": "Recipe added"}


@app.get("/recipes")
def list_recipes():
    """List all recipes."""
    return [r.model_dump() for r in recipes]


# --- Meal plan endpoints ---

@app.post("/meal-plans/generate")
def generate_meal_plan(req: GenerateMealPlanRequest):
    """Generate a multi-day meal plan."""
    planner = AdvancedMealPlanner(
        recipes=recipes,
        pantry_items=pantry_items,
        days=req.days,
        dietary_tags=req.dietary_tags,
        max_calories=req.max_calories,
        seed=req.seed,
    )
    plans = planner.generate_plan()
    return [p.model_dump() for p in plans]


@app.get("/meal-plans/export/csv")
def export_meal_plan_csv():
    """Export current meal plan as CSV."""
    # Generate a default plan for export
    planner = AdvancedMealPlanner(
        recipes=recipes,
        pantry_items=pantry_items,
        days=7,
    )
    plans = planner.generate_plan()
    csv_data = Exporter.meal_plan_to_csv(plans)
    return {"format": "csv", "data": csv_data}


@app.get("/meal-plans/export/markdown")
def export_meal_plan_markdown():
    """Export current meal plan as Markdown."""
    planner = AdvancedMealPlanner(
        recipes=recipes,
        pantry_items=pantry_items,
        days=7,
    )
    plans = planner.generate_plan()
    md_data = Exporter.meal_plan_to_markdown(plans)
    return {"format": "markdown", "data": md_data}


# --- Shopping list endpoints ---

@app.post("/shopping-list/generate")
def generate_shopping_list(req: GenerateShoppingListRequest):
    """Generate a shopping list for given recipe IDs."""
    selected = [r for r in recipes if r.id in req.recipe_ids]
    items = ShoppingListGenerator.generate(pantry_items, selected)
    return [i.model_dump() for i in items]


@app.get("/shopping-list/export/csv")
def export_shopping_list_csv():
    """Export shopping list as CSV."""
    items = ShoppingListGenerator.generate(pantry_items, recipes)
    csv_data = Exporter.shopping_list_to_csv(items)
    return {"format": "csv", "data": csv_data}


# --- Preference/filter endpoints ---

@app.post("/recipes/filter")
def filter_recipes(req: FilterRecipesRequest):
    """Filter recipes by dietary preferences."""
    filtered = PreferenceFilter.filter_by_tags(
        recipes,
        required_tags=req.required_tags,
        excluded_tags=req.excluded_tags,
    )
    return [r.model_dump() for r in filtered]


@app.get("/recipes/tags")
def get_available_tags():
    """Get all available dietary tags and their counts."""
    tags = PreferenceFilter.get_available_tags(recipes)
    counts = PreferenceFilter.get_tag_counts(recipes)
    return {"available_tags": sorted(tags), "tag_counts": counts}
