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
        skill_data: Dictionary containing skill data
        
    Raises:
        SkillValidationError: If the schema is invalid
    """
    required_keys = {"system_prompt", "functions", "examples"}
    missing_keys = required_keys - set(skill_data.keys())
    
    if missing_keys:
        raise SkillValidationError(
            f"Missing required keys: {', '.join(sorted(missing_keys))}"
        )
    
    if not isinstance(skill_data["system_prompt"], str):
        raise SkillValidationError("'system_prompt' must be a string")
    
    if not isinstance(skill_data["functions"], list):
        raise SkillValidationError("'functions' must be a list")
    
    if not isinstance(skill_data["examples"], list):
        raise SkillValidationError("'examples' must be a list")
    
    # Validate each function has required fields
    for i, func in enumerate(skill_data["functions"]):
        if not isinstance(func, dict):
            raise SkillValidationError(f"Function at index {i} must be a dictionary")
        
        required_func_keys = {"name", "description", "parameters"}
        missing_func_keys = required_func_keys - set(func.keys())
        
        if missing_func_keys:
            raise SkillValidationError(
                f"Function '{func.get('name', i)}' missing required keys: {', '.join(sorted(missing_func_keys))}"
            )
        
        if not isinstance(func["name"], str):
            raise SkillValidationError(f"Function '{func['name']}' name must be a string")
        
        if not isinstance(func["description"], str):
            raise SkillValidationError(f"Function '{func['name']}' description must be a string")
        
        if not isinstance(func["parameters"], dict):
            raise SkillValidationError(f"Function '{func['name']}' parameters must be a dictionary")


def load_skill(skill_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and validate a JSON skill file.
    
    Args:
        skill_path: Path to the JSON skill file
        
    Returns:
        Dictionary containing the parsed and validated skill data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        SkillValidationError: If the file fails validation
    """
    path = Path(skill_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        try:
            skill_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in skill file: {e.msg}",
                e.doc,
                e.pos
            )
    
    validate_skill_schema(skill_data)
    
    return skill_data
