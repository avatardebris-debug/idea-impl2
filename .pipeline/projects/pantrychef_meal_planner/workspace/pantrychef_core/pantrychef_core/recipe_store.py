"""RecipeStore — CRUD operations for recipes and their ingredients."""

from __future__ import annotations

import sqlite3
from typing import Optional

from .models import Recipe, RecipeIngredient
from .database import Database


class RecipeStore:
    """Manage recipes and ingredients backed by SQLite."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.db.init_db()

    def add_recipe(
        self,
        name: str,
        servings: int,
        prep_time: int,
        ingredients: list[RecipeIngredient],
    ) -> Recipe:
        """Insert a recipe and its ingredients in a transaction."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO recipes (name, servings, prep_time) VALUES (?, ?, ?)",
                (name, servings, prep_time),
            )
            recipe_id = cursor.lastrowid
            for ing in ingredients:
                conn.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, name, quantity, unit) "
                    "VALUES (?, ?, ?, ?)",
                    (recipe_id, ing.name, ing.quantity, ing.unit),
                )
            conn.commit()
            return Recipe(
                id=recipe_id,
                name=name,
                servings=servings,
                prep_time=prep_time,
                ingredients=ingredients,
            )

    def get_recipe(self, recipe_id: int) -> Optional[Recipe]:
        """Return a recipe with its ingredients, or None."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, servings, prep_time FROM recipes WHERE id = ?",
                (recipe_id,),
            ).fetchone()
            if row is None:
                return None
            recipe = Recipe(
                id=row[0],
                name=row[1],
                servings=row[2],
                prep_time=row[3],
                ingredients=[],
            )
            ing_rows = conn.execute(
                "SELECT id, recipe_id, name, quantity, unit FROM recipe_ingredients WHERE recipe_id = ?",
                (recipe_id,),
            ).fetchall()
            for ir in ing_rows:
                recipe.ingredients.append(
                    RecipeIngredient(
                        id=ir[0],
                        recipe_id=ir[1],
                        name=ir[2],
                        quantity=ir[3],
                        unit=ir[4],
                    )
                )
            return recipe

    def list_recipes(self) -> list[Recipe]:
        """Return all recipes with their ingredients."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, servings, prep_time FROM recipes"
            ).fetchall()
            recipes = []
            for row in rows:
                recipe = Recipe(
                    id=row[0],
                    name=row[1],
                    servings=row[2],
                    prep_time=row[3],
                    ingredients=[],
                )
                ing_rows = conn.execute(
                    "SELECT id, recipe_id, name, quantity, unit FROM recipe_ingredients WHERE recipe_id = ?",
                    (row[0],),
                ).fetchall()
                for ir in ing_rows:
                    recipe.ingredients.append(
                        RecipeIngredient(
                            id=ir[0],
                            recipe_id=ir[1],
                            name=ir[2],
                            quantity=ir[3],
                            unit=ir[4],
                        )
                    )
                recipes.append(recipe)
            return recipes
