"""Validation utilities for the multi-format export engine."""

from typing import Any, Dict, Optional


def validate_manuscript(manuscript: Any) -> bool:
    """Validate a Manuscript object for export readiness.

    Args:
        manuscript: The Manuscript to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If the manuscript is invalid.
    """
    if manuscript is None:
        raise ValueError("manuscript cannot be None")

    if not hasattr(manuscript, "title") or not manuscript.title:
        raise ValueError("manuscript title must be a non-empty string")

    if not hasattr(manuscript, "chapters") or not manuscript.chapters:
        raise ValueError("manuscript must have at least one chapter")

    for i, ch in enumerate(manuscript.chapters):
        if not hasattr(ch, "title"):
            raise ValueError(f"chapter {i} must have a title")
        if not hasattr(ch, "content"):
            raise ValueError(f"chapter {i} must have content")
        for j, item in enumerate(ch.content):
            if not hasattr(item, "text"):
                raise ValueError(
                    f"chapter {i} item {j} must have text attribute"
                )

    return True


def validate_export_options(options: Optional[Dict[str, Any]]) -> bool:
    """Validate export options dictionary.

    Args:
        options: Export options to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If options are invalid.
    """
    if options is None:
        raise ValueError("options cannot be None")

    valid_page_sizes = {"A4", "Letter", "Legal", "A5", "B5"}
    valid_font_families = {"serif", "sans-serif", "monospace"}
    valid_margin_keys = {"top", "right", "bottom", "left"}

    if "page_size" in options:
        if options["page_size"] not in valid_page_sizes:
            raise ValueError(
                f"page_size must be one of {sorted(valid_page_sizes)}"
            )

    if "font_family" in options:
        if not isinstance(options["font_family"], str):
            raise ValueError("font_family must be a string")

    if "line_height" in options:
        if not isinstance(options["line_height"], (int, float)):
            raise ValueError("line_height must be a number")
        if options["line_height"] <= 0:
            raise ValueError("line_height must be positive")

    if "font_size" in options:
        if not isinstance(options["font_size"], (int, float)):
            raise ValueError("font_size must be a number")
        if options["font_size"] <= 0:
            raise ValueError("font_size must be positive")

    if "margins" in options:
        margins = options["margins"]
        if not isinstance(margins, dict):
            raise ValueError("margins must be a dictionary")
        for key in margins:
            if key not in valid_margin_keys:
                raise ValueError(
                    f"margin key '{key}' must be one of {sorted(valid_margin_keys)}"
                )
        for key, value in margins.items():
            if not isinstance(value, str):
                raise ValueError(f"margin '{key}' must be a string")
            if not any(value.endswith(unit) for unit in ["in", "cm", "px", "pt"]):
                raise ValueError(
                    f"margin '{key}' must end with a unit (in, cm, px, pt)"
                )

    return True
