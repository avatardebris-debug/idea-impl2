# Phase 1 Review — Financial Document Analyzer

### What's Good
- Clean package structure with proper `__init__.py` exposing the public API (`parse_csv`, `parse_pdf`, `generate_report`).
- `core.py` contains well-designed, self-contained utility functions (`_safe_divide`, `_normalize_key`, `_extract_numeric`, `build_metrics_dict`) that handle edge cases like zero denominators, parenthetical negatives, and currency symbols.
- `parsers.py` correctly handles both standard and transposed CSV layouts with a reasonable heuristic for auto-detection.
- Column name mapping in `parsers.py` is comprehensive — covers many common financial column name variants (e.g., "net sales", "turnover", "ebit", "bottom line").
- `parsers.py` gracefully falls back to computing `gross_profit = revenue - cogs` when the gross profit column is missing but revenue and COGS are present.
- `parse_pdf` uses `pdfplumber` (a robust PDF table extraction library) and handles empty rows, header detection, and column normalization.
- `reporters.py` provides clean currency formatting with B/M/K suffixes and a useful `_trend_indicator` helper for period-over-period comparison.
- `generate_report` supports optional `previous_metrics` for trend comparison, making it useful for multi-period analysis.
- `cli.py` has a well-structured argparse interface with `--file` and `--previous` flags, proper error handling with `sys.exit(1)` on failures, and correct exit code 0 on success.
- `conftest.py` correctly injects the workspace path into `sys.path` for pytest compatibility.
- `requirements.txt` lists the expected dependencies (pandas, tabula-py, reportlab).

## Blocking Bugs
- **parsers.py:149** — `parse_pdf` uses `df.applymap()` which was deprecated in pandas 2.1.0 and removed in pandas 2.1.0+; it will raise `AttributeError: 'DataFrame' object has no attribute 'applymap'`. Should use `df.map()` instead.
- **parsers.py:150** — Same issue: `df.applymap()` is removed in pandas 2.1+. This will cause a crash when parsing PDFs with any pandas version >= 2.1.0.

## Non-Blocking Notes
- `requirements.txt` lists `tabula-py` and `reportlab` but the code actually uses `pdfplumber` for PDF parsing. Either the requirements should be updated to include `pdfplumber` (and remove unused deps), or the code should use `tabula-py` as originally intended.
- `parsers.py` defines `_find_column` with exact-then-partial matching, but the partial match logic (`if key in norm`) could produce false positives for short keys like "ebit" matching "revenue" if not careful. The current implementation avoids this by checking exact match first, but a more robust approach would use word-boundary matching.
- `parsers.py` has duplicated `_first_nonzero` function defined inside both the transposed and standard CSV branches. This could be extracted to a module-level helper to reduce duplication.
- `reporters.py` — `_trend_indicator` returns `"— 0.0%"` when `pct_change == 0` but `"—"` when `previous == 0`. The inconsistent use of the em-dash (with/without percentage) could confuse users.
- `cli.py` — The `--previous` flag prints a warning to stderr but continues execution. This is reasonable behavior, but the warning message could be more informative about what was skipped.
- No type hints on `parse_csv`, `parse_pdf`, or `main` functions (minor — the internal helpers are well-typed).
- The `_extract_numeric` function strips parentheses twice (once for the general case, once for the parenthetical negative case), which is redundant but harmless.

## Reusable Components
- **`core.py`** — Contains `_safe_divide`, `_normalize_key`, `_extract_numeric`, and `build_metrics_dict`. These are general-purpose utilities: safe division, string normalization, numeric extraction from formatted strings (handles currency symbols, commas, parenthetical negatives), and a reusable metrics dict builder. Self-contained and project-agnostic.
- **`reporters.py`** — Contains `_format_currency` (general-purpose currency formatting with B/M/K suffixes) and `_trend_indicator` (general-purpose percentage change trend indicator). Both are self-contained and reusable.

## Verdict
FAIL — `parse_pdf` will crash on pandas >= 2.1.0 due to use of removed `DataFrame.applymap()` method.
