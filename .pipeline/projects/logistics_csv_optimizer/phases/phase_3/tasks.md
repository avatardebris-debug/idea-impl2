# Phase 3 Tasks

- [x] Task 1: API Surface Extraction
  - What: Move the orchestration logic from `cli.py` into `api.py`.
  - Files:
    - `logistics_csv_optimizer/api.py`
    - `cli.py`

- [x] Task 2: CLI Standard I/O Support
  - What: Update `cli.py` to allow reading from `sys.stdin` and writing to `sys.stdout` when `-` is passed.
  - Files:
    - `cli.py`
    - `logistics_csv_optimizer/importer.py` (if necessary to support file objects instead of just paths)

- [x] Task 3: Containerization
  - What: Write a Dockerfile.
  - Files:
    - `Dockerfile`

- [x] Task 4: Documentation
  - What: Write comprehensive `README.md`.
  - Files:
    - `README.md`