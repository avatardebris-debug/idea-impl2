"""Tests for batch config schema and loader (Task 1)."""

import os
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
    _parse_batch_config,
)
from vastai_init.batch.validator import (
    BatchConfigValidationError,
    validate_batch_config,
    validate_batch_config_raw,
)


# ── BatchPresetRef ──────────────────────────────────────────────────────────

class TestBatchPresetRef:
    def test_defaults(self):
        ref = BatchPresetRef(preset_path="presets/default.yaml")
        assert ref.count == 1

    def test_custom_count(self):
        ref = BatchPresetRef(preset_path="presets/default.yaml", count=5)
        assert ref.count == 5

    def test_to_dict(self):
        ref = BatchPresetRef(preset_path="p.yaml", count=3)
        d = ref.to_dict()
        assert d == {"preset_path": "p.yaml", "count": 3}

    def test_from_dict(self):
        ref = BatchPresetRef.from_dict({"preset_path": "p.yaml", "count": 2})
        assert ref.preset_path == "p.yaml"
        assert ref.count == 2

    def test_from_dict_defaults(self):
        ref = BatchPresetRef.from_dict({"preset_path": "p.yaml"})
        assert ref.count == 1


# ── TimingConfig ────────────────────────────────────────────────────────────

class TestTimingConfig:
    def test_defaults(self):
        t = TimingConfig()
        assert t.delay_seconds == 0.0
        assert t.stagger_percent == 0.0

    def test_custom(self):
        t = TimingConfig(delay_seconds=30.0, stagger_percent=25.0)
        assert t.delay_seconds == 30.0
        assert t.stagger_percent == 25.0

    def test_to_dict(self):
        t = TimingConfig(delay_seconds=10.0, stagger_percent=50.0)
        assert t.to_dict() == {"delay_seconds": 10.0, "stagger_percent": 50.0}

    def test_from_dict(self):
        t = TimingConfig.from_dict({"delay_seconds": 15.0, "stagger_percent": 30.0})
        assert t.delay_seconds == 15.0
        assert t.stagger_percent == 30.0

    def test_from_dict_defaults(self):
        t = TimingConfig.from_dict({})
        assert t.delay_seconds == 0.0
        assert t.stagger_percent == 0.0


# ── BatchConfig ─────────────────────────────────────────────────────────────

class TestBatchConfig:
    def test_to_dict_roundtrip(self):
        config = BatchConfig(
            name="test-batch",
            presets=[BatchPresetRef("p.yaml", count=2)],
            timing=TimingConfig(delay_seconds=10.0),
            concurrency=3,
            timeout=600,
        )
        d = config.to_dict()
        assert d["name"] == "test-batch"
        assert d["presets"][0]["preset_path"] == "p.yaml"
        assert d["presets"][0]["count"] == 2
        assert d["timing"]["delay_seconds"] == 10.0
        assert d["concurrency"] == 3
        assert d["timeout"] == 600


# ── Schema Constants ────────────────────────────────────────────────────────

class TestSchemaConstants:
    def test_required_fields(self):
        assert "name" in BATCH_REQUIRED_FIELDS
        assert "presets" in BATCH_REQUIRED_FIELDS

    def test_preset_ref_required(self):
        assert "preset_path" in BATCH_PRESET_REF_REQUIRED

    def test_optional_fields(self):
        assert "timing" in BATCH_OPTIONAL_FIELDS
        assert "concurrency" in BATCH_OPTIONAL_FIELDS
        assert "timeout" in BATCH_OPTIONAL_FIELDS


# ── _parse_batch_config ─────────────────────────────────────────────────────

class TestParseBatchConfig:
    def test_minimal(self):
        raw = {"name": "test", "presets": [{"preset_path": "p.yaml"}]}
        config = _parse_batch_config(raw, "/tmp/test.yaml")
        assert config.name == "test"
        assert len(config.presets) == 1
        assert config.presets[0].preset_path == "p.yaml"
        assert config.presets[0].count == 1
        assert config.concurrency == 1
        assert config.timeout == 3600

    def test_full(self):
        raw = {
            "name": "full-batch",
            "presets": [
                {"preset_path": "p1.yaml", "count": 3},
                {"preset_path": "p2.yaml", "count": 2},
            ],
            "timing": {"delay_seconds": 15.0, "stagger_percent": 20.0},
            "concurrency": 4,
            "timeout": 7200,
        }
        config = _parse_batch_config(raw, "/tmp/full.yaml")
        assert config.name == "full-batch"
        assert len(config.presets) == 2
        assert config.presets[0].count == 3
        assert config.presets[1].count == 2
        assert config.timing.delay_seconds == 15.0
        assert config.timing.stagger_percent == 20.0
        assert config.concurrency == 4
        assert config.timeout == 7200

    def test_string_presets(self):
        raw = {"name": "test", "presets": ["p1.yaml", "p2.yaml"]}
        config = _parse_batch_config(raw, "/tmp/test.yaml")
        assert len(config.presets) == 2
        assert config.presets[0].preset_path == "p1.yaml"
        assert config.presets[0].count == 1
        assert config.presets[1].preset_path == "p2.yaml"

    def test_empty_presets(self):
        raw = {"name": "test", "presets": []}
        config = _parse_batch_config(raw, "/tmp/test.yaml")
        assert len(config.presets) == 0


# ── load_batch_config ───────────────────────────────────────────────────────

class TestLoadBatchConfig:
    def test_load_valid(self, tmp_path):
        config_yaml = tmp_path / "batch.yaml"
        config_yaml.write_text(
            yaml.dump({
                "name": "test-batch",
                "presets": [{"preset_path": "p.yaml", "count": 2}],
                "concurrency": 3,
            })
        )
        config = load_batch_config(config_yaml)
        assert config.name == "test-batch"
        assert config.presets[0].count == 2
        assert config.concurrency == 3

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_batch_config("/nonexistent/batch.yaml")

    def test_load_not_yaml(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("not: valid: yaml: [[[")
        with pytest.raises(yaml.YAMLError):
            load_batch_config(bad_file)

    def test_load_non_mapping(self, tmp_path):
        arr_file = tmp_path / "arr.yaml"
        arr_file.write_text("- item1\n- item2\n")
        with pytest.raises(yaml.YAMLError, match="mapping"):
            load_batch_config(arr_file)


# ── validate_batch_config ───────────────────────────────────────────────────

class TestValidateBatchConfig:
    def test_valid_config(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml", count=1)],
            concurrency=1,
            timeout=300,
        )
        # Should not raise
        validate_batch_config(config)

    def test_empty_name(self):
        config = BatchConfig(
            name="",
            presets=[BatchPresetRef("presets/default.yaml")],
        )
        with pytest.raises(BatchConfigValidationError, match="name"):
            validate_batch_config(config)

    def test_empty_presets(self):
        config = BatchConfig(
            name="test",
            presets=[],
        )
        with pytest.raises(BatchConfigValidationError, match="presets"):
            validate_batch_config(config)

    def test_missing_preset_file(self, tmp_path):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef(str(tmp_path / "nonexistent.yaml"))],
        )
        with pytest.raises(BatchConfigValidationError, match="not found"):
            validate_batch_config(config)

    def test_zero_count(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml", count=0)],
        )
        with pytest.raises(BatchConfigValidationError, match="count"):
            validate_batch_config(config)

    def test_negative_count(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml", count=-1)],
        )
        with pytest.raises(BatchConfigValidationError, match="count"):
            validate_batch_config(config)

    def test_negative_delay(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml")],
            timing=TimingConfig(delay_seconds=-1.0),
        )
        with pytest.raises(BatchConfigValidationError, match="delay_seconds"):
            validate_batch_config(config)

    def test_invalid_stagger(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml")],
            timing=TimingConfig(stagger_percent=150.0),
        )
        with pytest.raises(BatchConfigValidationError, match="stagger_percent"):
            validate_batch_config(config)

    def test_zero_concurrency(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml")],
            concurrency=0,
        )
        with pytest.raises(BatchConfigValidationError, match="concurrency"):
            validate_batch_config(config)

    def test_zero_timeout(self):
        config = BatchConfig(
            name="test",
            presets=[BatchPresetRef("presets/default.yaml")],
            timeout=0,
        )
        with pytest.raises(BatchConfigValidationError, match="timeout"):
            validate_batch_config(config)

    def test_multiple_errors(self):
        config = BatchConfig(
            name="",
            presets=[],
            concurrency=0,
            timeout=0,
        )
        with pytest.raises(BatchConfigValidationError) as exc_info:
            validate_batch_config(config)
        error_msg = str(exc_info.value)
        assert "name" in error_msg
        assert "presets" in error_msg
        assert "concurrency" in error_msg


# ── validate_batch_config_raw ───────────────────────────────────────────────

class TestValidateBatchConfigRaw:
    def test_valid_raw(self):
        raw = {
            "name": "test",
            "presets": [{"preset_path": "p.yaml", "count": 1}],
            "concurrency": 1,
            "timeout": 300,
        }
        errors = validate_batch_config_raw(raw)
        assert errors == []

    def test_missing_name(self):
        raw = {"presets": [{"preset_path": "p.yaml"}]}
        errors = validate_batch_config_raw(raw)
        assert any("name" in e for e in errors)

    def test_missing_presets(self):
        raw = {"name": "test"}
        errors = validate_batch_config_raw(raw)
        assert any("presets" in e for e in errors)

    def test_missing_preset_path(self):
        raw = {"name": "test", "presets": [{"count": 1}]}
        errors = validate_batch_config_raw(raw)
        assert any("preset_path" in e for e in errors)

    def test_invalid_count(self):
        raw = {"name": "test", "presets": [{"preset_path": "p.yaml", "count": 0}]}
        errors = validate_batch_config_raw(raw)
        assert any("count" in e for e in errors)

    def test_invalid_concurrency(self):
        raw = {"name": "test", "presets": [{"preset_path": "p.yaml"}], "concurrency": 0}
        errors = validate_batch_config_raw(raw)
        assert any("concurrency" in e for e in errors)

    def test_invalid_timeout(self):
        raw = {"name": "test", "presets": [{"preset_path": "p.yaml"}], "timeout": -1}
        errors = validate_batch_config_raw(raw)
        assert any("timeout" in e for e in errors)

    def test_invalid_delay(self):
        raw = {
            "name": "test",
            "presets": [{"preset_path": "p.yaml"}],
            "timing": {"delay_seconds": -5},
        }
        errors = validate_batch_config_raw(raw)
        assert any("delay_seconds" in e for e in errors)

    def test_invalid_stagger(self):
        raw = {
            "name": "test",
            "presets": [{"preset_path": "p.yaml"}],
            "timing": {"stagger_percent": 200},
        }
        errors = validate_batch_config_raw(raw)
        assert any("stagger_percent" in e for e in errors)


# ── find_batch_configs ──────────────────────────────────────────────────────

class TestFindBatchConfigs:
    def test_find_in_existing_dir(self, tmp_path):
        # Create some batch config files
        (tmp_path / "batch1.yaml").write_text("name: test1\npresets: []\n")
        (tmp_path / "batch2.yml").write_text("name: test2\npresets: []\n")
        (tmp_path / "not-a-batch.txt").write_text("ignore")

        configs = find_batch_configs(tmp_path)
        assert len(configs) == 2
        assert any("batch1.yaml" in str(c) for c in configs)
        assert any("batch2.yml" in str(c) for c in configs)

    def test_find_in_nonexistent_dir(self):
        configs = find_batch_configs("/nonexistent/directory")
        assert configs == []

    def test_find_default_directory(self):
        # Should not raise even if default dir doesn't exist
        configs = find_batch_configs()
        assert isinstance(configs, list)
