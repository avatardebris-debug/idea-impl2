# Phase 2 Tasks

- [x] Task 1: Analytics Engine — Trend Analysis Module
  - What: Create the analytics engine module with trend analysis capabilities. Add rolling average calculation and sales spike/drop detection per book. Add database query methods to fetch time-series sales data grouped by book.
  - Files: Create `manuscriptdata_analyzer/analytics.py` (new module with `TrendAnalyzer` class and DB query helpers), add new DB query methods to `manuscriptdata_analyzer/database.py` (e.g. `get_sales_trend_data()`, `get_book_sales_series()`)
  - Done when: `TrendAnalyzer` class calculates 3-day and 7-day rolling averages on sales data, detects spikes (>20% above rolling average) and drops (>20% below rolling average) per book, DB provides per-book daily sales series, and unit tests in `tests/test_analytics.py` pass with fixture data

- [x] Task 2: Multi-Book Comparison Engine
  - What: Build the comparison engine that ranks books by total revenue, total units sold, and reader engagement (avg rating from demographics). Add DB query methods to aggregate sales and demographics per book.
  - Files: Add comparison methods to `manuscriptdata_analyzer/analytics.py` (e.g. `BookComparator` class), add DB query methods to `manuscriptdata_analyzer/database.py` (e.g. `get_book_ranking()`, `get_book_engagement()`)
  - Done when: `BookComparator` ranks books by revenue, units sold, and engagement score, DB returns aggregated per-book stats and engagement metrics, and unit tests verify ranking correctness with fixture data

- [x] Task 3: Demographic Profiler
  - What: Build the demographic profiler that generates detailed age/gender/country breakdowns with percentage distributions, cross-tabulations (e.g. age × gender), and top-performing segments.
  - Files: Add demographic profiler to `manuscriptdata_analyzer/analytics.py` (e.g. `DemographicProfiler` class), add DB query methods to `manuscriptdata_analyzer/database.py` (e.g. `get_demographic_cross_tab()`, `get_top_demographic_segments()`)
  - Done when: `DemographicProfiler` produces age, gender, and country breakdowns with percentages, supports cross-tabulation (age × gender), identifies top-performing demographic segments by rating, and unit tests verify output accuracy

- [x] Task 4: Report Generator — Text Reports and CSV Export
  - What: Build the report generator that produces formatted text reports (combining trend, comparison, and demographic data) and CSV exports of analytics results.
  - Files: Add report generator to `manuscriptdata_analyzer/analytics.py` (e.g. `ReportGenerator` class with `generate_text_report()` and `export_csv()` methods)
  - Done when: `ReportGenerator.generate_text_report()` produces a formatted multi-section text report with trend analysis, book rankings, and demographic breakdowns, `export_csv()` writes analytics data to a CSV file, and unit tests verify output formatting and CSV content

- [x] Task 5: CLI Commands — `analyze` and `compare`
  - What: Add two new CLI commands. `analyze` runs the full analytics pipeline (trend + comparison + demographics) and outputs a comprehensive performance report (to stdout or file). `compare` outputs a side-by-side book comparison table.
  - Files: Modify `manuscriptdata_analyzer/cli.py` to add `analyze` and `compare` commands, update `manuscriptdata_analyzer/__main__.py` if needed
  - Done when: `manuscriptdata-analyzer analyze --db <path> [--output report.txt]` outputs a formatted performance report, `manuscriptdata-analyzer compare --db <path> [--books Book A,Book B]` outputs a side-by-side comparison table, both commands exit 0 on success, and CLI tests verify output content

- [x] Task 6: Unit Tests for Analytics Engine
  - What: Write comprehensive unit tests for all analytics components: trend analysis, book comparison, demographic profiler, and report generator. Use existing fixture CSV files and create any additional test fixtures needed.
  - Files: Create `tests/test_analytics.py` (new test file with test fixtures if needed), add CLI tests to `tests/test_cli.py` for `analyze` and `compare` commands
  - Done when: All analytics unit tests pass (trend detection, spike/drop identification, book ranking, demographic breakdowns, report formatting, CSV export), CLI tests for `analyze` and `compare` commands pass, and `pytest` runs clean with no failures