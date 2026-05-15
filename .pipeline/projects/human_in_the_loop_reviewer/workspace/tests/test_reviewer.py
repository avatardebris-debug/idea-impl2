"""Unit tests for HumanInLoopReviewer."""

import threading
import time

import pytest

from human_in_the_loop_reviewer import Checkpoint, HumanInLoopReviewer


class TestHumanInLoopReviewer:
    """Tests for the HumanInLoopReviewer class."""

    def setup_method(self):
        """Create a fresh reviewer for each test."""
        self.reviewer = HumanInLoopReviewer()

    def test_create_checkpoint_returns_id(self):
        """create_checkpoint returns a non-empty string id."""
        cp_id = self.reviewer.create_checkpoint("Test request")
        assert isinstance(cp_id, str)
        assert len(cp_id) > 0

    def test_approve_unblocks_waiter(self):
        """Approving a checkpoint unblocks the waiter with 'approved' status."""
        cp_id = self.reviewer.create_checkpoint("Approve me")
        result_holder = {}
        error_holder = {}

        def waiter():
            try:
                result = self.reviewer.wait_for_response(cp_id, timeout=5)
                result_holder["result"] = result
            except Exception as e:
                error_holder["error"] = e

        t = threading.Thread(target=waiter, daemon=True)
        t.start()

        # Give the waiter time to start waiting
        time.sleep(0.2)

        # Approve from main thread
        approved = self.reviewer.approve(cp_id)
        assert approved is True

        t.join(timeout=5)
        assert "error" not in error_holder
        assert "result" in result_holder
        assert result_holder["result"].status == "approved"

    def test_reject_unblocks_waiter_with_reason(self):
        """Rejecting a checkpoint unblocks the waiter with 'rejected' status."""
        cp_id = self.reviewer.create_checkpoint("Reject me")
        result_holder = {}
        error_holder = {}

        def waiter():
            try:
                result = self.reviewer.wait_for_response(cp_id, timeout=5)
                result_holder["result"] = result
            except Exception as e:
                error_holder["error"] = e

        t = threading.Thread(target=waiter, daemon=True)
        t.start()
        time.sleep(0.2)

        rejected = self.reviewer.reject(cp_id, reason="Not good enough")
        assert rejected is True

        t.join(timeout=5)
        assert "error" not in error_holder
        assert "result" in result_holder
        assert result_holder["result"].status == "rejected"

    def test_timeout_raises_timeout_error(self):
        """wait_for_response raises TimeoutError when timeout expires."""
        cp_id = self.reviewer.create_checkpoint("Timeout me")
        with pytest.raises(TimeoutError):
            self.reviewer.wait_for_response(cp_id, timeout=0.1)

    def test_wait_for_response_missing_id_raises_value_error(self):
        """wait_for_response raises ValueError for a non-existent checkpoint_id."""
        with pytest.raises(ValueError, match="not found"):
            self.reviewer.wait_for_response("nonexistent-id-12345")

    def test_approve_unknown_id_returns_false(self):
        """approve returns False for an unknown checkpoint_id."""
        result = self.reviewer.approve("unknown-id-99999")
        assert result is False

    def test_reject_unknown_id_returns_false(self):
        """reject returns False for an unknown checkpoint_id."""
        result = self.reviewer.reject("unknown-id-99999")
        assert result is False

    def test_multiple_waiters_all_unblock_on_notify_all(self):
        """Multiple waiters on the same checkpoint all unblock when approved."""
        cp_id = self.reviewer.create_checkpoint("Multi-waiter")
        results = []
        errors = []
        barrier = threading.Barrier(3)

        def waiter(idx):
            try:
                barrier.wait(timeout=5)
                result = self.reviewer.wait_for_response(cp_id, timeout=5)
                results.append((idx, result.status))
            except Exception as e:
                errors.append((idx, str(e)))

        threads = [threading.Thread(target=waiter, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()

        time.sleep(0.3)  # Let all waiters start
        self.reviewer.approve(cp_id)

        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        statuses = {r[1] for r in results}
        assert statuses == {"approved"}

    def test_wait_for_response_deleted_while_waiting(self):
        """wait_for_response raises ValueError if checkpoint is deleted while waiting."""
        cp_id = self.reviewer.create_checkpoint("Delete me")
        error_holder = {}

        def waiter():
            try:
                self.reviewer.wait_for_response(cp_id, timeout=5)
            except Exception as e:
                error_holder["error"] = e

        t = threading.Thread(target=waiter, daemon=True)
        t.start()
        time.sleep(0.2)

        # Delete the checkpoint directly from the store
        # First we have to trigger the condition to wake the waiter
        condition = self.reviewer._get_condition(cp_id)
        with condition:
            self.reviewer._store._store.pop(cp_id)
            condition.notify_all()

        t.join(timeout=5)
        assert "error" in error_holder
        assert isinstance(error_holder["error"], ValueError)
        assert "deleted while waiting" in str(error_holder["error"])

