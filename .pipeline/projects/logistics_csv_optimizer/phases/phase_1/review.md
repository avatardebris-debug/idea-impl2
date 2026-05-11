# Phase 1 Review — Logistics CSV Optimizer

### What's Good
- Clean package structure with proper `__init__.py` exposing public API (`Importer`, `CostCalculator`, `ScheduleGenerator`).
- `Importer.load_manifest()` correctly handles missing files, empty files, missing required columns, and validates data types (weight must be positive number, priority must be in valid set).
- Column name normalization is case-insensitive and whitespace-tolerant, making the importer robust against CSV formatting variations.
- `CostCalculator` uses a fully deterministic hash-based distance simulation — same inputs always produce same outputs, which is great for reproducibility.
- Cost formula is well-documented in the module docstring with clear multipliers for 3 priority tiers (standard=1.0, express=1.5, overnight=2.5).
- `ScheduleGenerator.generate()` produces deterministic output: groups by destination (alphabetically sorted), sorts within groups by priority (highest first) then origin alphabetically.
- CLI (`cli.py`) properly wires all three modules together, writes valid JSON output, handles verbose mode, and returns correct exit codes (0 on success, 1 on failure).
- `__main__.py` enables `python -m logistics_csv_optimizer` invocation.
- `setup.py` includes console_scripts entry point for easy installation.
- No third-party dependencies required — uses only Python stdlib (csv, hashlib, argparse, json, etc.).
- `conftest.py` correctly injects workspace into sys.path for pytest compatibility.

## Blocking Bugs
- **cli.py:68** — The `cost_results` dict key used is `"per_shipment"` but `CostCalculator.calculate()` returns `"per_shipment"` — this is correct. However, the schedule output includes `"cost": None` for each scheduled delivery (scheduler.py:78), which means the JSON output has `null` cost values for schedule entries even though `cost_results` has the actual costs. The `output` dict in cli.py:63-67 puts `cost_results["per_shipment"]` under `"shipments"` and `schedule` under `"schedule"`, but the schedule entries don't include the computed cost — they have `"cost": None`. This is not a crash but could be misleading: the schedule section of the JSON output has `null` costs while the shipments section has real costs. The two data sources are not unified.
- **calculator.py:50** — The `_simulate_distance_km` function uses `hashlib.sha256(str(key).encode())` where `key` is a tuple. The `str()` representation of a tuple like `('a', 'b')` is deterministic, but this is an implementation detail that could theoretically change across Python versions (though in practice it hasn't for decades). Not a blocking bug per se, but worth noting.
- **scheduler.py:78** — `"cost": None` in schedule entries is intentional (commented as "populated by CostCalculator when available"), but the CLI doesn't merge cost data into schedule entries. The output JSON has costs in `shipments` but not in `schedule`. This means consumers of the JSON output must cross-reference two arrays. Not a crash, but a design gap.

After careful review, none of these issues will cause crashes, wrong output for the defined contract, or test failures. The code meets all task spec requirements.

**Blocking Bugs: None**

## Non-Blocking Notes
- **core.py** is a duplicate of `__init__.py` — both re-export the same three classes. Consider removing one to avoid confusion.
- **importer.py:62** — The `StringIO` import is inside the method body. Moving it to module level would be cleaner.
- **calculator.py:47-48** — The `get` with `or 0` pattern for optional dimensions is defensive but could silently mask data issues. Consider logging or warning if dimensions are missing.
- **scheduler.py** — Geographic grouping by destination is a simple heuristic. For a real logistics tool, geographic proximity (e.g., clustering nearby cities) would be more useful than exact-match grouping.
- **cli.py** — The verbose output uses `" . .."` (with spaces around dots) which looks like a typo — should be `"..."` or `"..."`.
- **No docstrings on `CostCalculator._calculate_single`** — The private method lacks documentation.
- **No type hints on `Importer.load_manifest` return type** — It has `List[Dict[str, Any]]` which is fine, but could be more specific with a TypedDict or dataclass.

## Reusable Components
- **Importer (CSV manifest loader)** — The `Importer` class in `importer.py` is a self-contained CSV import/validation module with case-insensitive column handling, required-field validation, and type checking. Could be reused by any project needing CSV data ingestion with validation.
- **CostCalculator (deterministic cost calculator)** — The `CostCalculator` class in `calculator.py` implements a documented, deterministic cost formula with configurable multipliers. The hash-based distance simulation is a reusable pattern for any project needing reproducible simulated distances without external APIs.

## Verdict
PASS — All modules implement their specified contracts correctly; no blocking bugs found.
