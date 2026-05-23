"""Internal registry for robot primitives.

This module is imported by submodules to register primitives,
and by __init__.py to expose the registry.
"""

_PRIMITIVE_REGISTRY: list = []
_CATEGORY_MAP: dict = {}


def register_primitive(cls, category: str, description: str, parameters: list, returns: str = "None") -> None:
    """Register a primitive class in the internal registry."""
    _PRIMITIVE_REGISTRY.append({
        "name": cls.__name__.lower().replace("_", "_"),
        "category": category,
        "description": description,
        "parameters": parameters,
        "returns": returns,
    })
    _CATEGORY_MAP.setdefault(category, []).append(cls)


def load_all_primitives() -> list:
    """Return the full list of registered primitive metadata."""
    return list(_PRIMITIVE_REGISTRY)


def category_map() -> dict:
    """Return the category-to-classes mapping."""
    return dict(_CATEGORY_MAP)
