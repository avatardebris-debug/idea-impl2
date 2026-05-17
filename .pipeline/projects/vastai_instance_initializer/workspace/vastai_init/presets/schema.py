"""Preset schema definitions for VAST.ai instance configurations.

Defines the structure of YAML preset files that describe VAST.ai instance
parameters including GPU type, price cap, storage, SSH commands, environment
variables, Docker image, and other configuration options.
"""

from typing import Any

# Required fields that must be present in every preset
PRESET_REQUIRED_FIELDS = [
    "name",
    "gpu_type",
    "price_cap",
    "storage",
    "image",
]

# Optional fields with their default values and type constraints
PRESET_OPTIONAL_FIELDS: dict[str, dict[str, Any]] = {
    "ssh_commands": {
        "default": [],
        "type": list,
        "description": "List of SSH commands to run on the instance after launch",
    },
    "env_vars": {
        "default": {},
        "type": dict,
        "description": "Environment variables to set on the instance",
    },
    "disk_size": {
        "default": None,
        "type": (int, str),
        "description": "Total disk size (e.g., '100GB' or 100), overrides storage",
    },
    "region": {
        "default": None,
        "type": str,
        "description": "Preferred region for instance placement",
    },
    "min_vram": {
        "default": None,
        "type": (int, str),
        "description": "Minimum VRAM requirement in GB",
    },
    "uptime": {
        "default": None,
        "type": (int, str),
        "description": "Maximum uptime for the instance (e.g., '2h' or 7200)",
    },
    "ssh_public_key": {
        "default": None,
        "type": str,
        "description": "SSH public key to inject into the instance",
    },
    "docker_args": {
        "default": {},
        "type": dict,
        "description": "Additional Docker arguments for the container",
    },
    "ports": {
        "default": [],
        "type": list,
        "description": "List of ports to expose",
    },
    "labels": {
        "default": {},
        "type": dict,
        "description": "Labels to attach to the instance",
    },
    "timeout": {
        "default": 300,
        "type": int,
        "description": "Timeout in seconds for polling instance status",
    },
    "poll_interval": {
        "default": 10,
        "type": int,
        "description": "Interval in seconds between status polls",
    },
    "count": {
        "default": 1,
        "type": int,
        "description": "Number of identical instances to launch from this preset",
    },
}

# Full schema combining required and optional fields
PRESET_SCHEMA: dict[str, dict[str, Any]] = {}
for field in PRESET_REQUIRED_FIELDS:
    PRESET_SCHEMA[field] = {"required": True, "type": str}
for field, info in PRESET_OPTIONAL_FIELDS.items():
    PRESET_SCHEMA[field] = {
        "required": False,
        "type": info["type"],
        "default": info["default"],
        "description": info["description"],
    }


def get_schema_field(field_name: str) -> dict[str, Any] | None:
    """Get the schema definition for a given field name.

    Args:
        field_name: The name of the field to look up.

    Returns:
        The schema definition dict, or None if the field is not in the schema.
    """
    return PRESET_SCHEMA.get(field_name)


def is_required_field(field_name: str) -> bool:
    """Check if a field is required in the preset schema.

    Args:
        field_name: The name of the field to check.

    Returns:
        True if the field is required, False otherwise.
    """
    return PRESET_SCHEMA.get(field_name, {}).get("required", False)


def get_field_default(field_name: str) -> Any:
    """Get the default value for an optional field.

    Args:
        field_name: The name of the field.

    Returns:
        The default value, or None if the field is not optional or has no default.
    """
    field_info = PRESET_SCHEMA.get(field_name, {})
    return field_info.get("default", None)
