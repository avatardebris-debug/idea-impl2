"""Tests for batch configuration (batch/config.py)."""

import tempfile
from pathlib import Path

import pytest
import yaml

from vastai_init.batch.config import (
    BATCH_OPTIONAL_FIELDS,
    BATCH_PRESET_REF_REQUIRED,
    BATCH_REQUIRED_FIELDS,
    BatchConfig,
    BatchPresetRef,
    TimingConfig,
    find_batch_configs,
    load_batch_config,
)


# Fixtures
@pytest.fixture
def minimal_batch_yaml(tmp_path):
    """Create a minimal batch config YAML file."""
    data = {
        "name": "test-batch",
        "presets": [
            {"preset_path": "presets/gpu.yaml", "count": 2},
            "presets/cpu.yaml",
        ],
    }
    batch_file = tmp_path / "batch.yaml"
    with open(batch_file, "w") as f:
        yaml.dump(data, f)
    return batch_file


@pytest.fixture
def full_batch_yaml(tmp_path):
    """Create a full batch config YAML file."""
    data = {
        "name": "full-batch",
        "presets": [
            {"preset_path": "presets/gpu.yaml", "count": 3},
            {"preset_path": "presets/cpu.yaml", "count": 1},
        ],
        "timing": {
            "delay_seconds": 5.0,
            "stagger_percent": 10.0,
        },
        "concurrency": 4,
        "timeout": 7200,
    }
    batch_file = tmp_path / "full_batch.yaml"
    with open(batch_file, "w") as f:
        yaml.dump(data, f)
    return batch_file


# Tests for BatchPresetRef
class TestBatchPresetRef:
    """Tests for BatchPresetRef dataclass."""

    def test_default_values(self):
        ref = BatchPresetRef(preset_path="test.yaml")
        assert ref.preset_path == "test.yaml"
        assert ref.count == 1

    def test_custom_values(self):
        ref = BatchPresetRef(preset_path="test.yaml", count=5)
        assert ref.preset_path == "test.yaml"
        assert ref.count == 5

    def test_to_dict(self):
        ref = BatchPresetRef(preset_path="test.yaml", count=3)
        d = ref.to_dict()
        assert d == {"preset_path": "test.yaml", "count": 3}

    def test_from_dict(self):
        data = {"preset_path": "test.yaml", "count": 4}
        ref = BatchPresetRef.from_dict(data)
        assert ref.preset_path == "test.yaml"
        assert ref.count == 4

    def test_from_dict_defaults_count(self):
        data = {"preset_path": "test.yaml"}
        ref = BatchPresetRef.from_dict(data)
        assert ref.count == 1


class TestTimingConfig:
    """Tests for TimingConfig dataclass."""

    def test_default_values(self):
        timing = TimingConfig()
        assert timing.delay_seconds == 0.0
        assert timing.stagger_percent == 0.0

    def test_custom_values(self):
        timing = TimingConfig(delay_seconds=5.0, stagger_percent=10.0)
        assert timing.delay_seconds == 5.0
        assert timing.stagger_percent == 10.0

    def test_to_dict(self):
        timing = TimingConfig(delay_seconds=3.5, stagger_percent=15.0)
        d = timing.to_dict()
        assert d == {"delay_seconds": 3.5, "stagger_percent": 15.0}

    def test_from_dict(self):
        data = {"delay_seconds": 7.0, "stagger_percent": 20.0}
        timing = TimingConfig.from_dict(data)
        assert timing.delay_seconds == 7.0
        assert timing.stagger_percent == 20.0

    def test_from_dict_defaults(self):
        data = {}
        timing = TimingConfig.from_dict(data)
        assert timing.delay_seconds == 0.0
        assert timing.stagger_percent == 0.0


class TestBatchConfig:
    """Tests for BatchConfig dataclass."""

    def test_default_values(self):
        config = BatchConfig(name="test", presets=[])
        assert config.name == "test"
        assert config.presets == []
        assert config.timing.delay_seconds == 0.0
        assert config.concurrency == 1
        assert config.timeout == 3600

    def test_custom_values(self):
        presets = [BatchPresetRef("a.yaml", 2)]
        timing = TimingConfig(delay_seconds=5.0, stagger_percent=10.0)
        config = BatchConfig(
            name="test",
            presets=presets,
            timing=timing,
            concurrency=4,
            timeout=7200,
        )
        assert config.name == "test"
        assert len(config.presets) == 1
        assert config.timing.delay_seconds == 5.0
        assert config.concurrency == 4
        assert config.timeout == 7200

    def test_to_dict(self):
        presets = [BatchPresetRef("a.yaml", 2)]
        config = BatchConfig(name="test", presets=presets, concurrency=2, timeout=1800)
        d = config.to_dict()
        assert d["name"] == "test"
        assert len(d["presets"]) == 1
        assert d["concurrency"] == 2
        assert d["timeout"] == 1800
        assert d["_source_path"] == ""


# Tests for schema constants
class TestSchemaConstants:
    """Tests for batch config schema constants."""

    def test_required_fields(self):
        assert "name" in BATCH_REQUIRED_FIELDS
        assert "presets" in BATCH_REQUIRED_FIELDS

    def test_preset_ref_required(self):
        assert "preset_path" in BATCH_PRESET_REF_REQUIRED

    def test_optional_fields_structure(self):
        for field, info in BATCH_OPTIONAL_FIELDS.items():
            assert "default" in info
            assert "type" in info


# Tests for load_batch_config
class TestLoadBatchConfig:
    """Tests for load_batch_config function."""

    def test_load_minimal_config(self, minimal_batch_yaml):
        config = load_batch_config(minimal_batch_yaml)
        assert config.name == "test-batch"
        assert len(config.presets) == 2
        assert config.presets[0].preset_path == "presets/gpu.yaml"
        assert config.presets[0].count == 2
        assert config.presets[1].preset_path == "presets/cpu.yaml"
        assert config.presets[1].count == 1
        assert config.timing.delay_seconds == 0.0
        assert config.concurrency == 1
        assert config.timeout == 3600

    def test_load_full_config(self, full_batch_yaml):
        config = load_batch_config(full_batch_yaml)
        assert config.name == "full-batch"
        assert len(config.presets) == 2
        assert config.presets[0].count == 3
        assert config.presets[1].count == 1
        assert config.timing.delay_seconds == 5.0
        assert config.timing.stagger_percent == 10.0
        assert config.concurrency == 4
        assert config.timeout == 7200

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_batch_config(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("{{invalid yaml")
        with pytest.raises(Exception):  # yaml.YAMLError
            load_batch_config(bad_yaml)

    def test_load_non_dict_yaml(self, tmp_path):
        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- item1\n- item2\n")
        with pytest.raises(Exception):  # yaml.YAMLError
            load_batch_config(list_yaml)

    def test_load_string_preset_refs(self, minimal_batch_yaml):
        config = load_batch_config(minimal_batch_yaml)
        assert isinstance(config.presets[1].preset_path, str)

    def test_load_dict_preset_refs(self, minimal_batch_yaml):
        config = load_batch_config(minimal_batch_yaml)
        assert isinstance(config.presets[0].preset_path, str)
        assert config.presets[0].count == 2

    def test_load_missing_name(self, tmp_path):
        data = {"presets": [{"preset_path": "a.yaml"}]}
        batch_file = tmp_path / "no_name.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.name == "unnamed-batch"

    def test_load_missing_presets(self, tmp_path):
        data = {"name": "test"}
        batch_file = tmp_path / "no_presets.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.presets == []

    def test_load_missing_timing(self, tmp_path):
        data = {"name": "test", "presets": []}
        batch_file = tmp_path / "no_timing.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.timing.delay_seconds == 0.0
        assert config.timing.stagger_percent == 0.0

    def test_load_missing_concurrency(self, tmp_path):
        data = {"name": "test", "presets": []}
        batch_file = tmp_path / "no_concurrency.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.concurrency == 1

    def test_load_missing_timeout(self, tmp_path):
        data = {"name": "test", "presets": []}
        batch_file = tmp_path / "no_timeout.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.timeout == 3600

    def test_load_converts_concurrency_to_int(self, tmp_path):
        data = {"name": "test", "presets": [], "concurrency": "4"}
        batch_file = tmp_path / "str_concurrency.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.concurrency == 4

    def test_load_converts_timeout_to_int(self, tmp_path):
        data = {"name": "test", "presets": [], "timeout": "7200"}
        batch_file = tmp_path / "str_timeout.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.timeout == 7200

    def test_load_timing_as_dict(self, tmp_path):
        data = {
            "name": "test",
            "presets": [],
            "timing": {"delay_seconds": 10.0, "stagger_percent": 5.0},
        }
        batch_file = tmp_path / "timing_dict.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.timing.delay_seconds == 10.0
        assert config.timing.stagger_percent == 5.0

    def test_load_timing_as_non_dict(self, tmp_path):
        data = {"name": "test", "presets": [], "timing": "invalid"}
        batch_file = tmp_path / "timing_invalid.yaml"
        with open(batch_file, "w") as f:
            yaml.dump(data, f)
        config = load_batch_config(batch_file)
        assert config.timing.delay_seconds == 0.0
        assert config.timing.stagger_percent == 0.0

    def test_load_preserves_source_path(self, minimal_batch_yaml):
        config = load_batch_config(minimal_batch_yaml)
        assert config._source_path == str(minimal_batch_yaml)


# Tests for find_batch_configs
class TestFindBatchConfigs:
    """Tests for find_batch_configs function."""

    def test_find_in_existing_directory(self, tmp_path):
        # Create some batch config files
        (tmp_path / "batch1.yaml").write_text("name: test\npresets: []\n")
        (tmp_path / "batch2.yml").write_text("name: test\npresets: []\n")
        (tmp_path / "batch3.yaml").write_text("name: test\npresets: []\n")

        configs = find_batch_configs(tmp_path)
        assert len(configs) == 3

    def test_find_in_nonexistent_directory(self):
        configs = find_batch_configs("/nonexistent/path")
        assert configs == []

    def test_find_in_empty_directory(self, tmp_path):
        configs = find_batch_configs(tmp_path)
        assert configs == []

    def test_find_only_yaml_yml_files(self, tmp_path):
        (tmp_path / "batch.yaml").write_text("name: test\npresets: []\n")
        (tmp_path / "batch.yml").write_text("name: test\npresets: []\n")
        (tmp_path / "batch.json").write_text("{}")
        (tmp_path / "batch.txt").write_text("test")

        configs = find_batch_configs(tmp_path)
        assert len(configs) == 2
        assert all(config.suffix in (".yaml", ".yml") for config in configs)

    def test_find_returns_sorted_paths(self, tmp_path):
        (tmp_path / "z_batch.yaml").write_text("name: test\npresets: []\n")
        (tmp_path / "a_batch.yaml").write_text("name: test\npresets: []\n")
        (tmp_path / "m_batch.yaml").write_text("name: test\npresets: []\n")

        configs = find_batch_configs(tmp_path)
        assert len(configs) == 3
        assert configs[0].name == "a_batch.yaml"
        assert configs[1].name == "m_batch.yaml"
        assert configs[2].name == "z_batch.yaml"

    def test_find_with_none_directory(self):
        # Should use default directory
        configs = find_batch_configs(None)
        assert isinstance(configs, list)
