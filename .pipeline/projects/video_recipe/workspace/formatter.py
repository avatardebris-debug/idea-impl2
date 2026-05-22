"""Formatter — render recipes as JSON or Markdown."""

import json


def render_recipe(recipe: dict, format: str = "json") -> str:
    """Render a recipe dict into the specified format.

    Args:
        recipe: Recipe dict with title, summary, steps.
        format: Output format — "json" or "markdown".

    Returns:
        Rendered string.

    Raises:
        ValueError: If format is unsupported.
    """
    if format == "json":
        return _render_json(recipe)
    elif format == "markdown":
        return _render_markdown(recipe)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'markdown'.")


def _render_json(recipe: dict) -> str:
    """Render recipe as pretty-printed JSON."""
    return json.dumps(recipe, indent=2, ensure_ascii=False)


def _render_markdown(recipe: dict) -> str:
    """Render recipe as Markdown."""
    lines = [
        f"# {recipe['title']}",
        "",
        f"{recipe['summary']}",
        "",
        "## Steps",
        "",
    ]
    for i, step in enumerate(recipe["steps"], 1):
        ts = step.get("timestamp", 0)
        desc = step.get("description", "")
        tools = step.get("inferred_tools", [])
        materials = step.get("inferred_materials", [])

        lines.append(f"### Step {i} (at {ts:.1f}s)")
        lines.append("")
        lines.append(desc)
        lines.append("")
        if tools:
            lines.append(f"**Tools:** {', '.join(tools)}")
            lines.append("")
        if materials:
            lines.append(f"**Materials:** {', '.join(materials)}")
            lines.append("")
    return "\n".join(lines)
