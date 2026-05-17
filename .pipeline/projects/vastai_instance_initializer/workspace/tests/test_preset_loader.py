"""Tests for preset validation and loading (Task 4)."""

import tempfile
from pathlib import Path

import pytest
import yaml

from vastai_init.presets.validator import (
    PresetValidationError,
    load_preset,
    validate_preset,
)


# ── Helpers ──────────────────────────────────────────────────

def _make_preset(**overrides) -> dict:
    """Create a minimal valid preset with optional overrides."""
    base = {
        "name": "test-preset",
        "gpu_type": "A100",
        "price_cap": "0.50",
        "storage": "100GB",
        "image": "ubuntu:22.04",
    }
    base.update(overrides)
    return base


def _write_preset_file(preset: dict, tmp_path: Path) -> Path:
    """Write a preset dict to a temp YAML file and return the path."""
    path = tmp_path / "preset.yaml"
    with open(path, "w") as f:
        yaml.dump(preset, f)
    return path


# ── validate_preset: valid presets ─────────────────────────────

class TestValidatePresetValid:
    def test_minimal_valid_preset(self):
        preset = _make_preset()
        result = validate_preset(preset)
        assert result["name"] == "test-preset"
        assert result["gpu_type"] == "A100"

    def test_valid_preset_with_optional_fields(self):
        preset = _make_preset(
            ssh_commands=["echo hello"],
            env_vars={"KEY": "value"},
            region="us-east",
            ports=[8080, 443],
            labels={"app": "test"},
            docker_args={"--gpus": "all"},
        )
        result = validate_preset(preset)
        assert result["ssh_commands"] == ["echo hello"]
        assert result["env_vars"] == {"KEY": "value"}
        assert result["region"] == "us-east"
        assert result["ports"] == [8080, 443]
        assert result["labels"] == {"app": "test"}
        assert result["docker_args"] == {"--gpus": "all"}

    def test_valid_preset_with_numeric_storage(self):
        preset = _make_preset(storage=200)
        result = validate_preset(preset)
        assert result["storage"] == 200

    def test_valid_preset_with_tb_storage(self):
        preset = _make_preset(storage="1TB")
        result = validate_preset(preset)
        assert result["storage"] == "1TB"

    def test_valid_preset_with_disk_size(self):
        preset = _make_preset(disk_size="500GB")
        result = validate_preset(preset)
        assert result["disk_size"] == "500GB"

    def test_valid_preset_with_min_vram(self):
        preset = _make_preset(min_vram=24)
        result = validate_preset(preset)
        assert result["min_vram"] == 24

    def test_valid_preset_with_uptime(self):
        preset = _make_preset(uptime="2h")
        result = validate_preset(preset)
        assert result["uptime"] == "2h"

    def test_valid_preset_with_ssh_public_key(self):
        preset = _make_preset(ssh_public_key="ssh-rsa AAAA...")
        result = validate_preset(preset)
        assert result["ssh_public_key"] == "ssh-rsa AAAA..."

    def test_valid_preset_with_timeout_and_poll_interval(self):
        preset = _make_preset(timeout=600, poll_interval=30)
        result = validate_preset(preset)
        assert result["timeout"] == 600
        assert result["poll_interval"] == 30

    def test_valid_preset_with_count(self):
        preset = _make_preset(count=5)
        result = validate_preset(preset)
        assert result["count"] == 5

    def test_valid_preset_with_zero_price_cap(self):
        preset = _make_preset(price_cap="0")
        result = validate_preset(preset)
        assert result["price_cap"] == "0"

    def test_valid_preset_with_negative_price_cap_raises(self):
        preset = _make_preset(price_cap="-1")
        with pytest.raises(PresetValidationError, match="non-negative"):
            validate_preset(preset)

    def test_valid_preset_with_float_price_cap(self):
        preset = _make_preset(price_cap="0.75")
        result = validate_preset(preset)
        assert result["price_cap"] == "0.75"

    def test_valid_preset_with_integer_price_cap(self):
        preset = _make_preset(price_cap=10)
        result = validate_preset(preset)
        assert result["price_cap"] == 10

    def test_valid_preset_with_integer_storage(self):
        preset = _make_preset(storage=100)
        result = validate_preset(preset)
        assert result["storage"] == 100


# ── validate_preset: missing required fields ─────────────────

class TestValidatePresetMissingRequired:
    def test_missing_name(self):
        preset = _make_preset()
        del preset["name"]
        with pytest.raises(PresetValidationError, match="Missing required field: 'name'"):
            validate_preset(preset)

    def test_missing_gpu_type(self):
        preset = _make_preset()
        del preset["gpu_type"]
        with pytest.raises(PresetValidationError, match="Missing required field: 'gpu_type'"):
            validate_preset(preset)

    def test_missing_price_cap(self):
        preset = _make_preset()
        del preset["price_cap"]
        with pytest.raises(PresetValidationError, match="Missing required field: 'price_cap'"):
            validate_preset(preset)

    def test_missing_storage(self):
        preset = _make_preset()
        del preset["storage"]
        with pytest.raises(PresetValidationError, match="Missing required field: 'storage'"):
            validate_preset(preset)

    def test_missing_image(self):
        preset = _make_preset()
        del preset["image"]
        with pytest.raises(PresetValidationError, match="Missing required field: 'image'"):
            validate_preset(preset)

    def test_missing_all_required(self):
        with pytest.raises(PresetValidationError) as exc_info:
            validate_preset({})
        assert "Missing required field: 'name'" in str(exc_info.value)
        assert "Missing required field: 'gpu_type'" in str(exc_info.value)
        assert "Missing required field: 'price_cap'" in str(exc_info.value)
        assert "Missing required field: 'storage'" in str(exc_info.value)
        assert "Missing required field: 'image'" in str(exc_info.value)


# ── validate_preset: invalid field values ────────────────────

class TestValidatePresetInvalidValues:
    def test_empty_name(self):
        preset = _make_preset(name="")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_whitespace_name(self):
        preset = _make_preset(name="   ")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_empty_gpu_type(self):
        preset = _make_preset(gpu_type="")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_empty_image(self):
        preset = _make_preset(image="")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_invalid_price_cap_type(self):
        preset = _make_preset(price_cap="abc")
        with pytest.raises(PresetValidationError, match="must be a valid number"):
            validate_preset(preset)

    def test_invalid_storage_no_unit(self):
        preset = _make_preset(storage="100")
        with pytest.raises(PresetValidationError, match="must include a unit"):
            validate_preset(preset)

    def test_invalid_storage_type(self):
        preset = _make_preset(storage={"size": 100})
        with pytest.raises(PresetValidationError, match="must be a string with unit or a number"):
            validate_preset(preset)

    def test_empty_gpu_type_string(self):
        preset = _make_preset(gpu_type="  ")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_empty_image_string(self):
        preset = _make_preset(image="  ")
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)


# ── validate_preset: type validation ─────────────────────────

class TestValidatePresetTypes:
    def test_name_not_string(self):
        preset = _make_preset(name=123)
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_gpu_type_not_string(self):
        preset = _make_preset(gpu_type=123)
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_price_cap_not_string_or_number(self):
        preset = _make_preset(price_cap=["0.50"])
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_storage_not_string_or_number(self):
        preset = _make_preset(storage=["100GB"])
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_image_not_string(self):
        preset = _make_preset(image=123)
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_ssh_commands_not_list(self):
        preset = _make_preset(ssh_commands="echo hello")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_env_vars_not_dict(self):
        preset = _make_preset(env_vars="KEY=value")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_timeout_not_int(self):
        preset = _make_preset(timeout="300")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_poll_interval_not_int(self):
        preset = _make_preset(poll_interval="10")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_count_not_int(self):
        preset = _make_preset(count="1")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_ports_not_list(self):
        preset = _make_preset(ports="8080")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_labels_not_dict(self):
        preset = _make_preset(labels="app=test")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)

    def test_docker_args_not_dict(self):
        preset = _make_preset(docker_args="--gpus all")
        with pytest.raises(PresetValidationError, match="invalid type"):
            validate_preset(preset)


# ── validate_preset: None values ────────────────────────────

class TestValidatePresetNoneValues:
    def test_none_required_field(self):
        preset = _make_preset(name=None)
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            validate_preset(preset)

    def test_none_optional_field(self):
        preset = _make_preset(ssh_commands=None)
        result = validate_preset(preset)
        assert result["ssh_commands"] is None

    def test_none_env_vars(self):
        preset = _make_preset(env_vars=None)
        result = validate_preset(preset)
        assert result["env_vars"] is None


# ── validate_preset: unknown fields ─────────────────────────

class TestValidatePresetUnknownFields:
    def test_unknown_field_warns_but_passes(self):
        preset = _make_preset(unknown_field="value")
        result = validate_preset(preset)
        assert result["unknown_field"] == "value"

    def test_multiple_unknown_fields(self):
        preset = _make_preset(field_a=1, field_b="two")
        result = validate_preset(preset)
        assert result["field_a"] == 1
        assert result["field_b"] == "two"


# ── validate_preset: defaults ───────────────────────────────

class TestValidatePresetDefaults:
    def test_missing_optional_fields_get_defaults(self):
        preset = _make_preset()
        result = validate_preset(preset)
        assert result["ssh_commands"] == []
        assert result["env_vars"] == {}
        assert result["disk_size"] is None
        assert result["region"] is None
        assert result["min_vram"] is None
        assert result["uptime"] is None
        assert result["ssh_public_key"] is None
        assert result["docker_args"] == {}
        assert result["ports"] == []
        assert result["labels"] == {}
        assert result["timeout"] == 300
        assert result["poll_interval"] == 10
        assert result["count"] == 1

    def test_existing_optional_fields_not_overwritten(self):
        preset = _make_preset(
            ssh_commands=["ls"],
            timeout=600,
            count=3,
        )
        result = validate_preset(preset)
        assert result["ssh_commands"] == ["ls"]
        assert result["timeout"] == 600
        assert result["count"] == 3

    def test_original_preset_not_mutated(self):
        preset = _make_preset()
        original_keys = set(preset.keys())
        validate_preset(preset)
        assert set(preset.keys()) == original_keys


# ── load_preset: valid files ───────────────────────────────

class TestLoadPresetValid:
    def test_load_minimal_preset(self, tmp_path: Path):
        path = _write_preset_file(_make_preset(), tmp_path)
        result = load_preset(path)
        assert result["name"] == "test-preset"
        assert result["gpu_type"] == "A100"

    def test_load_preset_with_optional_fields(self, tmp_path: Path):
        preset = _make_preset(
            ssh_commands=["echo hello"],
            region="eu-west",
            timeout=600,
        )
        path = _write_preset_file(preset, tmp_path)
        result = load_preset(path)
        assert result["ssh_commands"] == ["echo hello"]
        assert result["region"] == "eu-west"
        assert result["timeout"] == 600

    def test_load_preset_returns_defaults_for_missing(self, tmp_path: Path):
        preset = _make_preset()
        # ssh_commands and timeout are not in the base preset, so they're already missing
        path = _write_preset_file(preset, tmp_path)
        result = load_preset(path)
        assert result["ssh_commands"] == []
        assert result["timeout"] == 300

    def test_load_preset_with_string_path(self, tmp_path: Path):
        preset = _make_preset()
        path = _write_preset_file(preset, tmp_path)
        result = load_preset(str(path))
        assert result["name"] == "test-preset"

    def test_load_preset_with_pathlib_path(self, tmp_path: Path):
        preset = _make_preset()
        path = _write_preset_file(preset, tmp_path)
        result = load_preset(path)
        assert result["name"] == "test-preset"


# ── load_preset: errors ───────────────────────────────────

class TestLoadPresetErrors:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_preset("/nonexistent/path/preset.yaml")

    def test_path_is_directory(self, tmp_path: Path):
        dir_path = tmp_path / "dir"
        dir_path.mkdir()
        with pytest.raises(PresetValidationError, match="not a file"):
            load_preset(dir_path)

    def test_invalid_yaml(self, tmp_path: Path):
        path = tmp_path / "bad.yaml"
        path.write_text("{{invalid yaml:::")
        with pytest.raises(PresetValidationError, match="Invalid YAML"):
            load_preset(path)

    def test_yaml_is_list_not_dict(self, tmp_path: Path):
        path = tmp_path / "list.yaml"
        path.write_text("- item1\n- item2\n")
        with pytest.raises(PresetValidationError, match="must contain a YAML mapping"):
            load_preset(path)

    def test_yaml_is_string_not_dict(self, tmp_path: Path):
        path = tmp_path / "string.yaml"
        path.write_text("just a string")
        with pytest.raises(PresetValidationError, match="must contain a YAML mapping"):
            load_preset(path)

    def test_yaml_is_number_not_dict(self, tmp_path: Path):
        path = tmp_path / "number.yaml"
        path.write_text("42")
        with pytest.raises(PresetValidationError, match="must contain a YAML mapping"):
            load_preset(path)

    def test_yaml_is_null(self, tmp_path: Path):
        path = tmp_path / "null.yaml"
        path.write_text("null")
        with pytest.raises(PresetValidationError, match="must contain a YAML mapping"):
            load_preset(path)

    def test_invalid_preset_raises(self, tmp_path: Path):
        preset = {"name": "", "gpu_type": "A100", "price_cap": "0.50", "storage": "100GB", "image": "ubuntu"}
        path = _write_preset_file(preset, tmp_path)
        with pytest.raises(PresetValidationError, match="must be a non-empty string"):
            load_preset(path)


# ── PresetValidationError ────────────────────────────────

class TestPresetValidationError:
    def test_exception_has_field(self):
        try:
            raise PresetValidationError("test error", field="name")
        except PresetValidationError as e:
            assert e.field == "name"
            assert "test error" in str(e)

    def test_exception_without_field(self):
        try:
            raise PresetValidationError("test error")
        except PresetValidationError as e:
            assert e.field is None
            assert "test error" in str(e)

    def test_exception_is_subclass_of_exception(self):
        assert issubclass(PresetValidationError, Exception)
