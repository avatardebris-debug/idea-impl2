# Phase 2 Review — Financial Document Analyzer

### What's Good
- **Core utilities are well-designed**: `_safe_divide`, `_normalize_key`, `_extract_numeric`, and `build_metrics_dict` are clean, self-contained, and handle edge cases (zero denominator, None, currency symbols, parenthetical negatives, empty strings).
- **Comprehensive test coverage**: 56 tests across `test_core.py` and `test_parsers.py` covering normal inputs, edge cases, error handling, and output structure validation.
- **CSV parser handles both standard and transposed formats** with a reasonable heuristic for auto-detection.
- **Gross profit fallback** (revenue - cogs) is a smart default when the gross_profit column is missing.
- **PDF parser uses pdfplumber with graceful ImportError handling** — the module-level try/except prevents crashes when pdfplumber isn't installed.
- **Tests properly mock pdfplumber** using `unittest.mock.MagicMock`, avoiding real PDF dependency in CI.
- **Report generator** produces clean, readable text output with currency formatting (B/M/K suffixes), margin percentages, and trend indicators (▲/▼/—).
- **CLI has proper error handling**: file existence checks, unsupported file type rejection, and user-friendly error messages via `sys.stderr`.
- **Test helpers** (`_write_csv`, `_write_pdf`) are well-structured with try/finally cleanup.
- **Column name mapping** (`REVENUE_KEYS`, `COGS_KEYS`, etc.) is comprehensive and covers common financial terminology variations.
- **`_find_column` prioritizes exact matches over partial matches**, reducing false positives.
- **`__init__.py` exposes a clean public API** (`parse_csv`, `parse_pdf`, `generate_report`).

## Blocking Bugs
None

## Non-Blocking Notes
- **`_extract_numeric` handles `None` explicitly but `_safe_divide` doesn't guard against `None` denominator** — if `None` is passed as denominator, it will raise a `TypeError`. This is unlikely in practice since all callers pass floats, but worth noting.
- **`_trend_indicator` returns `"— 0.0%"` for zero change** — the dash and percentage are slightly inconsistent (other cases show `▲/▼` with no space before the dash). Consider `"— 0.0%"` → `"— 0.0%"` or `"0.0%"` for consistency.
- **`parse_csv` and `parse_pdf` both define `_first_nonzero` as a nested function** — this is duplicated code. Extracting it to a module-level helper would reduce duplication.
- **`parse_pdf` uses `df.map()` which is pandas 2.1+** — if older pandas versions are used, this will fail. Consider `df.applymap()` for backward compatibility or a version check.
- **`_format_currency` always uses `$` prefix** — the function strips other currency symbols in `_extract_numeric` but always formats with `$`. If multi-currency support is needed, this should be configurable.
- **`generate_report` hardcodes margin labels** — if new margins are added, they need to be manually added to `margin_labels` dict. Consider making this dynamic.
- **No validation that parsed metrics are reasonable** (e.g., gross_profit should typically be ≤ revenue). Consider adding sanity checks.
- **`parse_csv` transposed detection** relies on the first column containing year-like values — this could fail for non-standard layouts. Consider adding a confidence threshold or manual override.
- **`parse_pdf` only looks at the first page** (`pdf.pages[0]`) — multi-page financial statements would miss data. Consider iterating all pages or using a table-finding strategy.
- **`_find_column` uses `in` for partial matching** — this could match unintended columns (e.g., "Total Revenue" matching "Revenue" when "Total Revenue" is the actual target). Consider ranking by match quality.
- **`build_metrics_dict` accepts `**kwargs` for metrics** — this is flexible but could silently accept typos. Consider using a typed dataclass or Pydantic model for validation.
- **No logging** — errors and warnings go to stderr but there's no structured logging for debugging or monitoring.
- **`requirements.txt` pins no versions** — consider pinning versions for reproducibility (e.g., `pandas>=2.0,<3.0`).
