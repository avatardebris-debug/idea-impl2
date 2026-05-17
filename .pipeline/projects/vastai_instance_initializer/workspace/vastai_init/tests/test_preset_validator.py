"""Tests for preset validation (validator.py)."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from vastai_init.presets.validator import (
    PresetValidationError,
    _validate_field_type,
    load_preset,
    validate_preset,
)


# Fixtures
@pytest.fixture
def valid_preset_data():
    """Return a minimal valid preset dictionary."""
    return {
        "name": "test-instance",
        "gpu_type": "A100",
        "price_cap": 1.5,
        "storage": "50GB",
        "image": "ubuntu:latest",
    }


@pytest.fixture
def preset_file(tmp_path, valid_preset_data):
    """Create a temporary preset YAML file."""
    preset_file = tmp_path / "test_preset.yaml"
    with open(preset_file, "w") as f:
        yaml.dump(valid_preset_data, f)
    return preset_file


@pytest.fixture
def preset_file_with_optional(tmp_path, valid_preset_data):
    """Create a preset YAML file with optional fields."""
    data = {
        **valid_preset_data,
        "region": "us-east-1",
        "timeout": 600,
        "poll_interval": 15,
        "count": 3,
        "ssh_commands": ["echo hello"],
        "env_vars": {"KEY": "value"},
        "docker_args": {"-v": "/host:/container"},
        "ports": [8080, 9090],
        "labels": {"app": "test"},
    }
    preset_file = tmp_path / "test_preset_full.yaml"
    with open(preset_file, "w") as f:
        yaml.dump(data, f)
    return preset_file


# Tests for _validate_field_type
class TestValidateFieldType:
    """Tests for _validate_field_type helper."""

    def test_valid_string(self):
        assert _validate_field_type("hello", str) is True

    def test_valid_int(self):
        assert _validate_field_type(42, int) is True

    def test_valid_float(self):
        assert _validate_field_type(1.5, float) is True

    def test_valid_list(self):
        assert _validate_field_type([1, 2], list) is True

    def test_valid_dict(self):
        assert _validate_field_type({"a": 1}, dict) is True

    def test_invalid_type(self):
        assert _validate_field_type("hello", int) is False

    def test_invalid_list_type(self):
        assert _validate_field_type([1, 2], str) is False

    def test_invalid_dict_type(self):
        assert _validate_field_type({"a": 1}, list) is False

    def test_none_value(self):
        assert _validate_field_type(None, str) is False

    def test_bool_is_int_subclass(self):
        # In Python, bool is a subclass of int
        assert _validate_field_type(True, int) is True


# Tests for validate_preset
class TestValidatePreset:
    """Tests for validate_preset function."""

    def test_valid_preset(self, valid_preset_data):
        errors = validate_preset(valid_preset_data)
        assert errors == []

    def test_valid_preset_with_optional(self, preset_file_with_optional):
        with open(preset_file_with_optional) as f:
            data = yaml.safe_load(f)
        errors = validate_preset(data)
        assert errors == []

    def test_missing_required_name(self, valid_preset_data):
        data = {k: v for k, v in valid_preset_data.items() if k != "name"}
        errors = validate_preset(data)
        assert any("name" in e for e in errors)

    def test_missing_required_gpu_type(self, valid_preset_data):
        data = {k: v for k, v in valid_preset_data.items() if k != "gpu_type"}
        errors = validate_preset(data)
        assert any("gpu_type" in e for e in errors)

    def test_missing_required_price_cap(self, valid_preset_data):
        data = {k: v for k, v in valid_preset_data.items() if k != "price_cap"}
        errors = validate_preset(data)
        assert any("price_cap" in e for e in errors)

    def test_missing_required_storage(self, valid_preset_data):
        data = {k: v for k, v in valid_preset_data.items() if k != "storage"}
        errors = validate_preset(data)
        assert any("storage" in e for e in errors)

    def test_missing_required_image(self, valid_preset_data):
        data = {k: v for k, v in valid_preset_data.items() if k != "image"}
        errors = validate_preset(data)
        assert any("image" in e for e in errors)

    def test_invalid_type_for_timeout(self, valid_preset_data):
        data = {**valid_preset_data, "timeout": "not_an_int"}
        errors = validate_preset(data)
        assert any("timeout" in e for e in errors)

    def test_invalid_type_for_count(self, valid_preset_data):
        data = {**valid_preset_data, "count": "not_an_int"}
        errors = validate_preset(data)
        assert any("count" in e for e in errors)

    def test_invalid_type_for_price_cap(self, valid_preset_data):
        data = {**valid_preset_data, "price_cap": "not_a_number"}
        errors = validate_preset(data)
        assert any("price_cap" in e for e in errors)

    def test_invalid_type_for_ssh_commands(self, valid_preset_data):
        data = {**valid_preset_data, "ssh_commands": "not_a_list"}
        errors = validate_preset(data)
        assert any("ssh_commands" in e for e in errors)

    def test_invalid_type_for_env_vars(self, valid_preset_data):
        data = {**valid_preset_data, "env_vars": "not_a_dict"}
        errors = validate_preset(data)
        assert any("env_vars" in e for e in errors)

    def test_invalid_type_for_docker_args(self, valid_preset_data):
        data = {**valid_preset_data, "docker_args": "not_a_dict"}
        errors = validate_preset(data)
        assert any("docker_args" in e for e in errors)

    def test_invalid_type_for_ports(self, valid_preset_data):
        data = {**valid_preset_data, "ports": "not_a_list"}
        errors = validate_preset(data)
        assert any("ports" in e for e in errors)

    def test_invalid_type_for_labels(self, valid_preset_data):
        data = {**valid_preset_data, "labels": "not_a_dict"}
        errors = validate_preset(data)
        assert any("labels" in e for e in errors)

    def test_empty_dict(self):
        errors = validate_preset({})
        assert len(errors) == 5  # All 5 required fields missing

    def test_non_dict_input(self):
        with pytest.raises(PresetValidationError):
            validate_preset("not a dict")

    def test_multiple_errors(self, valid_preset_data):
        data = {
            "name": 123,  # wrong type
            "gpu_type": 456,  # wrong type
            "price_cap": "bad",  # wrong type
        }
        errors = validate_preset(data)
        assert len(errors) >= 3


# Tests for load_preset
class TestLoadPreset:
    """Tests for load_preset function."""

    def test_load_valid_preset(self, preset_file):
        preset = load_preset(preset_file)
        assert preset["name"] == "test-instance"
        assert preset["gpu_type"] == "A100"
        assert preset["price_cap"] == 1.5
        assert preset["storage"] == "50GB"
        assert preset["image"] == "ubuntu:latest"

    def test_load_preset_with_optional_fields(self, preset_file_with_optional):
        preset = load_preset(preset_file_with_optional)
        assert preset["region"] == "us-east-1"
        assert preset["timeout"] == 600
        assert preset["poll_interval"] == 15
        assert preset["count"] == 3
        assert preset["ssh_commands"] == ["echo hello"]
        assert preset["env_vars"] == {"KEY": "value"}
        assert preset["docker_args"] == {"-v": "/host:/container"}
        assert preset["ports"] == [8080, 9090]
        assert preset["labels"] == {"app": "test"}

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_preset(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("{{invalid yaml content")
        with pytest.raises(PresetValidationError):
            load_preset(bad_yaml)

    def test_load_non_dict_yaml(self, tmp_path):
        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- item1\n- item2\n")
        with pytest.raises(PresetValidationError):
            load_preset(list_yaml)

    def test_load_invalid_preset(self, tmp_path):
        invalid_preset = tmp_path / "invalid.yaml"
        invalid_preset.write_text("gpu_type: A100\n")  # missing required fields
        with pytest.raises(PresetValidationError):
            load_preset(invalid_preset)

    def test_load_preset_applies_defaults(self, tmp_path):
        minimal = tmp_path / "minimal.yaml"
        minimal.write_text("name: test\ngpu_type: A100\nprice_cap: 1.0\nstorage: 50GB\nimage: ubuntu\n")
        preset = load_preset(minimal)
        assert preset["timeout"] == 300
        assert preset["poll_interval"] == 10
        assert preset["count"] == 1
        assert preset["ssh_commands"] == []
        assert preset["env_vars"] == {}
        assert preset["docker_args"] == {}
        assert preset["ports"] == []
        assert preset["labels"] == {}

    def test_load_preset_source_path(self, preset_file):
        preset = load_preset(preset_file)
        assert preset["_source_path"] == str(preset_file)

    def test_load_preset_with_extra_fields(self, tmp_path):
        extra = tmp_path / "extra.yaml"
        extra.write_text("name: test\ngpu_type: A100\nprice_cap: 1.0\nstorage: 50GB\nimage: ubuntu\nextra_field: ignored\n")
        preset = load_preset(extra)
        assert "extra_field" not in preset

    def test_load_preset_with_none_values(self, tmp_path):
        with_none = tmp_path / "none.yaml"
        with_none.write_text("name: test\ngpu_type: A100\nprice_cap: 1.0\nstorage: 50GB\nimage: ubuntu\ndisk_size: null\n")
        preset = load_preset(with_none)
        assert preset["disk_size"] is None
