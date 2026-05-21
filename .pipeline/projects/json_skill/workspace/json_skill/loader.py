"""
Loader module for JSON skills.

Handles reading JSON skill files and validating their structure.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union


class SkillValidationError(Exception):
    """Raised when a skill JSON file fails validation."""
    pass


def validate_skill_schema(skill_data: Dict[str, Any]) -> None:
    """
    Validate that a skill dictionary has the required structure.
    
    Args:
        skill_data: Dictionary containing skill data.

    Raises:
        SkillValidationError: If validation fails.
    """
    required_fields = ["name", "description", "system_prompt"]
    for field in required_fields:
        if field not in skill_data:
            raise SkillValidationError(f"Missing required field: {field}")

    if "functions" in skill_data and not isinstance(skill_data["functions"], list):
        raise SkillValidationError("'functions' must be a list")

    if "examples" in skill_data and not isinstance(skill_data["examples"], list):
        raise SkillValidationError("'examples' must be a list")

    if "functions" in skill_data:
        for i, func in enumerate(skill_data["functions"]):
            if not isinstance(func, dict):
                raise SkillValidationError(f"functions[{i}] must be a dict")
            if "name" not in func:
                raise SkillValidationError(f"functions[{i}] missing 'name'")


def load_skill(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a skill from a JSON file.
    
    Args:
        path: Path to the JSON skill file.

    Returns:
        Dictionary containing the skill data.

    Raises:
        SkillValidationError: If the file fails validation.
    """
    path = Path(path)
    with open(path, "r") as f:
        skill_data = json.load(f)
    validate_skill_schema(skill_data)
    return skill_data
