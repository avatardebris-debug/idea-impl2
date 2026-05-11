"""In-memory thread-safe checkpoint store."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from .exceptions import InvalidCheckpointError, InvalidStatusError
from .models import Checkpoint


class CheckpointStore:
    """Manages a dictionary of Checkpoints keyed by UUID.

    All public methods are thread-safe via an internal threading.Lock.
    """

    VALID_STATUSES = ("pending", "approved", "rejected")

    def __init__(self) -> None:
        self._store: Dict[str, Checkpoint] = {}
        self._lock = threading.Lock()

    # -- helpers --

    @staticmethod
    def _validate_review_request(review_request: object) -> str:
        """Validate that review_request is a non-empty string."""
        if not isinstance(review_request, str):
            raise InvalidCheckpointError(
                f"review_request must be a string, got {type(review_request).__name__}"
            )
        if not review_request.strip():
            raise InvalidCheckpointError("review_request must be a non-empty string")
        return review_request

    @staticmethod
    def _validate_status(status: object) -> str:
        """Validate that status is a valid status string."""
        if not isinstance(status, str):
            raise InvalidStatusError(
                f"status must be a string, got {type(status).__name__}",
                new_status=str(status),
            )
        if status not in CheckpointStore.VALID_STATUSES:
            raise InvalidStatusError(
                f"Invalid status '{status}'. Must be one of {CheckpointStore.VALID_STATUSES}",
                new_status=status,
            )
        return status

    # -- public API --

    def create(self, checkpoint: Checkpoint) -> str:
        """Store a checkpoint and return its id.

        Raises:
            InvalidCheckpointError: If checkpoint.review_request is invalid.
        """
        self._validate_review_request(checkpoint.review_request)
        with self._lock:
            self._store[checkpoint.id] = checkpoint
        return checkpoint.id

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieve a checkpoint by id, or None if not found."""
        with self._lock:
            return self._store.get(checkpoint_id)

    def update_status(self, checkpoint_id: str, status: str) -> bool:
        """Update the status of an existing checkpoint.

        Raises:
            InvalidStatusError: If status is invalid or transition is not allowed.

        Returns True if the checkpoint was found and updated, False otherwise.
        """
        self._validate_status(status)
        with self._lock:
            cp = self._store.get(checkpoint_id)
            if cp is None:
                return False
            # Prevent reverting to 'pending' from approved/rejected
            if status == "pending" and cp.status in ("approved", "rejected"):
                raise InvalidStatusError(
                    f"Cannot revert checkpoint from '{cp.status}' to 'pending'",
                    current_status=cp.status,
                    new_status=status,
                )
            cp.status = status
            return True

    def list_all(self) -> List[Checkpoint]:
        """Return a snapshot list of all checkpoints."""
        with self._lock:
            return list(self._store.values())