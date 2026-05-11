# Phase 1 Tasks

- [x] Task 1: Create project structure and core data models
  - What: Define the `Checkpoint` dataclass with fields for id, review_request, status (pending/approved/rejected), created_at, and metadata. Set up the Python package layout.
  - Files: `human_in_the_loop_reviewer/__init__.py`, `human_in_the_loop_reviewer/models.py`
  - Done when: `from human_in_the_loop_reviewer.models import Checkpoint` works; Checkpoint has all required fields and a sensible default status of "pending".

- [x] Task 2: Build the in-memory checkpoint store
  - What: Implement `CheckpointStore` class that manages a dictionary of checkpoints keyed by UUID. Supports create, get, update, and list operations. Thread-safe via threading.Lock.
  - Files: `human_in_the_loop_reviewer/store.py`
  - Done when: `CheckpointStore` can create a checkpoint, retrieve it by ID, update its status, and list all checkpoints. Basic unit-style smoke test passes (e.g., create → get → update → verify).

- [x] Task 3: Implement the HumanInLoopReviewer engine
  - What: Core `HumanInLoopReviewer` class that wraps `CheckpointStore`. Provides methods: `create_checkpoint(review_request, metadata)` to pause and record a request, `wait_for_response(checkpoint_id, timeout=None)` that blocks until the checkpoint is approved or rejected, `approve(checkpoint_id)` and `reject(checkpoint_id, reason)` to change checkpoint status.
  - Files: `human_in_the_loop_reviewer/reviewer.py`
  - Done when: `HumanInLoopReviewer` can create a checkpoint, block on `wait_for_response` in one thread, and unblock via `approve`/`reject` called from another thread. Timeout raises a `TimeoutError`.

- [x] Task 4: Wire the public API and package entry point
  - What: Expose all public classes and functions from `__init__.py`. Ensure clean import paths: `from human_in_the_loop_reviewer import HumanInLoopReviewer, Checkpoint`.
  - Files: `human_in_the_loop_reviewer/__init__.py`
  - Done when: `from human_in_the_loop_reviewer import HumanInLoopReviewer, Checkpoint` works without errors. All public classes are accessible at the top level.

- [x] Task 5: Create a basic demo script
  - What: Write `examples/basic_demo.py` that demonstrates the full flow: create a checkpoint, simulate a human approving it, and show the result.
  - Files: `examples/basic_demo.py`
  - Done when: `python examples/basic_demo.py` runs end-to-end without errors and prints a clear success message showing the checkpoint was created, approved, and the result was retrieved.