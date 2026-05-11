# Human-in-the-Loop Reviewer

A Python library for managing manual review checkpoints with blocking wait-for-response semantics.

## Overview

This package provides a `HumanInLoopReviewer` engine that wraps a thread-safe `CheckpointStore`. It allows you to create review checkpoints, wait for a human to approve or reject them, and retrieve the results.

## Installation

```bash
pip install human_in_the_loop_reviewer
```

## Quick Start

```python
from human_in_the_loop_reviewer import HumanInLoopReviewer

reviewer = HumanInLoopReviewer()

# Create a checkpoint
cp_id = reviewer.create_checkpoint("Review this draft document")

# In another thread, a human approves or rejects:
# reviewer.approve(cp_id)  or  reviewer.reject(cp_id, reason="...")

# Wait for the response (blocks until approved/rejected or timeout)
result = reviewer.wait_for_response(cp_id, timeout=60.0)
print(result.status)  # 'approved' or 'rejected'
```

## Core Classes

- **`Checkpoint`** — Dataclass representing a manual review checkpoint with `id`, `review_request`, `status`, `created_at`, and `metadata`.
- **`CheckpointStore`** — Thread-safe in-memory store for checkpoints.
- **`HumanInLoopReviewer`** — Engine that wraps a `CheckpointStore` and provides blocking `wait_for_response` semantics with per-checkpoint condition variables.

## Exceptions

- **`InvalidCheckpointError`** — Raised when a checkpoint operation receives an invalid checkpoint reference.
- **`InvalidStatusError`** — Raised when an invalid status transition is attempted.

## Valid Statuses

- `pending` — Initial state when a checkpoint is created.
- `approved` — Human has approved the checkpoint.
- `rejected` — Human has rejected the checkpoint.

## Project Structure

```
human_in_the_loop_reviewer/
├── __init__.py      # Public API exports
├── models.py        # Checkpoint dataclass
├── store.py         # CheckpointStore (thread-safe)
├── reviewer.py      # HumanInLoopReviewer engine
└── exceptions.py    # Custom exceptions
tests/
├── test_store.py
├── test_reviewer.py
├── test_integration.py
└── test_validation.py
```
