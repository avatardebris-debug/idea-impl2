"""Core HumanInLoopReviewer engine."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from .exceptions import InvalidCheckpointError, InvalidStatusError
from .models import Checkpoint
from .store import CheckpointStore


class HumanInLoopReviewer:
    """Wraps a CheckpointStore and provides blocking wait-for-response semantics.

    Typical usage:
        reviewer = HumanInLoopReviewer()
        cp_id = reviewer.create_checkpoint("Review this draft")
        # In another thread, a human calls reviewer.approve(cp_id)
        result = reviewer.wait_for_response(cp_id)
    """

    def __init__(self, store: Optional[CheckpointStore] = None) -> None:
        self._store = store if store is not None else CheckpointStore()
        # One Condition per checkpoint to allow targeted wake-ups.
        self._conditions: Dict[str, threading.Condition] = {}
        self._lock = threading.Lock()

    # -- helpers --

    def _get_condition(self, checkpoint_id: str) -> threading.Condition:
        with self._lock:
            if checkpoint_id not in self._conditions:
                self._conditions[checkpoint_id] = threading.Condition(threading.Lock())
            return self._conditions[checkpoint_id]

    # -- public API --

    def create_checkpoint(self, review_request: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new checkpoint and return its id.

        Raises:
            InvalidCheckpointError: If review_request is invalid.
        """
        cp = Checkpoint(review_request=review_request, metadata=metadata)
        self._store.create(cp)
        with self._lock:
            self._conditions[cp.id] = threading.Condition(threading.Lock())
        return cp.id

    def wait_for_response(self, checkpoint_id: str, timeout: float = 30.0) -> Checkpoint:
        """Block until the checkpoint is approved or rejected.

        Raises:
            ValueError: If checkpoint_id does not exist.
            TimeoutError: If the timeout expires before a response.
        """
        cp = self._store.get(checkpoint_id)
        if cp is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found")

        condition = self._get_condition(checkpoint_id)
        start_time = time.monotonic()
        with condition:
            while cp.status == "pending":
                remaining = timeout - (time.monotonic() - start_time)
                if remaining <= 0:
                    raise TimeoutError(f"Timed out waiting for response on checkpoint {checkpoint_id}")
                condition.wait(timeout=remaining)
                # Re-fetch in case the store was updated
                cp = self._store.get(checkpoint_id)
                if cp is None:
                    raise ValueError(f"Checkpoint '{checkpoint_id}' was deleted while waiting")
        return cp

    def approve(self, checkpoint_id: str) -> bool:
        """Approve a checkpoint.

        Raises:
            InvalidCheckpointError: If checkpoint_id is invalid.
        """
        if not checkpoint_id or not isinstance(checkpoint_id, str):
            raise InvalidCheckpointError("checkpoint_id must be a non-empty string", checkpoint_id=checkpoint_id)

        cp = self._store.get(checkpoint_id)
        if cp is None:
            return False

        condition = self._get_condition(checkpoint_id)
        with condition:
            self._store.update_status(checkpoint_id, "approved")
            condition.notify_all()
        return True

    def reject(self, checkpoint_id: str, reason: str = "") -> bool:
        """Reject a checkpoint.

        Raises:
            InvalidCheckpointError: If checkpoint_id is invalid.
        """
        if not checkpoint_id or not isinstance(checkpoint_id, str):
            raise InvalidCheckpointError("checkpoint_id must be a non-empty string", checkpoint_id=checkpoint_id)

        cp = self._store.get(checkpoint_id)
        if cp is None:
            return False

        condition = self._get_condition(checkpoint_id)
        with condition:
            self._store.update_status(checkpoint_id, "rejected")
            condition.notify_all()
        return True

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieve a checkpoint by id."""
        return self._store.get(checkpoint_id)

    def list_checkpoints(self) -> list:
        """List all checkpoints."""
        return self._store.list_all()
