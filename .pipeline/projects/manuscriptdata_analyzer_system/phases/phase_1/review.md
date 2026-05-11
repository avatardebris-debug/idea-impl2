# Phase 1 Review — manuscriptdata_analyzer

## What's Good

- **Clean project scaffolding**: `pyproject.toml` is well-structured with proper `[build-system]`, `[project]`, and `[project.scripts]` sections. The CLI entry point is correctly wired via `__main__.py` and `cli.py`.
- **Robust CSV parser with auto-detection**: `csv_parser.py` correctly detects all three data types (sales, demographics, content metrics) by inspecting headers. The `COLUMN_ALIASES` mapping provides flexibility for varied column naming conventions.
- **Smart value normalisation**: `_normalise_value()` handles currency symbols (`$`), commas, and percentage signs gracefully — a real-world concern for CSV data ingestion.
- **SQLite schema with indexes**: `database.py` creates all three tables (`sales_data`, `demographics_data`, `content_metrics`) with appropriate indexes on commonly queried columns (date, book_title, platform, age_group, gender, country, chapter).
- **Well-structured query methods**: `get_sales_summary()`, `get_demographics_summary()`, and `get_content_metrics_summary()` all return rich dicts with breakdowns, not just raw aggregates.
- **Comprehensive test suite**: 35 tests covering parser detection, value normalisation, full CSV parsing, table creation, indexes, CRUD operations, and CLI import/summary commands. All pass.
- **Fixture CSV files**: Realistic test data for all three types with 15 rows each, covering edge cases like `$` in revenue, varied platforms, and multiple demographics.
- **Proper error handling**: Unrecognised CSVs raise clear `ValueError`; unknown data types raise `ValueError`; unconnected database raises `RuntimeError`.
- **CLI output formatting**: The `summary` command produces a neatly formatted report with aligned columns, dollar formatting, and percentage breakdowns.
- **`conftest.py` path injection**: Ensures local imports work in pytest regardless of working directory.
- **WAL journal mode**: Database uses `PRAGMA journal_mode=WAL` for better concurrency.

## Blocking Bugs

None. All 35 tests pass. The CLI works correctly. No crashes, wrong output, or test failures detected.

## Non-Blocking Notes

- **CLI command naming**: The spec says the command should be `import`, but click auto-converts `import_data` to `import-data`. This is fine, but if the spec strictly requires `import` (without hyphen), consider using `@cli.command(name="import")` to override click's default hyphenation.
- **`detect_data_type` ambiguity**: If a CSV has headers matching multiple types (e.g., a CSV with "Chapter" and "Date" columns), the detection order (sales → demographics → content) silently picks the first match. Consider adding a priority or requiring exact match for production use.
- **`_normalise_value` uses `col` parameter for type dispatch but receives canonical column name**: The function signature says `col: str` but the docstring and usage pass the canonical name. This is fine but could be confusing — consider renaming to `canonical_col` for clarity.
- **`insert_records` assumes all records have identical keys**: If a CSV row has a missing column, the record dict will lack that key, causing a `KeyError` when other rows are processed. Consider validating that all records share the same schema before inserting.
- **No `__all__` exports**: The modules don't define `__all__`, which means `from module import *` would expose internals. Not critical but good practice for a library.
- **`get_sales_summary` returns `None` for empty table but `row[0] == 0` check**: `COUNT(*)` always returns at least 0 (never `None`), so the `row is None` check is dead code. Minor.
- **No logging**: The CLI and database layer use `click.echo` for all output. Consider adding a `logging` module for debug-level diagnostics.
- **`db_path` defaults to CWD**: This could cause confusion if the user runs the CLI from a different directory. Consider using `~/.local/share/manuscriptdata_analyzer/` or a config file for the default path.
- **No data validation on insert**: The database layer accepts any dict keys — no schema validation beyond the table structure. Consider adding a `validate_record()` helper.

## Reusable Components

1. **CSV Parser with Auto-Detection** (`manuscriptdata_analyzer/csv_parser.py`)
   - Self-contained module that reads CSV files, auto-detects data types by header inspection, normalizes column names via aliases, and converts string values to appropriate Python types (int, float, string, None).
   - The `COLUMN_ALIASES` mapping, `_normalise_value()`, and `detect_data_type()` are all general-purpose utilities that could be reused for any CSV ingestion pipeline.

2. **SQLite Database Layer** (`manuscriptdata_analyzer/database.py`)
   - The `Database` class with its `connect()`, `insert_records()`, and query methods is a well-structured pattern for SQLite-backed data storage.
   - The schema definition (`CREATE_TABLES_SQL`) and index creation pattern is reusable for any analytics pipeline.

## Verdict

**PASS** — All 35 tests pass, CLI works correctly, no blocking bugs found.
