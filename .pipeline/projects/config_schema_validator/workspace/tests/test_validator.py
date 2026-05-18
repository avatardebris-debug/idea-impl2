"""Tests for config_validator."""

import yaml
from pathlib import Path
from typer.testing import CliRunner

from config_validator.cli import app

runner = CliRunner()


def test_validate_valid_constitution(tmp_path):
    """Test validating a valid constitution schema."""
    config_file = tmp_path / "constitution.yaml"
    valid_data = {
        "version": "1.0",
        "phases": {
            "planning": {
                "agent_name": "Planner",
                "temperature": 0.5,
                "prompts": [
                    {"role": "system", "content": "You are a planner."}
                ]
            }
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(valid_data, f)

    result = runner.invoke(app, [str(config_file), "--type", "constitution"])
    if result.exit_code != 0:
        print(f"OUTPUT: {result.stdout}")
    assert result.exit_code == 0
    assert "Successfully validated" in result.stdout


def test_validate_invalid_schema(tmp_path):
    """Test validating with invalid schema data."""
    config_file = tmp_path / "invalid.yaml"
    invalid_data = {
        "phases": {
            "planning": {
                # Missing agent_name
                "temperature": "not a float",
            }
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(invalid_data, f)

    result = runner.invoke(app, [str(config_file), "--type", "constitution"])
    assert result.exit_code == 1
    assert "Validation failed" in result.stderr


def test_validate_unknown_type(tmp_path):
    """Test with an unknown schema type."""
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump({"key": "value"}, f)

    result = runner.invoke(app, [str(config_file), "--type", "unknown_schema"])
    assert result.exit_code == 1
    assert "Unknown schema type" in result.stderr
