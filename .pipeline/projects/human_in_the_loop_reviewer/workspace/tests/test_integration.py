"""Integration / smoke tests for the Human-in-the-Loop Reviewer."""

import threading
import time

import pytest

from human_in_the_loop_reviewer import Checkpoint, HumanInLoopReviewer


class TestIntegration:
    """End-to-end integration tests mirroring the demo scenarios."""

    def test_full_approve_flow(self):
        """Full approve flow matching the demo script behavior."""
        reviewer = HumanInLoopReviewer()

        # 1. Create a checkpoint
        cp_id = reviewer.create_checkpoint(
            review_request="Please review this draft proposal.",
            metadata={"author": "agent-42", "priority": "high"},
        )
        assert isinstance(cp_id, str)
        assert len(cp_id) > 0

        # 2. Simulate a human approving in a separate thread
        result_holder = {}
        error_holder = {}

        def human_action():
            time.sleep(0.3)  # pretend the human takes a moment
            reviewer.approve(cp_id)

        t = threading.Thread(target=human_action, daemon=True)
        t.start()

        # 3. Wait for the response (blocks until approve)
        result = reviewer.wait_for_response(cp_id, timeout=5)
        assert result.status == "approved"
        assert result.review_request == "Please review this draft proposal."
        assert result.metadata["author"] == "agent-42"
        assert result.metadata["priority"] == "high"

        t.join(timeout=5)
        assert "error" not in error_holder

    def test_full_reject_flow(self):
        """Full reject flow: checkpoint is created, rejected, and waiter gets rejected status."""
        reviewer = HumanInLoopReviewer()

        cp_id = reviewer.create_checkpoint(
            review_request="Review this design mockup.",
            metadata={"designer": "alice"},
        )

        result_holder = {}
        error_holder = {}

        def human_action():
            time.sleep(0.3)
            reviewer.reject(cp_id, reason="Colors don't match brand guidelines")

        t = threading.Thread(target=human_action, daemon=True)
        t.start()

        result = reviewer.wait_for_response(cp_id, timeout=5)
        assert result.status == "rejected"
        assert result.review_request == "Review this design mockup."

        t.join(timeout=5)
        assert "error" not in error_holder

    def test_multi_checkpoint_independent_workflows(self):
        """Multiple independent checkpoints should not interfere with each other."""
        reviewer = HumanInLoopReviewer()

        cp1_id = reviewer.create_checkpoint(
            review_request="Approve this one.",
            metadata={"workflow": "A"},
        )
        cp2_id = reviewer.create_checkpoint(
            review_request="Reject this one.",
            metadata={"workflow": "B"},
        )
        cp3_id = reviewer.create_checkpoint(
            review_request="Wait for timeout.",
            metadata={"workflow": "C"},
        )

        results = {}
        errors = {}

        def waiter(cp_id, key, timeout_val=30.0):
            try:
                result = reviewer.wait_for_response(cp_id, timeout=timeout_val)
                results[key] = result.status
            except Exception as e:
                errors[key] = str(e)

        # Start all three waiters
        t1 = threading.Thread(target=waiter, args=(cp1_id, "A"))
        t2 = threading.Thread(target=waiter, args=(cp2_id, "B"))
        t3 = threading.Thread(target=waiter, args=(cp3_id, "C", 0.5))
        t1.start()
        t2.start()
        t3.start()

        time.sleep(0.3)  # Let all waiters start

        # Approve checkpoint A
        reviewer.approve(cp1_id)
        # Reject checkpoint B
        reviewer.reject(cp2_id, reason="Needs revision")
        # Do nothing to checkpoint C — it should timeout

        t1.join(timeout=5)
        t2.join(timeout=5)
        t3.join(timeout=5)

        # Verify results
        assert "A" in results, f"Workflow A did not complete. Errors: {errors}"
        assert "B" in results, f"Workflow B did not complete. Errors: {errors}"
        assert "C" in errors, f"Workflow C should have timed out. Results: {results}"
        assert "C" not in results

        assert results["A"] == "approved"
        assert results["B"] == "rejected"

        # Verify checkpoint C timed out
        assert "Timed out" in errors["C"]

        # Verify all three checkpoints exist in store
        all_checkpoints = reviewer._store.list_all()
        assert len(all_checkpoints) == 3
