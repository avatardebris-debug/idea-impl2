# Phase 3 Tasks

- [x] Task 1: Platform-Specific CSV Parsers & Detection
  - What: Extract parsing logic into a Strategy pattern. Implement auto-detection based on headers. Add mappers for KDP, Kobo, Apple, and B&N.
  - Files:
    - `manuscriptdata_analyzer/csv_parser.py` (Refactor to use a `PlatformParser` base class and specific implementations)

- [x] Task 2: Cross-Platform Analytics & JSON Export
  - What: Update the `ReportGenerator` and `TrendAnalyzer` to group by platform and provide total aggregations. Add JSON export capability.
  - Files:
    - `manuscriptdata_analyzer/analytics.py`
    - `manuscriptdata_analyzer/cli.py` (Add JSON support)

- [x] Task 3: Interactive CLI Dashboard
  - What: Create a persistent interactive loop (dashboard) for easier user experience.
  - Files:
    - `manuscriptdata_analyzer/dashboard.py` (New module)
    - `manuscriptdata_analyzer/cli.py` (Add `dashboard` command)

- [x] Task 4: Integration Testing & Final Polish
  - What: Add test cases simulating multi-platform data ingestion.
  - Files:
    - `tests/test_parsers.py`
    - `tests/test_integration.py`
