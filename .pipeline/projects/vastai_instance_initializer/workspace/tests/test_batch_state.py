"""Tests for batch state serialization (Task 4)."""

import json
from pathlib import Path

import pytest

from vastai_init.batch.state import (
    BatchState,
    InstanceState,
    load_batch_state,
    save_batch_state,
)


# ── InstanceState ────────────────────────────────────────────────────────────

class TestInstanceState:
    def test_defaults(self):
        inst = InstanceState(instance_id="i1", preset_path="p.yaml", count_index=0)
        assert inst.status == "pending"
        assert inst.error == ""
        assert inst.started_at == 0.0
        assert inst.stopped_at == 0.0
        assert inst.timing_offset == 0.0

    def test_custom_values(self):
        inst = InstanceState(
            instance_id="i1",
            preset_path="p.yaml",
            count_index=1,
            status="running",
            error="",
            started_at=100.0,
            stopped_at=0.0,
            timing_offset=5.0,
        )
        assert inst.instance_id == "i1"
        assert inst.status == "running"
        assert inst.started_at == 100.0
        assert inst.timing_offset == 5.0


# ── BatchState ───────────────────────────────────────────────────────────────

class TestBatchState:
    def test_defaults(self):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 1}],
            timing={"delay_seconds": 0.0, "stagger_percent": 0.0},
            concurrency=1,
            timeout=300,
        )
        assert state.instances == []
        assert state.started_at == 0.0
        assert state.completed_at == 0.0
        assert state.status == "pending"

    def test_with_instances(self):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 2}],
            timing={"delay_seconds": 0.0, "stagger_percent": 0.0},
            concurrency=1,
            timeout=300,
            instances=[
                InstanceState(instance_id="i1", preset_path="p.yaml", count_index=0, status="completed"),
                InstanceState(instance_id="i2", preset_path="p.yaml", count_index=1, status="pending"),
            ],
            started_at=1000.0,
            completed_at=1010.0,
            status="running",
        )
        assert len(state.instances) == 2
        assert state.instances[0].status == "completed"
        assert state.instances[1].status == "pending"
        assert state.started_at == 1000.0
        assert state.completed_at == 1010.0
        assert state.status == "running"


# ── save_batch_state ─────────────────────────────────────────────────────────

class TestSaveBatchState:
    def test_save_creates_file(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 1}],
            timing={"delay_seconds": 0.0, "stagger_percent": 0.0},
            concurrency=1,
            timeout=300,
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)
        assert path.exists()

    def test_save_creates_nested_dirs(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        nested_path = tmp_path / "a" / "b" / "c" / "state.json"
        save_batch_state(state, nested_path)
        assert nested_path.exists()

    def test_save_json_format(self, tmp_path):
        state = BatchState(
            batch_name="test-batch",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 2}],
            timing={"delay_seconds": 10.0, "stagger_percent": 50.0},
            concurrency=3,
            timeout=600,
            instances=[
                InstanceState(instance_id="i1", preset_path="p.yaml", count_index=0, status="completed"),
            ],
            started_at=1000.0,
            completed_at=1010.0,
            status="completed",
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        data = json.loads(path.read_text())
        assert data["batch_name"] == "test-batch"
        assert data["source_path"] == "test.yaml"
        assert data["concurrency"] == 3
        assert data["timeout"] == 600
        assert len(data["instances"]) == 1
        assert data["instances"][0]["instance_id"] == "i1"
        assert data["instances"][0]["status"] == "completed"
        assert data["started_at"] == 1000.0
        assert data["completed_at"] == 1010.0
        assert data["status"] == "completed"

    def test_save_empty_instances(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        data = json.loads(path.read_text())
        assert data["instances"] == []


# ── load_batch_state ─────────────────────────────────────────────────────────

class TestLoadBatchState:
    def test_load_existing_file(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 1}],
            timing={"delay_seconds": 10.0, "stagger_percent": 50.0},
            concurrency=2,
            timeout=300,
            instances=[
                InstanceState(instance_id="i1", preset_path="p.yaml", count_index=0, status="completed"),
            ],
            started_at=1000.0,
            completed_at=1010.0,
            status="completed",
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        loaded = load_batch_state(path)
        assert loaded.batch_name == "test"
        assert loaded.source_path == "test.yaml"
        assert loaded.concurrency == 2
        assert loaded.timeout == 300
        assert len(loaded.instances) == 1
        assert loaded.instances[0].instance_id == "i1"
        assert loaded.instances[0].status == "completed"
        assert loaded.started_at == 1000.0
        assert loaded.completed_at == 1010.0
        assert loaded.status == "completed"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_batch_state(tmp_path / "nonexistent.json")

    def test_load_preserves_all_fields(self, tmp_path):
        """Test that all fields are preserved through save/load cycle."""
        state = BatchState(
            batch_name="complex-batch",
            source_path="complex.yaml",
            presets=[
                {"preset_path": "p1.yaml", "count": 2},
                {"preset_path": "p2.yaml", "count": 3},
            ],
            timing={"delay_seconds": 15.0, "stagger_percent": 75.0},
            concurrency=5,
            timeout=900,
            instances=[
                InstanceState(instance_id="i1", preset_path="p1.yaml", count_index=0, status="completed", started_at=100.0),
                InstanceState(instance_id="i2", preset_path="p1.yaml", count_index=1, status="running", started_at=110.0),
                InstanceState(instance_id="", preset_path="p2.yaml", count_index=0, status="pending"),
            ],
            started_at=1000.0,
            completed_at=0.0,
            status="running",
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        loaded = load_batch_state(path)

        assert loaded.batch_name == state.batch_name
        assert loaded.source_path == state.source_path
        assert len(loaded.presets) == len(state.presets)
        assert loaded.presets[0]["preset_path"] == state.presets[0]["preset_path"]
        assert loaded.presets[1]["count"] == state.presets[1]["count"]
        assert loaded.timing["delay_seconds"] == state.timing["delay_seconds"]
        assert loaded.timing["stagger_percent"] == state.timing["stagger_percent"]
        assert loaded.concurrency == state.concurrency
        assert loaded.timeout == state.timeout
        assert len(loaded.instances) == len(state.instances)
        assert loaded.instances[0].instance_id == state.instances[0].instance_id
        assert loaded.instances[0].status == state.instances[0].status
        assert loaded.instances[0].started_at == state.instances[0].started_at
        assert loaded.instances[1].status == state.instances[1].status
        assert loaded.instances[2].status == state.instances[2].status
        assert loaded.started_at == state.started_at
        assert loaded.completed_at == state.completed_at
        assert loaded.status == state.status

    def test_load_with_empty_instances(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        loaded = load_batch_state(path)
        assert loaded.instances == []

    def test_load_with_zero_values(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={"delay_seconds": 0.0, "stagger_percent": 0.0},
            concurrency=0,
            timeout=0,
            instances=[],
            started_at=0.0,
            completed_at=0.0,
            status="pending",
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)

        loaded = load_batch_state(path)
        assert loaded.concurrency == 0
        assert loaded.timeout == 0
        assert loaded.started_at == 0.0
        assert loaded.completed_at == 0.0
        assert loaded.status == "pending"


# ── Round-trip consistency ───────────────────────────────────────────────────

class TestRoundTrip:
    def test_full_roundtrip(self, tmp_path):
        """Test that save/load preserves all data exactly."""
        original = BatchState(
            batch_name="roundtrip-test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 3}],
            timing={"delay_seconds": 5.0, "stagger_percent": 25.0},
            concurrency=4,
            timeout=600,
            instances=[
                InstanceState(instance_id="i1", preset_path="p.yaml", count_index=0, status="completed", started_at=100.0, stopped_at=110.0),
                InstanceState(instance_id="i2", preset_path="p.yaml", count_index=1, status="failed", error="timeout", started_at=120.0, stopped_at=130.0),
                InstanceState(instance_id="", preset_path="p.yaml", count_index=2, status="pending"),
            ],
            started_at=1000.0,
            completed_at=0.0,
            status="running",
        )

        path = tmp_path / "state.json"
        save_batch_state(original, path)
        loaded = load_batch_state(path)

        assert loaded.batch_name == original.batch_name
        assert loaded.source_path == original.source_path
        assert loaded.presets == original.presets
        assert loaded.timing == original.timing
        assert loaded.concurrency == original.concurrency
        assert loaded.timeout == original.timeout
        assert len(loaded.instances) == len(original.instances)

        for orig_inst, load_inst in zip(original.instances, loaded.instances):
            assert orig_inst.instance_id == load_inst.instance_id
            assert orig_inst.preset_path == load_inst.preset_path
            assert orig_inst.count_index == load_inst.count_index
            assert orig_inst.status == load_inst.status
            assert orig_inst.error == load_inst.error
            assert orig_inst.started_at == load_inst.started_at
            assert orig_inst.stopped_at == load_inst.stopped_at
            assert orig_inst.timing_offset == load_inst.timing_offset

        assert loaded.started_at == original.started_at
        assert loaded.completed_at == original.completed_at
        assert loaded.status == original.status

    def test_multiple_saves_overwrite(self, tmp_path):
        """Test that saving multiple times overwrites the file."""
        path = tmp_path / "state.json"

        # First save
        state1 = BatchState(
            batch_name="first",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        save_batch_state(state1, path)
        assert json.loads(path.read_text())["batch_name"] == "first"

        # Second save
        state2 = BatchState(
            batch_name="second",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=2,
            timeout=600,
        )
        save_batch_state(state2, path)
        data = json.loads(path.read_text())
        assert data["batch_name"] == "second"
        assert data["concurrency"] == 2
        assert data["timeout"] == 600


# ── Path handling ────────────────────────────────────────────────────────────

class TestPathHandling:
    def test_save_with_path_object(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)
        assert path.exists()

    def test_save_with_string_path(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path_str = str(tmp_path / "state.json")
        save_batch_state(state, path_str)
        assert Path(path_str).exists()

    def test_load_with_path_object(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path = tmp_path / "state.json"
        save_batch_state(state, path)
        loaded = load_batch_state(path)
        assert loaded.batch_name == "test"

    def test_load_with_string_path(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[],
            timing={},
            concurrency=1,
            timeout=300,
        )
        path_str = str(tmp_path / "state.json")
        save_batch_state(state, path_str)
        loaded = load_batch_state(path_str)
        assert loaded.batch_name == "test"
