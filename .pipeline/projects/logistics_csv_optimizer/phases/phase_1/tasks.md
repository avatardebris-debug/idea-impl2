# Phase 1 Tasks

- [x] Task 1: Project scaffolding and package structure
  - What: Create the project directory layout, Python package, and dependency manifest for the Logistics CSV Optimizer.
  - Files: logistics_csv_optimizer/__init__.py, logistics_csv_optimizer/core.py, logistics_csv_optimizer/cli.py, setup.py, requirements.txt
  - Done when: Package can be installed via `pip install -e .` and `python -m logistics_csv_optimizer --help` prints usage without errors.

- [x] Task 2: CSV shipment manifest importer
  - What: Build a module that reads CSV shipment manifest files, parses rows into structured shipment objects (origin, destination, weight, dimensions, priority), and validates required fields.
  - Files: logistics_csv_optimizer/importer.py
  - Done when: `Importer.load_manifest("sample.csv")` returns a list of validated shipment dicts; missing required columns raise a clear ValueError; empty files return an empty list.

- [x] Task 3: Routing cost calculator
  - What: Implement cost calculation logic that takes a list of shipments and computes routing costs based on distance, weight, and priority tier (standard, express, overnight).
  - Files: logistics_csv_optimizer/calculator.py
  - Done when: `CostCalculator.calculate(shipments)` returns a dict with per-shipment costs and a total cost; cost formula is deterministic and documented; supports at least 3 priority tiers with different multipliers.

- [x] Task 4: Delivery schedule generator
  - What: Build a schedule optimizer that takes shipments and their calculated costs and produces an ordered delivery schedule sorted by priority and geographic grouping.
  - Files: logistics_csv_optimizer/scheduler.py
  - Done when: `ScheduleGenerator.generate(shipments)` returns a list of scheduled deliveries ordered by priority (highest first) with geographic grouping; output is deterministic given the same input.

- [x] Task 5: CLI integration and end-to-end workflow
  - What: Wire the importer, calculator, and scheduler together behind a CLI interface so a user can run a single command to import a CSV, compute costs, and output the optimized schedule.
  - Files: logistics_csv_optimizer/cli.py (updated), logistics_csv_optimizer/__main__.py
  - Done when: Running `python -m logistics_csv_optimizer --input sample_manifest.csv --output schedule.json` reads the CSV, calculates costs, generates the schedule, and writes a valid JSON output file; exit code is 0 on success and non-zero on failure.