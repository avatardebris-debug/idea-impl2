"""Tests for batch orchestrator (Task 2)."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vastai_init.batch.config import BatchConfig, BatchPresetRef, TimingConfig
from vastai_init.batch.orchestrator import BatchOrchestrator, BatchResult, LaunchTask
from vastai_init.batch.state import BatchState, InstanceState, save_batch_state, load_batch_state


# ── BatchPresetRef helper ────────────────────────────────────────────────────

def _make_config(
    preset_paths: list[str] | None = None,
    counts: list[int] | None = None,
    timing: TimingConfig | None = None,
    concurrency: int = 1,
    timeout: int = 300,
) -> BatchConfig:
    """Helper to create a BatchConfig for testing."""
    if preset_paths is None:
        preset_paths = ["presets/default.yaml"]
    if counts is None:
        counts = [1] * len(preset_paths)

    presets = [BatchPresetRef(p, c) for p, c in zip(preset_paths, counts)]
    return BatchConfig(
        name="test-batch",
        presets=presets,
        timing=timing or TimingConfig(),
        concurrency=concurrency,
        timeout=timeout,
    )


# ── LaunchTask ───────────────────────────────────────────────────────────────

class TestLaunchTask:
    def test_defaults(self):
        task = LaunchTask(preset_ref=BatchPresetRef("p.yaml"), count_index=0, timing_offset=0.0)
        assert task.status == "pending"
        assert task.instance_id == ""
        assert task.error == ""
        assert task.started_at == 0.0
        assert task.stopped_at == 0.0

    def test_custom_status(self):
        task = LaunchTask(
            preset_ref=BatchPresetRef("p.yaml"),
            count_index=1,
            timing_offset=5.0,
            status="running",
            instance_id="abc123",
        )
        assert task.status == "running"
        assert task.instance_id == "abc123"
        assert task.timing_offset == 5.0


# ── BatchResult ──────────────────────────────────────────────────────────────

class TestBatchResult:
    def test_defaults(self):
        result = BatchResult(
            batch_name="test",
            total_instances=5,
            launched=3,
            failed=1,
            stopped=1,
            skipped=0,
            elapsed_seconds=10.0,
        )
        assert result.batch_name == "test"
        assert result.total_instances == 5
        assert result.launched == 3
        assert result.failed == 1
        assert result.stopped == 1
        assert result.skipped == 0
        assert result.elapsed_seconds == 10.0
        assert result.errors == []


# ── BatchOrchestrator._build_tasks ───────────────────────────────────────────

class TestBuildTasks:
    def test_single_preset_single_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[1])
        orch = BatchOrchestrator(config)
        assert len(orch.tasks) == 1
        assert orch.tasks[0].count_index == 0
        assert orch.tasks[0].preset_ref.preset_path == "p.yaml"

    def test_single_preset_multiple_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        orch = BatchOrchestrator(config)
        assert len(orch.tasks) == 3
        for i, task in enumerate(orch.tasks):
            assert task.count_index == i
            assert task.preset_ref.preset_path == "p.yaml"

    def test_multiple_presets(self):
        config = _make_config(
            preset_paths=["p1.yaml", "p2.yaml"],
            counts=[2, 3],
        )
        orch = BatchOrchestrator(config)
        assert len(orch.tasks) == 5
        # First 2 from p1
        for i in range(2):
            assert orch.tasks[i].preset_ref.preset_path == "p1.yaml"
            assert orch.tasks[i].count_index == i
        # Next 3 from p2
        for i in range(3):
            assert orch.tasks[i + 2].preset_ref.preset_path == "p2.yaml"
            assert orch.tasks[i + 2].count_index == i

    def test_no_timing(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        orch = BatchOrchestrator(config)
        for task in orch.tasks:
            assert task.timing_offset == 0.0

    def test_delay_timing(self):
        config = _make_config(
            preset_paths=["p.yaml"],
            counts=[3],
            timing=TimingConfig(delay_seconds=10.0),
        )
        orch = BatchOrchestrator(config)
        for task in orch.tasks:
            assert task.timing_offset == 10.0

    def test_stagger_timing(self):
        config = _make_config(
            preset_paths=["p.yaml"],
            counts=[4],
            timing=TimingConfig(delay_seconds=12.0, stagger_percent=100.0),
        )
        orch = BatchOrchestrator(config)
        # stagger_range = 12.0, stagger_step = 12.0 / 3 = 4.0
        expected_offsets = [0.0, 4.0, 8.0, 12.0]
        for i, task in enumerate(orch.tasks):
            assert task.timing_offset == pytest.approx(expected_offsets[i])

    def test_stagger_single_task(self):
        """Stagger should not apply to a single task, but delay still does."""
        config = _make_config(
            preset_paths=["p.yaml"],
            counts=[1],
            timing=TimingConfig(delay_seconds=10.0, stagger_percent=100.0),
        )
        orch = BatchOrchestrator(config)
        # Delay applies, stagger does not (only 1 task)
        assert orch.tasks[0].timing_offset == 10.0


# ── BatchOrchestrator._update_status ─────────────────────────────────────────

class TestUpdateStatus:
    def test_update_to_launched(self):
        orch = BatchOrchestrator(_make_config())
        task = orch.tasks[0] if orch.tasks else LaunchTask(
            preset_ref=BatchPresetRef("p.yaml"), count_index=0, timing_offset=0.0
        )
        orch._update_status(task, "launched", "inst-1")
        assert task.status == "launched"
        assert task.instance_id == "inst-1"
        assert task.started_at > 0

    def test_update_to_failed(self):
        orch = BatchOrchestrator(_make_config())
        task = orch.tasks[0] if orch.tasks else LaunchTask(
            preset_ref=BatchPresetRef("p.yaml"), count_index=0, timing_offset=0.0
        )
        orch._update_status(task, "failed", "", "connection error")
        assert task.status == "failed"
        assert task.error == "connection error"
        assert task.stopped_at > 0


# ── BatchOrchestrator._get_batch_status ──────────────────────────────────────

class TestGetBatchStatus:
    def test_all_pending(self):
        orch = BatchOrchestrator(_make_config())
        assert orch._get_batch_status() == "running"

    def test_all_completed(self):
        orch = BatchOrchestrator(_make_config())
        for task in orch.tasks:
            task.status = "completed"
        assert orch._get_batch_status() == "completed"

    def test_mixed_statuses(self):
        config = _make_config(preset_paths=["p1.yaml", "p2.yaml"], counts=[1, 1])
        orch = BatchOrchestrator(config)
        orch.tasks[0].status = "completed"
        orch.tasks[1].status = "failed"
        assert orch._get_batch_status() == "failed"

    def test_no_tasks(self):
        orch = BatchOrchestrator(_make_config(preset_paths=[], counts=[]))
        assert orch._get_batch_status() == "completed"


# ── BatchOrchestrator.launch (dry_run) ───────────────────────────────────────

class TestLaunchDryRun:
    def test_launch_single(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[1])
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.batch_name == "test-batch"
        assert result.total_instances == 1
        assert result.launched == 1
        assert result.failed == 0
        assert result.elapsed_seconds > 0

    def test_launch_multiple(self):
        config = _make_config(preset_paths=["p1.yaml", "p2.yaml"], counts=[2, 3])
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.total_instances == 5
        assert result.launched == 5
        assert result.failed == 0

    def test_launch_with_concurrency(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[10], concurrency=5)
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.total_instances == 10
        assert result.launched == 10

    def test_launch_with_timing(self):
        config = _make_config(
            preset_paths=["p.yaml"],
            counts=[2],
            timing=TimingConfig(delay_seconds=0.01, stagger_percent=100.0),
        )
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.total_instances == 2
        assert result.launched == 2

    def test_launch_empty_batch(self):
        config = _make_config(preset_paths=[], counts=[])
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.total_instances == 0
        assert result.launched == 0

    def test_launch_preserves_task_states(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[2])
        orch = BatchOrchestrator(config, dry_run=True)
        asyncio.run(orch.launch())

        for task in orch.tasks:
            assert task.status == "completed"
            assert task.instance_id != ""


# ── BatchOrchestrator.launch (with state persistence) ────────────────────────

class TestLaunchWithState:
    def test_save_and_load_state(self, tmp_path):
        config = _make_config(preset_paths=["p.yaml"], counts=[2])
        state_file = str(tmp_path / "batch_state.json")
        orch = BatchOrchestrator(config, dry_run=True, state_path=state_file)

        asyncio.run(orch.launch())

        # Check state was saved
        assert Path(state_file).exists()
        data = json.loads(Path(state_file).read_text())
        assert data["batch_name"] == "test-batch"
        assert len(data["instances"]) == 2

    def test_resume_partial_batch(self, tmp_path):
        """Test resuming a batch from saved state."""
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        state_file = str(tmp_path / "batch_state.json")

        # First launch - complete all
        orch1 = BatchOrchestrator(config, dry_run=True, state_path=state_file)
        asyncio.run(orch1.launch())

        # Second launch - should see all completed
        orch2 = BatchOrchestrator(config, dry_run=True, state_path=state_file)
        result = asyncio.run(orch2.launch())

        assert result.total_instances == 3
        assert result.launched == 3


# ── BatchOrchestrator helper methods ─────────────────────────────────────────

class TestOrchestratorHelpers:
    def test_get_task_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[5])
        orch = BatchOrchestrator(config)
        assert orch.get_task_count() == 5

    def test_get_pending_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        orch = BatchOrchestrator(config)
        assert orch.get_pending_count() == 3

    def test_get_completed_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        orch = BatchOrchestrator(config)
        assert orch.get_completed_count() == 0

        for task in orch.tasks:
            task.status = "completed"
        assert orch.get_completed_count() == 3

    def test_get_failed_count(self):
        config = _make_config(preset_paths=["p.yaml"], counts=[3])
        orch = BatchOrchestrator(config)
        assert orch.get_failed_count() == 0

        orch.tasks[0].status = "failed"
        assert orch.get_failed_count() == 1

    def test_get_result_before_launch(self):
        config = _make_config()
        orch = BatchOrchestrator(config)
        assert orch.get_result() is None

    def test_get_result_after_launch(self):
        config = _make_config()
        orch = BatchOrchestrator(config, dry_run=True)
        asyncio.run(orch.launch())
        result = orch.get_result()
        assert result is not None
        assert result.total_instances == 1


# ── BatchState serialization ─────────────────────────────────────────────────

class TestBatchStateSerialization:
    def test_save_and_load(self, tmp_path):
        state = BatchState(
            batch_name="test",
            source_path="test.yaml",
            presets=[{"preset_path": "p.yaml", "count": 1}],
            timing={"delay_seconds": 10.0, "stagger_percent": 50.0},
            concurrency=2,
            timeout=300,
            instances=[
                InstanceState(
                    instance_id="inst-1",
                    preset_path="p.yaml",
                    count_index=0,
                    status="completed",
                )
            ],
            started_at=1000.0,
            completed_at=1010.0,
            status="completed",
        )

        path = tmp_path / "state.json"
        save_batch_state(state, path)
        loaded = load_batch_state(path)

        assert loaded.batch_name == state.batch_name
        assert loaded.source_path == state.source_path
        assert loaded.concurrency == state.concurrency
        assert loaded.timeout == state.timeout
        assert len(loaded.instances) == 1
        assert loaded.instances[0].instance_id == "inst-1"
        assert loaded.instances[0].status == "completed"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_batch_state(tmp_path / "nonexistent.json")

    def test_save_creates_parent_dirs(self, tmp_path):
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


# ── Integration: full batch flow ─────────────────────────────────────────────

class TestFullBatchFlow:
    def test_full_dry_run_batch(self):
        """Test a complete batch launch flow in dry-run mode."""
        config = _make_config(
            preset_paths=["p1.yaml", "p2.yaml"],
            counts=[2, 1],
            timing=TimingConfig(delay_seconds=0.01, stagger_percent=100.0),
            concurrency=2,
        )

        status_updates = []

        def on_status(preset_path, count_index, status, instance_id="", error=""):
            status_updates.append((preset_path, count_index, status))

        orch = BatchOrchestrator(
            config,
            dry_run=True,
            on_instance_status=on_status,
        )

        result = asyncio.run(orch.launch())

        assert result.total_instances == 3
        assert result.launched == 3
        assert result.failed == 0
        assert len(status_updates) > 0

        # Check that all tasks are completed
        for task in orch.tasks:
            assert task.status == "completed"

    def test_batch_with_callback(self):
        """Test that status callbacks are invoked."""
        config = _make_config(preset_paths=["p.yaml"], counts=[1])
        callback = MagicMock()

        orch = BatchOrchestrator(config, dry_run=True, on_instance_status=callback)
        asyncio.run(orch.launch())

        # Callback should have been called for status updates
        assert callback.call_count > 0

    def test_batch_result_accuracy(self):
        """Test that batch result counts are accurate."""
        config = _make_config(preset_paths=["p.yaml"], counts=[5])
        orch = BatchOrchestrator(config, dry_run=True)
        result = asyncio.run(orch.launch())

        assert result.total_instances == 5
        assert result.launched == 5
        assert result.failed == 0
        assert result.stopped == 0
        assert result.skipped == 0
        assert result.elapsed_seconds > 0
