"""Integration tests for the CLI module.

Tests CLI commands (create, status, list, approve, reject, wait) by invoking
the CLI as a subprocess, verifying return codes and output.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the workspace is on sys.path so the package is importable
_ws = Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))


def _run_cli(*args: str, state_file: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess and return the result.

    Args:
        *args: CLI arguments.
        state_file: Optional path to a temporary state file.

    Returns:
        CompletedProcess with stdout, stderr, and returncode.
    """
    cmd = [sys.executable, "-m", "human_in_the_loop_reviewer"] + list(args)

    env = None
    if state_file is not None:
        env = dict(__import__("os").environ)
        env["HUMAN_IN_THE_LOOP_STATE"] = str(state_file)

    return subprocess.run(cmd, capture_output=True, text=True, env=env)


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    """Provide a temporary state file for each test."""
    return tmp_path / "test_state.json"


class TestCreateCommand:
    """Tests for the 'create' CLI command."""

    def test_create_success(self, state_file: Path) -> None:
        """Happy path: create a checkpoint returns an ID."""
        result = _run_cli("create", "Review this draft", state_file=state_file)
        assert result.returncode == 0
        assert "Checkpoint created" in result.stdout
        # Extract ID from output
        checkpoint_id = result.stdout.strip().split(": ")[1]
        assert len(checkpoint_id) > 0

    def test_create_empty_review_request(self, state_file: Path) -> None:
        """Creating with empty review_request fails."""
        result = _run_cli("create", "", state_file=state_file)
        assert result.returncode != 0
        assert "non-empty" in result.stderr.lower()

    def test_create_whitespace_only_review_request(self, state_file: Path) -> None:
        """Creating with whitespace-only review_request fails."""
        result = _run_cli("create", "   ", state_file=state_file)
        assert result.returncode != 0
        assert "non-empty" in result.stderr.lower()

    def test_create_no_args(self, state_file: Path) -> None:
        """Creating without review_request argument fails."""
        result = _run_cli("create", state_file=state_file)
        assert result.returncode != 0


class TestStatusCommand:
    """Tests for the 'status' CLI command."""

    def test_status_existing_checkpoint(self, state_file: Path) -> None:
        """Status of an existing checkpoint is displayed."""
        create_result = _run_cli("create", "Test checkpoint", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        status_result = _run_cli("status", checkpoint_id, state_file=state_file)
        assert status_result.returncode == 0
        assert "pending" in status_result.stdout.lower()

    def test_status_missing_checkpoint(self, state_file: Path) -> None:
        """Status of a non-existent checkpoint returns error."""
        result = _run_cli("status", "nonexistent-id-12345", state_file=state_file)
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestListCommand:
    """Tests for the 'list' CLI command."""

    def test_list_empty(self, state_file: Path) -> None:
        """List with no checkpoints shows empty."""
        result = _run_cli("list", state_file=state_file)
        assert result.returncode == 0
        assert "No checkpoints" in result.stdout or result.stdout.strip() == ""

    def test_list_with_checkpoints(self, state_file: Path) -> None:
        """List shows all checkpoints."""
        _run_cli("create", "First checkpoint", state_file=state_file)
        _run_cli("create", "Second checkpoint", state_file=state_file)

        result = _run_cli("list", state_file=state_file)
        assert result.returncode == 0
        assert "First checkpoint" in result.stdout
        assert "Second checkpoint" in result.stdout


class TestApproveCommand:
    """Tests for the 'approve' CLI command."""

    def test_approve_success(self, state_file: Path) -> None:
        """Approving a checkpoint updates its status."""
        create_result = _run_cli("create", "Approve me", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        approve_result = _run_cli("approve", checkpoint_id, state_file=state_file)
        assert approve_result.returncode == 0
        assert "approved" in approve_result.stdout.lower()

        # Verify status
        status_result = _run_cli("status", checkpoint_id, state_file=state_file)
        assert "approved" in status_result.stdout.lower()

    def test_approve_missing_checkpoint(self, state_file: Path) -> None:
        """Approving a non-existent checkpoint returns error."""
        result = _run_cli("approve", "nonexistent-id-12345", state_file=state_file)
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestRejectCommand:
    """Tests for the 'reject' CLI command."""

    def test_reject_success(self, state_file: Path) -> None:
        """Rejecting a checkpoint updates its status."""
        create_result = _run_cli("create", "Reject me", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        reject_result = _run_cli("reject", checkpoint_id, state_file=state_file)
        assert reject_result.returncode == 0
        assert "rejected" in reject_result.stdout.lower()

        # Verify status
        status_result = _run_cli("status", checkpoint_id, state_file=state_file)
        assert "rejected" in status_result.stdout.lower()

    def test_reject_with_reason(self, state_file: Path) -> None:
        """Rejecting with a reason includes it in output."""
        create_result = _run_cli("create", "Reject with reason", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        reject_result = _run_cli(
            "reject", checkpoint_id, "--reason", "Content is incomplete", state_file=state_file
        )
        assert reject_result.returncode == 0
        assert "incomplete" in reject_result.stdout.lower()

    def test_reject_missing_checkpoint(self, state_file: Path) -> None:
        """Rejecting a non-existent checkpoint returns error."""
        result = _run_cli("reject", "nonexistent-id-12345", state_file=state_file)
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestWaitCommand:
    """Tests for the 'wait' CLI command."""

    def test_wait_timeout(self, state_file: Path) -> None:
        """Waiting with a short timeout times out."""
        create_result = _run_cli("create", "Wait test", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        result = _run_cli("wait", checkpoint_id, "--timeout", "0.1", state_file=state_file)
        assert result.returncode != 0
        assert "timeout" in result.stderr.lower() or "timed out" in result.stdout.lower()

    def test_wait_approved(self, state_file: Path) -> None:
        """Waiting returns approved status when checkpoint is approved."""
        create_result = _run_cli("create", "Wait for approval", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        # Approve in a separate thread
        import threading

        def approve():
            import time

            time.sleep(0.2)
            _run_cli("approve", checkpoint_id, state_file=state_file)

        thread = threading.Thread(target=approve)
        thread.start()

        result = _run_cli("wait", checkpoint_id, "--timeout", "5", state_file=state_file)
        thread.join(timeout=10)

        assert result.returncode == 0
        assert "approved" in result.stdout.lower()


class TestCLIStatePersistence:
    """Tests for state file persistence."""

    def test_state_file_created(self, state_file: Path) -> None:
        """State file is created after creating a checkpoint."""
        _run_cli("create", "Persist test", state_file=state_file)
        assert state_file.exists()
        with open(state_file) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_state_file_persists_across_commands(self, state_file: Path) -> None:
        """Checkpoints persist across separate CLI invocations."""
        create_result = _run_cli("create", "Persistent checkpoint", state_file=state_file)
        assert create_result.returncode == 0
        checkpoint_id = create_result.stdout.strip().split(": ")[1]

        # New invocation should see the checkpoint
        status_result = _run_cli("status", checkpoint_id, state_file=state_file)
        assert status_result.returncode == 0
        assert "pending" in status_result.stdout.lower()
