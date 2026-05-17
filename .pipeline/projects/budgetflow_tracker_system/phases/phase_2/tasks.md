# Phase 2 Tasks

- [ ] Task 1: Time-bucketing engine
  - What: Build a `TimeBucketEngine` that groups transactions into configurable intervals (daily, weekly, monthly, quarterly). Handles irregular import dates by aligning to calendar boundaries. Produces a `TimeSeriesBucket` object containing the bucket date range, total income, total expenses, net flow, and transaction count.
  - Files:
    - Create `budgetflow_tracker/src/forecasting/time_bucket.py` — `TimeBucketEngine` class with `bucket_transactions()` method
    - Create `budgetflow_tracker/src/forecasting/models.py` — `TimeSeriesBucket` Pydantic model
    - Modify `budgetflow_tracker/src/forecasting/__init__.py` — expose public API
    - Create `budgetflow_tracker/tests/test_time_bucket.py` — unit tests with synthetic data
  - Done when: `TimeBucketEngine.bucket_transactions()` correctly groups a set of transactions with irregular dates into daily, weekly, and monthly buckets; tests verify bucket boundaries, totals, and count accuracy for all three interval types.

- [ ] Task 2: Forecasting models (Holt-Winters + linear regression)
  - What: Implement two forecasting models: (1) Holt-Winters exponential smoothing (additive or multiplicative seasonal component) for capturing trend + seasonality, (2) Ordinary least squares linear regression for trend-only forecasts. Each model must produce point forecasts and confidence intervals. Include a `ModelSelector` that evaluates both models on a training window and picks the one with the lowest RMSE on a held-out test window.
  - Files:
    - Create `budgetflow_tracker/src/forecasting/holt_winters.py` — `HoltWintersForecaster` class
    - Create `budgetflow_tracker/src/forecasting/linear_regression.py` — `LinearRegressionForecaster` class
    - Create `budgetflow_tracker/src/forecasting/model_selector.py` — `ModelSelector` class
    - Create `budgetflow_tracker/tests/test_forecasting_models.py` — backtest both models against synthetic time series with known trend + seasonality; verify RMSE < threshold
  - Done when: Both models produce forecasts with confidence intervals; `ModelSelector` correctly picks the better model on synthetic data with known seasonality (Holt-Winters) and without (linear regression); RMSE on backtested data is ≤15% of the mean value.

- [ ] Task 3: Pattern detection (recurring transactions + anomaly detection)
  - What: Implement two detection engines: (1) `RecurringPatternDetector` that identifies recurring transactions by grouping by merchant/description similarity, checking for regular intervals (with tolerance), and flagging subscriptions, rent, salary, etc. (2) `AnomalyDetector` that flags transactions whose amount deviates from the category's historical mean by more than N standard deviations (configurable, default 2σ) or whose amount is an outlier relative to the category's distribution.
  - Files:
    - Create `budgetflow_tracker/src/forecasting/pattern_detector.py` — `RecurringPatternDetector` class with `detect_recurring()` method
    - Create `budgetflow_tracker/src/forecasting/anomaly_detector.py` — `AnomalyDetector` class with `detect_anomalies()` method
    - Create `budgetflow_tracker/src/forecasting/models.py` — `RecurringPattern` and `AnomalyFlag` Pydantic models (append to existing file from Task 1)
    - Create `budgetflow_tracker/tests/test_pattern_detection.py` — tests with synthetic recurring patterns (e.g., $1,500 rent every 30 days) and injected anomalies (e.g., $5,000 charge in a $50 category)
  - Done when: Recurring detector identifies ≥90% of injected recurring patterns in 6+ months of synthetic data; anomaly detector flags ≥80% of injected anomalies; both engines handle edge cases (missing data, variable intervals within tolerance).

- [ ] Task 4: Cash flow projection engine
  - What: Build a `CashFlowProjectionEngine` that combines the time-bucketed data, selected forecasting models, and recurring pattern detections to produce forward-looking income/expenses for the next 30/60/90 days. For each category, it uses the best-performing model to project future values, overlays known recurring patterns (fixed amounts on known dates), and computes aggregate cash position with confidence intervals (using Monte Carlo or analytical variance propagation).
  - Files:
    - Create `budgetflow_tracker/src/forecasting/projection_engine.py` — `CashFlowProjectionEngine` class with `project()` method returning `CashFlowProjection` results
    - Create `budgetflow_tracker/src/forecasting/models.py` — `CashFlowProjection` and `CategoryProjection` Pydantic models (append to existing file)
    - Create `budgetflow_tracker/tests/test_projection_engine.py` — tests verifying projection accuracy against known synthetic data, confidence interval coverage, and correct handling of recurring patterns
  - Done when: Engine produces 30/60/90-day projections per category and aggregate; projections include upper/lower confidence bounds; recurring patterns are correctly overlaid on top of model forecasts; tests confirm projections are consistent with input data.

- [ ] Task 5: Visualization module
  - What: Implement a `ChartGenerator` that produces static chart images (PNG) using matplotlib (with plotly as optional backend for interactive HTML export). Charts to support: (1) Spending trends over time (line chart), (2) Category breakdown (pie or bar chart), (3) Forecast curves with actuals overlaid and confidence interval bands, (4) Cash position over time (area chart). All charts must be configurable for any 90-day window and exportable to PNG/HTML.
  - Files:
    - Create `budgetflow_tracker/src/forecasting/visualization.py` — `ChartGenerator` class with methods: `generate_trend_chart()`, `generate_category_chart()`, `generate_forecast_chart()`, `generate_cash_position_chart()`
    - Create `budgetflow_tracker/src/forecasting/models.py` — `ChartOutput` Pydantic model (append to existing file)
    - Create `budgetflow_tracker/tests/test_visualization.py` — tests verifying chart generation produces valid output files and correct data rendering
  - Done when: All four chart types generate valid PNG files; forecast charts correctly overlay actuals, forecasts, and confidence bands; charts are configurable for any 90-day window; HTML export works when plotly is available.

- [ ] Task 6: Forecast CLI report
  - What: Build a CLI command (`budgetflow forecast`) that generates a text-based cash flow report and optionally renders charts. The report shows: projected cash position for the next 30/60/90 days, key inflection points (where cash flow changes direction), top categories driving forecast changes, recurring transactions detected, and anomalies flagged. Supports `--charts` flag to generate and save chart files, and `--window 30|60|90` to control projection horizon.
  - Files:
    - Create `budgetflow_tracker/src/ui/cli_forecast.py` — `cli_forecast()` function with argparse integration
    - Modify `budgetflow_tracker/src/ui/cli.py` — add `forecast` subcommand to the CLI entry point
    - Create `budgetflow_tracker/tests/test_cli_forecast.py` — tests verifying CLI output format, chart file generation, and correct integration with projection engine
  - Done when: `budgetflow forecast` command runs end-to-end producing text report with projected cash position, inflection points, recurring patterns, and anomalies; `--charts` flag generates PNG chart files; `--window` flag correctly controls projection horizon; all CLI output is deterministic and testable.