"""Unit tests for CheckpointStore."""

import threading
import time

import pytest

from human_in_the_loop_reviewer import Checkpoint, CheckpointStore


class TestCheckpointStore:
    """Tests for the CheckpointStore class."""

    def setup_method(self):
        """Create a fresh store for each test."""
        self.store = CheckpointStore()

    def test_create_and_get(self):
        """Happy path: create a checkpoint and retrieve it."""
        cp = Checkpoint(review_request="Test checkpoint")
        checkpoint_id = self.store.create(cp)
        assert checkpoint_id == cp.id

        retrieved = self.store.get(checkpoint_id)
        assert retrieved is not None
        assert retrieved.id == cp.id
        assert retrieved.review_request == "Test checkpoint"
        assert retrieved.status == "pending"

    def test_get_missing_checkpoint(self):
        """Getting a non-existent checkpoint returns None."""
        missing_id = "nonexistent-id-12345"
        result = self.store.get(missing_id)
        assert result is None

    def test_update_status_existing(self):
        """Updating status of an existing checkpoint works."""
        cp = Checkpoint(review_request="Update me")
        self.store.create(cp)

        updated = self.store.update_status(cp.id, "approved")
        assert updated is True

        retrieved = self.store.get(cp.id)
        assert retrieved.status == "approved"

    def test_update_status_missing(self):
        """Updating a non-existent checkpoint returns False."""
        updated = self.store.update_status("nonexistent-id-67890", "approved")
        assert updated is False

    def test_list_all_empty(self):
        """list_all returns empty list when store is empty."""
        all_checkpoints = self.store.list_all()
        assert all_checkpoints == []

    def test_list_all_with_checkpoints(self):
        """list_all returns all checkpoints."""
        cp1 = Checkpoint(review_request="First")
        cp2 = Checkpoint(review_request="Second")
        cp3 = Checkpoint(review_request="Third")
        self.store.create(cp1)
        self.store.create(cp2)
        self.store.create(cp3)

        all_checkpoints = self.store.list_all()
        assert len(all_checkpoints) == 3
        statuses = {cp.status for cp in all_checkpoints}
        assert statuses == {"pending"}

    def test_list_all_after_update(self):
        """list_all reflects status updates."""
        cp = Checkpoint(review_request="To update")
        self.store.create(cp)
        self.store.update_status(cp.id, "rejected")

        all_checkpoints = self.store.list_all()
        assert len(all_checkpoints) == 1
        assert all_checkpoints[0].status == "rejected"

    def test_thread_safety_concurrent_updates(self):
        """Concurrent updates from multiple threads should not corrupt state."""
        cp = Checkpoint(review_request="Concurrent test")
        self.store.create(cp)

        num_threads = 10
        results = []
        barrier = threading.Barrier(num_threads)

        def update_status():
            barrier.wait()
            for i in range(100):
                self.store.update_status(cp.id, "approved")
                results.append(True)

        threads = [threading.Thread(target=update_status) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # All updates should have completed without error
        assert len(results) == num_threads * 100

        # Final status should be consistent
        retrieved = self.store.get(cp.id)
        assert retrieved is not None
        assert retrieved.status == "approved"
