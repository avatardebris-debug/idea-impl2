"""Core schema inference engine for JSON data."""

from __future__ import annotations

import json
from typing import Any


def infer_schema(data: Any) -> dict[str, Any]:
    """Infer a JSON Schema draft-07 document from Python data.

    Accepts a dict, list of dicts, or a single dict. Returns a JSON Schema
    conforming to draft-07 with type, properties, required, and per-field
    constraints (min/max, minLength/maxLength, enum candidates).

    Args:
        data: A Python object — dict, list of dicts, or single dict.

    Returns:
        A dict representing a JSON Schema draft-07 document.
    """
    if isinstance(data, list):
        return _infer_array_schema(data)
    elif isinstance(data, dict):
        return _infer_object_schema([data])
    else:
        # Primitive — return a schema for that single value
        return {"type": _json_type(data)}


def infer_schema_stream(file_obj: Any, chunk_size: int = 10000) -> dict[str, Any]:
    """Stream a JSON or JSONL file and infer schema.
    
    Uses `ijson` for standard JSON arrays or standard line-iteration for JSONL.
    """
    import ijson
    
    # Check if it's JSONL by peeking at first character
    first_char = file_obj.read(1)
    file_obj.seek(0)
    
    if first_char == b'{' or (isinstance(first_char, str) and first_char == '{'):
        # JSONL
        objects = []
        for line in file_obj:
            if not line.strip():
                continue
            objects.append(json.loads(line))
            if len(objects) >= chunk_size:
                break
        return _infer_object_schema(objects)
    else:
        # JSON array using ijson
        objects = []
        for obj in ijson.items(file_obj, 'item'):
            objects.append(obj)
            if len(objects) >= chunk_size:
                break
        return _infer_array_schema(objects)

def _json_type(value: Any) -> str:
    """Map a Python value to a JSON Schema type string."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"  # fallback


def _infer_object_schema(objects: list[dict]) -> dict[str, Any]:
    """Infer schema from a list of dict objects (all must be dicts)."""
    if not objects:
        return {"type": "object", "properties": {}}

    # Collect all keys and their value types across all objects
    all_keys: set[str] = set()
    field_values: dict[str, list[Any]] = {k: [] for k in objects[0].keys()}

    for obj in objects:
        all_keys.update(obj.keys())
        for key, val in obj.items():
            if key not in field_values:
                field_values[key] = []
            field_values[key].append(val)

    # Determine required fields (present in ALL objects)
    required = [k for k in objects[0].keys() if all(k in obj for obj in objects)]

    properties: dict[str, Any] = {}
    for key in sorted(all_keys):
        values = field_values.get(key, [])
        properties[key] = _infer_field_schema(values)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": sorted(required) if required else [],
    }
    return schema


def _infer_array_schema(items: list[Any]) -> dict[str, Any]:
    """Infer schema for an array — returns items schema."""
    if not items:
        return {"type": "array", "items": {}}

    # Infer schema from the first item as representative
    first = items[0]
    if isinstance(first, dict):
        # Infer from all items that are dicts
        dict_items = [i for i in items if isinstance(i, dict)]
        if dict_items:
            item_schema = _infer_object_schema(dict_items)
        else:
            item_schema = {"type": "object"}
    else:
        item_schema = {"type": _json_type(first)}

    result: dict[str, Any] = {"type": "array", "items": item_schema}
    
    # Expose required fields at the top level for convenience
    if isinstance(item_schema, dict) and item_schema.get("type") == "object":
        if "required" in item_schema:
            result["required"] = item_schema["required"]
        if "properties" in item_schema:
            result["properties"] = item_schema["properties"]
    
    return result


def _infer_field_schema(values: list[Any]) -> dict[str, Any]:
    """Infer schema for a single field given its collected values."""
    if not values:
        return {}

    # Detect types present
    type_set: set[str] = set()
    for v in values:
        type_set.add(_json_type(v))

    # Handle null values — they don't contribute to type constraints
    non_null = [v for v in values if v is not None]

    if len(type_set) > 1:
        # Mixed types
        type_info: dict[str, Any] = {"type": sorted(type_set)}
    else:
        primary_type = type_set.pop()
        type_info: dict[str, Any] = {"type": primary_type}

    # Determine primary_type for per-type constraints
    # When mixed types, use the most common non-null type
    primary_type = None
    if len(type_set) == 1:
        primary_type = type_set.pop()
    else:
        # Mixed types: pick the most common non-null type
        type_counts: dict[str, int] = {}
        for v in values:
            t = _json_type(v)
            type_counts[t] = type_counts.get(t, 0) + 1
        primary_type = max(type_counts, key=type_counts.get)

    # Per-type constraints
    if primary_type == "integer" or primary_type == "number":
        numeric_vals = [v for v in non_null if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric_vals:
            type_info["minimum"] = min(numeric_vals)
            type_info["maximum"] = max(numeric_vals)

    elif primary_type == "string":
        str_vals = [v for v in non_null if isinstance(v, str)]
        if str_vals:
            type_info["minLength"] = min(len(s) for s in str_vals)
            type_info["maxLength"] = max(len(s) for s in str_vals)
            # Low-cardinality enum candidate
            unique_vals = set(str_vals)
            if len(unique_vals) <= 10:
                type_info["enum"] = sorted(unique_vals)

    elif primary_type == "object":
        # Recurse into nested dicts
        dict_vals = [v for v in non_null if isinstance(v, dict)]
        if dict_vals:
            nested = _infer_object_schema(dict_vals)
            type_info["properties"] = nested.get("properties", {})
            if nested.get("required"):
                type_info["required"] = nested["required"]

    elif primary_type == "array":
        arr_vals = [v for v in non_null if isinstance(v, list)]
        if arr_vals:
            # Infer items schema from first array's first element
            first_arr = arr_vals[0]
            if first_arr:
                if isinstance(first_arr, list):
                    # Nested array — infer items from the inner array's elements
                    inner_first = first_arr[0]
                    if isinstance(inner_first, list):
                        type_info["items"] = _infer_array_schema(inner_first)
                    else:
                        type_info["items"] = {"type": _json_type(inner_first)}
                else:
                    type_info["items"] = {"type": _json_type(first_arr)}
            else:
                type_info["items"] = {}

    # If null is one of the types, add it
    if "null" in type_set:
        if isinstance(type_info.get("type"), list):
            if "null" not in type_info["type"]:
                type_info["type"].append("null")
        else:
            type_info["type"] = [type_info["type"], "null"]

    return type_info
