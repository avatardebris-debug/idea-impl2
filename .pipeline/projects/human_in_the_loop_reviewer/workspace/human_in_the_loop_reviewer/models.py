"""Core data models for the Human-in-the-Loop Reviewer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class Checkpoint:
    """Represents a manual review checkpoint.

    Attributes:
        id: Unique identifier for the checkpoint.
        review_request: The request/prompt sent for human review.
        status: Current status — 'pending', 'approved', or 'rejected'.
        created_at: Timestamp when the checkpoint was created.
        metadata: Optional arbitrary metadata dict.
    """

    review_request: str
    status: str = "pending"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
