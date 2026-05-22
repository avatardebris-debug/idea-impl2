"""Pydantic data models for PantryChef Core entities."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PantryItem(BaseModel):
    """An item stored in the pantry."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    expiry_date: Optional[date] = None


class RecipeIngredient(BaseModel):
    """A single ingredient within a recipe."""

    id: Optional[int] = None
    recipe_id: Optional[int] = None
    name: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)


class Recipe(BaseModel):
    """A recipe with its ingredients."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    servings: int = Field(..., gt=0)
    prep_time: int = Field(..., ge=0)  # in minutes
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    nutrition: list[NutritionalInfo] = Field(default_factory=list)
    dietary_tags: list[str] = Field(default_factory=list)  # e.g. ["vegan", "gluten-free"]


class MealPlan(BaseModel):
    """A single-day meal plan with breakfast, lunch, and dinner."""

    id: Optional[int] = None
    date: date
    meal_type: str  # "breakfast", "lunch", "dinner"
    recipe_id: int
    recipe_name: str = ""
    servings: int = 1
    score: float = 0.0
    status: str = ""
    notes: str = ""


class ShoppingItem(BaseModel):
    """An item to buy for a meal plan."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    source_recipe_ids: list[int] = Field(default_factory=list)


class NutritionalInfo(BaseModel):
    """Nutritional information per serving of a recipe."""

    id: Optional[int] = None
    recipe_id: Optional[int] = None
    calories: float = Field(..., ge=0)
    protein: float = Field(..., ge=0)
    carbs: float = Field(..., ge=0)
    fat: float = Field(..., ge=0)
    fiber: float = Field(..., ge=0)
