"""
Tests for json_skill.runtime module.
"""

import json
import tempfile
import os
from pathlib import Path

from json_skill.runtime import SkillRuntime, SkillExecutionError


def _make_skill_file(data: dict) -> str:
    """Helper: write skill data to a temp JSON file, return path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        return f.name


def _make_skill_data() -> dict:
    return {
        "name": "test_skill",
        "description": "A test skill",
        "system_prompt": "You are a test assistant.",
        "functions": [
            {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            }
        ],
        "examples": [
            {"input": {"a": 1, "b": 2}, "output": 3}
        ]
    }


# ---------- SkillRuntime basic ---

def test_runtime_load_skill():
    """Runtime loads a skill from a JSON file."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        assert runtime.skill is not None
        assert runtime.skill["name"] == "test_skill"
    finally:
        os.unlink(path)


def test_runtime_load_skill_from_path():
    """Runtime loads a skill from a Path object."""
    data = _make_skill_data()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = Path(f.name)
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        assert runtime.skill["name"] == "test_skill"
    finally:
        os.unlink(str(path))


def test_runtime_build_payload():
    """Runtime builds a payload dict with system_prompt and functions."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        payload = runtime.build_payload()
        assert "system_prompt" in payload
        assert "functions" in payload
        assert payload["system_prompt"] == "You are a test assistant."
        assert len(payload["functions"]) == 1
        assert payload["functions"][0]["name"] == "add"
    finally:
        os.unlink(path)


def test_runtime_register_and_execute():
    """Runtime registers a handler and executes it."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)

        def add_impl(a: int, b: int) -> int:
            return a + b

        runtime.register_function("add", add_impl)
        result = runtime.execute("add", {"a": 10, "b": 20})
        assert result == 30
    finally:
        os.unlink(path)


def test_runtime_execute_unknown_function():
    """Executing an unknown function returns None."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        result = runtime.execute("nonexistent", {})
        assert result is None
    finally:
        os.unlink(path)


def test_runtime_execute_with_exception():
    """Executing a function that raises returns None."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)

        def bad_fn():
            raise ValueError("oops")

        runtime.register_function("bad", bad_fn)
        result = runtime.execute("bad", {})
        assert result is None
    finally:
        os.unlink(path)


def test_runtime_build_payload_with_examples():
    """Payload includes examples when present."""
    data = _make_skill_data()
    data["examples"] = [
        {"input": {"a": 1, "b": 2}, "output": 3},
        {"input": {"a": 10, "b": 20}, "output": 30}
    ]
    path = _make_skill_file(data)
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        payload = runtime.build_payload()
        assert "examples" in payload
        assert len(payload["examples"]) == 2
    finally:
        os.unlink(path)


def test_runtime_no_skill_load():
    """build_payload raises when no skill is loaded."""
    runtime = SkillRuntime()
    try:
        runtime.build_payload()
        assert False, "Expected SkillExecutionError"
    except SkillExecutionError:
        pass


def test_runtime_execute_no_skill_load():
    """execute raises when no skill is loaded."""
    runtime = SkillRuntime()
    try:
        runtime.execute("fn", {})
        assert False, "Expected SkillExecutionError"
    except SkillExecutionError:
        pass


def test_runtime_clear():
    """clear resets the runtime."""
    path = _make_skill_file(_make_skill_data())
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)
        runtime.register_function("add", lambda a, b: a + b)
        runtime.clear()
        assert runtime.skill is None
        assert runtime.dispatcher.list_functions() == []
    finally:
        os.unlink(path)


def test_runtime_full_pipeline():
    """End-to-end: load, register, execute, build payload."""
    data = {
        "name": "calculator",
        "description": "A calculator skill",
        "system_prompt": "You are a calculator.",
        "functions": [
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    },
                    "required": ["x", "y"]
                }
            }
        ],
        "examples": [
            {"input": {"x": 3, "y": 4}, "output": 12}
        ]
    }
    path = _make_skill_file(data)
    try:
        runtime = SkillRuntime()
        runtime.load_skill(path)

        def multiply_impl(x: float, y: float) -> float:
            return x * y

        runtime.register_function("multiply", multiply_impl)

        # Execute
        result = runtime.execute("multiply", {"x": 6, "y": 7})
        assert result == 42

        # Build payload
        payload = runtime.build_payload()
        assert payload["system_prompt"] == "You are a calculator."
        assert len(payload["functions"]) == 1
        assert payload["functions"][0]["name"] == "multiply"
        assert len(payload["examples"]) == 1
    finally:
        os.unlink(path)
