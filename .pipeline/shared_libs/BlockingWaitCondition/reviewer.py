"""Core HumanInLoopReviewer engine."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

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

    def __init__(self) -> None:
        self._store = CheckpointStore()
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
        """Create a new checkpoint and return its id."""
        cp = Checkpoint(review_request=review_request, metadata=metadata or {})
        self._store.create(cp)
        # Register a condition for this checkpoint
        with self._lock:
            self._conditions[cp.id] = threading.Condition(threading.Lock())
        return cp.id

    def wait_for_response(self, checkpoint_id: str, timeout: Optional[float] = None) -> Checkpoint:
        """Block until the checkpoint is approved or rejected.

        Raises:
            TimeoutError: If timeout expires before a response.
            ValueError: If checkpoint_id is not found.
        """
        cp = self._store.get(checkpoint_id)
        if cp is None:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        cond = self._get_condition(checkpoint_id)
        with cond:
            deadline = None if timeout is None else time.monotonic() + timeout
            while cp.status == "pending":
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError(f"Timed out waiting for response on checkpoint {checkpoint_id}")
                cond.wait(timeout=remaining)
                # Re-read from store in case another thread updated it
                cp = self._store.get(checkpoint_id)
                if cp is None:
                    raise ValueError(f"Checkpoint {checkpoint_id} disappeared")
            return cp

    def approve(self, checkpoint_id: str) -> bool:
        """Approve a checkpoint and unblock any waiters."""
        updated = self._store.update_status(checkpoint_id, "approved")
        if updated:
            cond = self._get_condition(checkpoint_id)
            with cond:
                cond.notify_all()
        return updated

    def reject(self, checkpoint_id: str, reason: str = "") -> bool:
        """Reject a checkpoint and unblock any waiters."""
        updated = self._store.update_status(checkpoint_id, "rejected")
        if updated:
            cond = self._get_condition(checkpoint_id)
            with cond:
                cond.notify_all()
        return updated
