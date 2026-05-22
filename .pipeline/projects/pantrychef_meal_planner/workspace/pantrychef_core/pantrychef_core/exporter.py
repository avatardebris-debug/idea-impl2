"""Exporter — CSV and Markdown export for meal plans."""

from __future__ import annotations

import csv
import io
from typing import Optional

from .models import MealPlan, ShoppingItem


class Exporter:
    """Export meal plans and shopping lists to CSV or Markdown."""

    @staticmethod
    def meal_plan_to_csv(plans: list[MealPlan]) -> str:
        """Export meal plan to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "meal_type", "recipe_id", "recipe_name", "score", "status"])
        for plan in plans:
            writer.writerow([
                plan.date.isoformat() if plan.date else "",
                plan.meal_type,
                plan.recipe_id,
                plan.recipe_name,
                plan.score,
                plan.status,
            ])
        return output.getvalue()

    @staticmethod
    def meal_plan_to_markdown(plans: list[MealPlan]) -> str:
        """Export meal plan to Markdown string."""
        lines = ["# Meal Plan\n"]

        # Group by date
        by_date: dict[str, list[MealPlan]] = {}
        for plan in plans:
            key = plan.date.isoformat() if plan.date else "unknown"
            by_date.setdefault(key, []).append(plan)

        for date_key in sorted(by_date.keys()):
            day_plans = by_date[date_key]
            lines.append(f"## {date_key}\n")
            lines.append("| Meal Type | Recipe | Score | Status |")
            lines.append("|-----------|--------|-------|--------|")
            for plan in day_plans:
                lines.append(
                    f"| {plan.meal_type.title()} | {plan.recipe_name} "
                    f"| {plan.score:.2f} | {plan.status} |"
                )
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def shopping_list_to_csv(items: list[ShoppingItem]) -> str:
        """Export shopping list to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "quantity", "unit", "source_recipes"])
        for item in items:
            writer.writerow([
                item.name,
                item.quantity,
                item.unit,
                ";".join(str(rid) for rid in item.source_recipe_ids),
            ])
        return output.getvalue()

    @staticmethod
    def shopping_list_to_markdown(items: list[ShoppingItem]) -> str:
        """Export shopping list to Markdown string."""
        lines = ["# Shopping List\n"]
        lines.append("| Item | Quantity | Unit | Source Recipes |")
        lines.append("|------|----------|------|----------------|")
        for item in items:
            lines.append(
                f"| {item.name} | {item.quantity} | {item.unit} "
                f"| {', '.join(str(rid) for rid in item.source_recipe_ids)} |"
            )
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def meal_plan_to_json(plans: list[MealPlan]) -> str:
        """Export meal plan to JSON string."""
        import json
        data = []
        for plan in plans:
            data.append({
                "date": plan.date.isoformat() if plan.date else None,
                "meal_type": plan.meal_type,
                "recipe_id": plan.recipe_id,
                "recipe_name": plan.recipe_name,
                "score": plan.score,
                "status": plan.status,
            })
        return json.dumps(data, indent=2)
