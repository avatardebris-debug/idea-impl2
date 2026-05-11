# Validation Report — Phase 2
## Summary
- Tests: 51 passed, 14 failed
## Verdict: FAIL

### Failed Tests (14)
1. `tests/test_manuscriptdata_analyzer.py::TestDatabase::test_get_sales_summary` — assert 985 == 995 (numeric mismatch)
2. `tests/test_manuscriptdata_analyzer.py::TestDatabase::test_get_book_engagement` — assertion mismatch on engagement data
3. `tests/test_manuscriptdata_analyzer.py::TestCSVIngestor::test_detect_sales` — ValueError: Unrecognised CSV format
4. `tests/test_manuscriptdata_analyzer.py::TestCSVIngestor::test_detect_demographics` — ValueError: Unrecognised CSV format
5. `tests/test_manuscriptdata_analyzer.py::TestCSVIngestor::test_detect_content_metrics` — ValueError: Unrecognised CSV format
6. `tests/test_manuscriptdata_analyzer.py::TestTrendAnalyzer::test_analyze_book` — KeyError: 'book_title'
7. `tests/test_manuscriptdata_analyzer.py::TestTrendAnalyzer::test_analyze_all_books` — KeyError: 'book_title'
8. `tests/test_manuscriptdata_analyzer.py::TestBookComparator::test_compare_books` — assertion mismatch on comparison keys
9. `tests/test_manuscriptdata_analyzer.py::TestReportGenerator::test_export_csv` — assertion mismatch on CSV content
10. `tests/test_manuscriptdata_analyzer.py::TestRunFullAnalysis::test_run_full_analysis` — KeyError: 'book_title'
11. `tests/test_manuscriptdata_analyzer.py::TestCLI::test_import_data_command` — exit code 1 (expected 0)
12. `tests/test_manuscriptdata_analyzer.py::TestCLI::test_analyze_command` — exit code 1 (expected 0)
13. `tests/test_manuscriptdata_analyzer.py::TestCLI::test_compare_command` — exit code 1 (expected 0)
14. `tests/test_manuscriptdata_analyzer.py::TestCLI::test_trends_command` — exit code 1 (expected 0)

### Key Issues
- **KeyError: 'book_title'** in analytics.py (line 198) — the TrendAnalyzer and related code accesses `book_title` key but the data structure uses different keys
- **CSV detection failures** — CSVIngestor cannot recognize standard CSV formats (sales, demographics, content_metrics)
- **Numeric mismatches** — expected vs actual values differ (e.g., 985 vs 995)
- **CLI commands** — `analyze` and `compare` commands fail with exit code 1 instead of 0
- **Missing dedicated test file** — `tests/test_analytics.py` does not exist; all analytics tests are in `tests/test_manuscriptdata_analyzer.py`

### Required Files Status
- `manuscriptdata_analyzer/analytics.py` — PRESENT
- `manuscriptdata_analyzer/database.py` — PRESENT
- `manuscriptdata_analyzer/cli.py` — PRESENT
- `tests/test_analytics.py` — MISSING
- `tests/test_cli.py` — PRESENT (but CLI tests for analyze/compare fail)

### Root Cause
The analytics engine code has structural bugs: incorrect key access patterns, CSV format detection issues, and CLI command implementations that do not properly integrate with the analytics pipeline. These bugs cause 14 test failures across trend analysis, book comparison, report generation, and CLI command functionality.
