## Phase 1: Dashboard Data Model & Real-Time Metric Pipeline

- **Description**: Build the data model that represents card game simulation metrics and wire it into the existing real-time ticker infrastructure. This phase creates the `DashboardDataSource` class that generates win rate, bankroll curve, and Nash equilibrium shift data as ticker streams, and the metric model classes that define the data schema.

- **Deliverable**: 
  - `src/dashboard/models.py` — Data classes: `WinRateMetric`, `BankrollCurvePoint`, `NashEquilibriumShift`, `DashboardState`
  - `src/dashboard/data_source.py` — `DashboardDataSource` class extending the `MockDataSource` pattern; generates metric updates on a configurable interval
  - `src/dashboard/tickers.py` — `DashboardTicker` class (extends `src.ticker.Ticker`) with metric-specific fields (e.g., `current_win_rate`, `bankroll_history`, `nash_distance`)
  - Unit tests in `tests/test_dashboard_data_source.py` and `tests/test_dashboard_models.py`
  - A standalone CLI demo script (`src/dashboard/demo_cli.py`) that prints metric updates to stdout

- **Dependencies**: None. Uses existing `src.ticker.Ticker` and the `MockDataSource` threading/update pattern from `src/data_source.py`.

- **Success criteria**:
  - `DashboardDataSource` produces at least 3 metric types (win rate, bankroll, Nash shift) as ticker updates at configurable intervals
  - All metric model classes serialize/deserialize via `to_dict()` / `from_dict()`
  - `DashboardTicker` carries all three metric types and exposes `price_color`-style visual hints (e.g., green for positive win rate, red for negative)
  - CLI demo prints 20 metric updates in real-time with correct formatting
  - All unit tests pass (≥ 15 test cases covering model creation, serialization, data source update loop, ticker color logic)

---