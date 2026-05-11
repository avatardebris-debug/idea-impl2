# Phase 2 Tasks

- [ ] Task 1: Write unit tests for CheckpointStore
  - What: Create `tests/test_store.py` with tests for all CheckpointStore methods: create, get, update_status, list_all. Cover happy path, not-found cases, and thread-safety smoke test.
  - Files: `tests/test_store.py` (new)
  - Done when: All 6+ test cases pass with `pytest tests/test_store.py -v` — create, get existing, get missing, update existing, update missing, list_all, and a thread-safety concurrent update test.

- [ ] Task 2: Write unit tests for HumanInLoopReviewer
  - What: Create `tests/test_reviewer.py` with tests for the full reviewer lifecycle: create_checkpoint, wait_for_response (approve path, reject path, timeout path), approve, reject, and invalid checkpoint_id handling.
  - Files: `tests/test_reviewer.py` (new)
  - Done when: All 8+ test cases pass with `pytest tests/test_reviewer.py -v` — approve unblocks waiter, reject unblocks waiter with reason, timeout raises TimeoutError, wait_for_response raises ValueError for missing id, approve/reject return False for unknown id, multiple waiters all unblock on notify_all.

- [ ] Task 3: Write integration / smoke tests
  - What: Create `tests/test_integration.py` with end-to-end scenarios mirroring the demo: full approve flow, full reject flow, and a multi-checkpoint workflow.
  - Files: `tests/test_integration.py` (new)
  - Done when: All 3 integration tests pass with `pytest tests/test_integration.py -v` — approve flow matches demo, reject flow returns rejected status, multi-checkpoint flow handles independent checkpoints correctly.

- [ ] Task 4: Add error handling and input validation
  - What: Add input validation to `CheckpointStore` and `HumanInLoopReviewer`: validate that `review_request` is non-empty string, validate status transitions (e.g., cannot update a non-pending checkpoint to "pending"), add custom exception classes for domain errors.
  - Files: `human_in_the_loop_reviewer/models.py`, `human_in_the_loop_reviewer/store.py`, `human_in_the_loop_reviewer/reviewer.py` (modify)
  - Done when: Passing empty review_request raises `ValueError`, invalid status transition raises `ValueError`, custom exceptions `InvalidCheckpointError` and `InvalidStatusError` are importable from the package root, and corresponding tests in `tests/test_validation.py` pass.

- [x] Task 5: Write README and project documentation
  - What: Create a comprehensive `README.md` at the workspace root with: project overview, installation instructions, quick-start example, API reference (Checkpoint, CheckpointStore, HumanInLoopReviewer), usage patterns (approve/reject/timeout), threading notes, and a link to the test suite.
  - Files: `README.md` (new)
  - Done when: README covers all sections listed above, the quick-start example matches the demo script output, and a reader can set up and run the project from the README alone.