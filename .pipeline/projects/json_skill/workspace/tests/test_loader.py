"""
Tests for json_skill.loader module.
"""

import json
import tempfile
import os
from pathlib import Path

from json_skill.loader import load_skill, validate_skill_schema, SkillValidationError


# ---------- validate_skill_schema ----------

def test_validate_valid_skill():
    """Valid skill data passes validation."""
    data = {
        "name": "test_skill",
        "description": "A test skill",
        "system_prompt": "You are a test assistant.",
        "functions": [
            {
                "name": "greet",
                "description": "Greet someone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        ],
        "examples": [
            {
                "input": {"name": "World"},
                "output": "Hello, World!"
            }
        ]
    }
    # Should not raise
    validate_skill_schema(data)


def test_validate_missing_name():
    """Missing 'name' raises SkillValidationError."""
    data = {"description": "no name"}
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError as e:
        assert "name" in str(e).lower()


def test_validate_missing_description():
    """Missing 'description' raises SkillValidationError."""
    data = {"name": "x"}
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError as e:
        assert "description" in str(e).lower()


def test_validate_missing_system_prompt():
    """Missing 'system_prompt' raises SkillValidationError."""
    data = {"name": "x", "description": "y"}
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError as e:
        assert "system_prompt" in str(e).lower()


def test_validate_functions_not_list():
    """'functions' must be a list."""
    data = {
        "name": "x",
        "description": "y",
        "system_prompt": "z",
        "functions": "not a list"
    }
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError:
        pass


def test_validate_examples_not_list():
    """'examples' must be a list."""
    data = {
        "name": "x",
        "description": "y",
        "system_prompt": "z",
        "examples": "not a list"
    }
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError:
        pass


def test_validate_functions_item_missing_name():
    """Each function item must have 'name'."""
    data = {
        "name": "x",
        "description": "y",
        "system_prompt": "z",
        "functions": [{"description": "no name"}]
    }
    try:
        validate_skill_schema(data)
        assert False, "Expected SkillValidationError"
    except SkillValidationError:
        pass


# ---------- load_skill ----------

def test_load_skill_from_file():
    """load_skill reads and validates a JSON file."""
    data = {
        "name": "file_skill",
        "description": "loaded from file",
        "system_prompt": "You are a file skill.",
        "functions": [],
        "examples": []
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = f.name
    try:
        skill = load_skill(path)
        assert skill["name"] == "file_skill"
        assert skill["system_prompt"] == "You are a file skill."
    finally:
        os.unlink(path)


def test_load_skill_from_pathlib():
    """load_skill accepts a Path object."""
    data = {
        "name": "path_skill",
        "description": "loaded from Path",
        "system_prompt": "path-based",
        "functions": [],
        "examples": []
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = Path(f.name)
    try:
        skill = load_skill(path)
        assert skill["name"] == "path_skill"
    finally:
        os.unlink(str(path))


def test_load_skill_nonexistent():
    """load_skill raises FileNotFoundError for missing file."""
    try:
        load_skill("/nonexistent/path/skill.json")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_load_skill_invalid_json():
    """load_skill raises SkillValidationError for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        f.flush()
        path = f.name
    try:
        load_skill(path)
        assert False, "Expected SkillValidationError"
    except SkillValidationError:
        pass
    finally:
        os.unlink(path)


def test_load_skill_invalid_schema():
    """load_skill raises SkillValidationError for invalid schema."""
    data = {"name": "x"}  # missing required fields
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = f.name
    try:
        load_skill(path)
        assert False, "Expected SkillValidationError"
    except SkillValidationError:
        pass
    finally:
        os.unlink(path)
