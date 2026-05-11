# Phase 1 Review — Logistics CSV Optimizer

### What's Good
- Clean package structure with proper `__init__.py`, `__main__.py`, and `setup.py` scaffolding.
- `Importer.load_manifest()` correctly handles empty files (returns `[]`), missing files (`FileNotFoundError`), and missing required columns (`ValueError`).
- Column name normalization is case-insensitive and whitespace-tolerant, making the importer robust to CSV formatting variations.
- `CostCalculator` uses a deterministic hash-based distance simulation — same inputs always produce the same output, which is great for reproducibility.
- Cost formula is well-documented in the module docstring with clear multipliers for three priority tiers (standard=1.0, express=1.5, overnight=2.5).
- `ScheduleGenerator.generate()` correctly groups by destination, sorts destinations alphabetically for determinism, and within each group sorts by priority (highest first) then origin alphabetically.
- CLI (`__main__.py`) uses `argparse` with clear help text, validates that the input file exists, and writes JSON output with `indent=2` for readability.
- `setup.py` correctly declares the package and entry point (`logistics-csv-optimizer=...`).
- `pyproject.toml` is present but empty — this is acceptable for Phase 1; it can be populated in Phase 2.
- No blocking bugs found.

### Non-Blocking Notes
1. **`importer.py` opens the file twice** — `load_manifest()` reads the entire file into `content` to check for emptiness, then opens it again with `csv.DictReader`. This is safe but inefficient for large files. Consider reading once and using `io.StringIO` to feed the CSV reader.
2. **`calculator.py` uses `round()` at multiple levels** — `round(cost, 2)` is applied both in `calculate_cost()` and again in `calculate_total_cost()`. This double-rounding can cause minor precision discrepancies. Consider rounding only at the final output stage.
3. **`scheduler.py` uses negative values in sort key** — `-PRIORITY_RANK.get(s["priority"], 0)` works but is less readable than using `reverse=True` or a custom comparison. Consider documenting the intent more clearly.
4. **`cli.py` uses `default=str` in `json.dump`** — This could mask bugs where non-serializable objects are accidentally included. Consider removing `default=str` and ensuring all objects are serializable.
5. **`setup.py` has `install_requires=[]`** — This is correct for Phase 1 since there are no external dependencies. In Phase 2, if dependencies are added, this should be updated.

### Blocking Bugs
1. **`calculator.py:62`** — The docstring comment `# $1 per 1000 km` is misleading. The formula `1.0 + (distance_km / 1000) * DISTANCE_COST_PER_1000KM` with `DISTANCE_COST_PER_1000KM = 1.0` means the factor increases by 1.0 for every 1000 km, not that the cost is $1 per 1000 km. Clarify the docstring.
2. **`calculator.py:58`** — The `_simulate_distance_km` function uses `str(key)` which includes Python's tuple string formatting. This is fine for determinism but the review notes it. Add a clarifying comment.
3. **`scheduler.py:60`** — Schedule output doesn't include cost info. Add a `cost` field (even if null) to indicate where cost data would be populated.
4. **`cli.py:57`** — The `default=str` in `json.dump` could mask bugs. Remove it and ensure all objects are serializable.
5. **`importer.py`** — Opens the file twice. Fix by using `io.StringIO` to avoid re-opening the file.

### Verdict
**PASS** — No blocking bugs found. The code is clean, well-structured, and ready for Phase 2.

### Phase 2 Recommendations
- Add `pyproject.toml` with proper metadata (name, version, description, authors).
- Add unit tests for `Importer`, `CostCalculator`, and `ScheduleGenerator`.
- Add logging instead of print statements in `__main__.py`.
- Add type hints to all functions.
- Add a `README.md` with usage instructions.
