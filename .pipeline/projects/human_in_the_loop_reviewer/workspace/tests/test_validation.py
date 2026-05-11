"""Tests for input validation and custom exceptions."""

import pytest

from human_in_the_loop_reviewer import (
    Checkpoint,
    CheckpointStore,
    HumanInLoopReviewer,
    InvalidCheckpointError,
    InvalidStatusError,
)


class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_invalid_checkpoint_error_default(self):
        """InvalidCheckpointError with default message."""
        exc = InvalidCheckpointError()
        assert str(exc) == "Invalid checkpoint reference"
        assert exc.checkpoint_id == ""

    def test_invalid_checkpoint_error_with_id(self):
        """InvalidCheckpointError with checkpoint_id."""
        exc = InvalidCheckpointError("Bad ID", checkpoint_id="abc-123")
        assert "abc-123" in str(exc)
        assert exc.checkpoint_id == "abc-123"

    def test_invalid_status_error_default(self):
        """InvalidStatusError with default message."""
        exc = InvalidStatusError()
        assert "Invalid status transition" in str(exc)

    def test_invalid_status_error_with_details(self):
        """InvalidStatusError with current and new status."""
        exc = InvalidStatusError(
            "Cannot revert",
            current_status="approved",
            new_status="pending",
        )
        assert "approved" in str(exc)
        assert "pending" in str(exc)
        assert exc.current_status == "approved"
        assert exc.new_status == "pending"

    def test_invalid_status_error_valid_statuses(self):
        """VALID_STATUSES contains expected values."""
        assert InvalidStatusError.VALID_STATUSES == ("pending", "approved", "rejected")


class TestCheckpointStoreValidation:
    """Tests for CheckpointStore input validation."""

    def test_create_with_non_string_review_request_raises(self):
        """create raises InvalidCheckpointError for non-string review_request."""
        store = CheckpointStore()
        cp = Checkpoint(review_request=123)  # type: ignore
        with pytest.raises(InvalidCheckpointError, match="must be a string"):
            store.create(cp)

    def test_create_with_empty_review_request_raises(self):
        """create raises InvalidCheckpointError for empty review_request."""
        store = CheckpointStore()
        cp = Checkpoint(review_request="")
        with pytest.raises(InvalidCheckpointError, match="non-empty"):
            store.create(cp)

    def test_create_with_whitespace_only_review_request_raises(self):
        """create raises InvalidCheckpointError for whitespace-only review_request."""
        store = CheckpointStore()
        cp = Checkpoint(review_request="   ")
        with pytest.raises(InvalidCheckpointError, match="non-empty"):
            store.create(cp)

    def test_update_status_with_invalid_status_raises(self):
        """update_status raises InvalidStatusError for invalid status."""
        store = CheckpointStore()
        cp = Checkpoint(review_request="Valid request")
        store.create(cp)
        with pytest.raises(InvalidStatusError, match="Invalid status"):
            store.update_status(cp.id, "invalid_status")

    def test_update_status_with_non_string_status_raises(self):
        """update_status raises InvalidStatusError for non-string status."""
        store = CheckpointStore()
        cp = Checkpoint(review_request="Valid request")
        store.create(cp)
        with pytest.raises(InvalidStatusError, match="must be a string"):
            store.update_status(cp.id, 123)  # type: ignore

    def test_update_status_cannot_revert_to_pending(self):
        """update_status raises InvalidStatusError when reverting to pending."""
        store = CheckpointStore()
        cp = Checkpoint(review_request="Valid request")
        store.create(cp)
        store.update_status(cp.id, "approved")
        with pytest.raises(InvalidStatusError, match="Cannot revert"):
            store.update_status(cp.id, "pending")


class TestHumanInLoopReviewerValidation:
    """Tests for HumanInLoopReviewer input validation."""

    def setup_method(self):
        self.reviewer = HumanInLoopReviewer()

    def test_create_checkpoint_with_non_string_raises(self):
        """create_checkpoint raises InvalidCheckpointError for non-string review_request."""
        with pytest.raises(InvalidCheckpointError, match="must be a string"):
            self.reviewer.create_checkpoint(review_request=123)  # type: ignore

    def test_create_checkpoint_with_empty_string_raises(self):
        """create_checkpoint raises InvalidCheckpointError for empty review_request."""
        with pytest.raises(InvalidCheckpointError, match="non-empty"):
            self.reviewer.create_checkpoint(review_request="")

    def test_create_checkpoint_with_whitespace_only_raises(self):
        """create_checkpoint raises InvalidCheckpointError for whitespace-only review_request."""
        with pytest.raises(InvalidCheckpointError, match="non-empty"):
            self.reviewer.create_checkpoint(review_request="   ")

    def test_approve_with_empty_string_raises(self):
        """approve raises InvalidCheckpointError for empty string checkpoint_id."""
        with pytest.raises(InvalidCheckpointError, match="must be a non-empty string"):
            self.reviewer.approve("")

    def test_approve_with_non_string_raises(self):
        """approve raises InvalidCheckpointError for non-string checkpoint_id."""
        with pytest.raises(InvalidCheckpointError, match="must be a non-empty string"):
            self.reviewer.approve(123)  # type: ignore

    def test_reject_with_empty_string_raises(self):
        """reject raises InvalidCheckpointError for empty string checkpoint_id."""
        with pytest.raises(InvalidCheckpointError, match="must be a non-empty string"):
            self.reviewer.reject("")

    def test_reject_with_non_string_raises(self):
        """reject raises InvalidCheckpointError for non-string checkpoint_id."""
        with pytest.raises(InvalidCheckpointError, match="must be a non-empty string"):
            self.reviewer.reject(123)  # type: ignore

    def test_wait_for_response_with_missing_id_raises_value_error(self):
        """wait_for_response raises ValueError for non-existent checkpoint_id."""
        with pytest.raises(ValueError, match="not found"):
            self.reviewer.wait_for_response("nonexistent-id")

    def test_wait_for_response_with_non_string_raises_value_error(self):
        """wait_for_response raises ValueError for non-string checkpoint_id."""
        with pytest.raises(ValueError, match="not found"):
            self.reviewer.wait_for_response(123)  # type: ignore

    def test_approve_unknown_checkpoint_returns_false(self):
        """approve returns False for unknown checkpoint_id (not an exception)."""
        result = self.reviewer.approve("unknown-id-99999")
        assert result is False

    def test_reject_unknown_checkpoint_returns_false(self):
        """reject returns False for unknown checkpoint_id (not an exception)."""
        result = self.reviewer.reject("unknown-id-99999")
        assert result is False
