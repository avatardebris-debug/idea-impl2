# Phase 1 Tasks

- [x] Task 1: Create dashboard data model classes
  - What: Define the four metric model dataclasses in `src/dashboard/models.py` with to_dict/from_dict serialization. Classes: WinRateMetric, BankrollCurvePoint, NashEquilibriumShift, DashboardState.
  - Files: `src/dashboard/models.py` (create), `src/dashboard/__init__.py` (create)
  - Done when: All four dataclasses are defined with appropriate fields. Each has to_dict() and from_dict() methods. DashboardState aggregates all three metric types.

- [x] Task 2: Create DashboardTicker class extending src.ticker.Ticker
  - What: Build `src/dashboard/tickers.py` with a `DashboardTicker` class that extends `src.ticker.Ticker`. Adds metric-specific fields (current_win_rate, bankroll_history, nash_distance) and price_color-style visual hints (green for positive win rate, red for negative, white for neutral).
  - Files: `src/dashboard/tickers.py` (create)
  - Done when: DashboardTicker inherits from Ticker, carries all three metric types, has price_color logic based on win rate sign, and includes to_dict/from_dict for the dashboard-specific fields.

- [x] Task 3: Create DashboardDataSource class
  - What: Build `src/dashboard/data_source.py` with a `DashboardDataSource` class that extends `MockDataSource` pattern. Generates metric updates on a configurable interval producing at least 3 metric types (win rate, bankroll, Nash shift) as ticker updates.
  - Files: `src/dashboard/data_source.py` (create)
  - Done when: DashboardDataSource extends MockDataSource, produces 3 metric types per update cycle at configurable intervals, and has start/stop/force_update methods.

- [x] Task 4: Create CLI demo script
  - What: Build `src/dashboard/demo_cli.py` that instantiates DashboardDataSource, starts it, and prints 20 metric updates to stdout with correct formatting.
  - Files: `src/dashboard/demo_cli.py` (create)
  - Done when: Running `python src/dashboard/demo_cli.py` prints exactly 20 formatted metric updates in real-time with all three metric types visible per update.

- [x] Task 5: Write unit tests for dashboard models
  - What: Create `tests/test_dashboard_models.py` with tests for model creation, serialization round-trips, and DashboardState aggregation.
  - Files: `tests/test_dashboard_models.py` (create)
  - Done when: At least 8 test cases covering WinRateMetric, BankrollCurvePoint, NashEquilibriumShift, DashboardState creation and to_dict/from_dict round-trip serialization. All tests pass with `pytest tests/test_dashboard_models.py`.

- [x] Task 6: Write unit tests for DashboardDataSource and DashboardTicker
  - What: Create `tests/test_dashboard_data_source.py` with tests for data source update loop, ticker color logic, and metric generation.
  - Files: `tests/test_dashboard_data_source.py` (create)
  - Done when: At least 8 test cases covering data source creation, update loop, ticker color logic, and metric generation. All tests pass with `pytest tests/test_dashboard_data_source.py`. Combined with Task 5, total test cases >= 15.