# Phase 2 Tasks

- [x] Fix blocking bug: Test symbol case mismatch (test_layout.py already expects "WIN_RATE" and "BANKROLL" matching source; test_dashboard_panels.py fixed to use uppercase symbols)
- [x] Fix blocking bug: Missing imports in renderers.py (imports already present on line 22)
- [x] Review verdict: PASS — all blocking bugs resolved, all tests pass. No further changes needed.

- [x] Task 1: Build panel base class and WinRatePanel
  - What: Create the abstract panel base class that defines the panel interface (compatible with TickerPanel), then implement WinRatePanel as a gauge-style display showing current win rate, confidence interval, and trend arrow.
  - Files: `src/dashboard/panels.py` (create — contains `DashboardPanel` base class and `WinRatePanel`)
  - Done when: `DashboardPanel` defines `render_data()`, `get_visual_encoding()`, and `update(ticker)` methods; `WinRatePanel` exposes `gauge_value`, `confidence_interval`, and `trend_arrow` properties; panel can be instantiated with default and custom values; unit tests in `tests/test_dashboard_panels.py` cover WinRatePanel creation, update from ticker, gauge value computation, confidence interval calculation, and trend arrow logic (≥ 8 test cases).

- [x] Task 2: Build BankrollCurvePanel and NashEquilibriumPanel
  - What: Implement `BankrollCurvePanel` (mini sparkline/area chart showing bankroll over time with profit/loss shading) and `NashEquilibriumPanel` (heatmap-style display showing distance from Nash equilibrium per strategy dimension).
  - Files: `src/dashboard/panels.py` (extend — add `BankrollCurvePanel` and `NashEquilibriumPanel`)
  - Done when: `BankrollCurvePanel` exposes `sparkline_data` (list of bankroll values), `profit_loss_shading` (bool), and `area_points` (list of (x,y) tuples for area chart); `NashEquilibriumPanel` exposes `heatmap_grid` (2D list of color-coded cells), `distance_values` (list of distances), and `color_map` (mapping of distance ranges to colors); both panels implement the same `update(ticker)` interface; unit tests cover sparkline data generation, profit/loss shading logic, heatmap grid construction, and color mapping (≥ 8 test cases).

- [x] Task 3: Build DashboardBoard layout manager
  - What: Create `DashboardBoard` class that extends the (abstract) `TickerBoard` concept and auto-positions the three dashboard panels (`WinRatePanel`, `BankrollCurvePanel`, `NashEquilibriumPanel`) in a 3-column layout with configurable sizing.
  - Files: `src/dashboard/layout.py` (create)
  - Done when: `DashboardBoard` accepts three panel instances, computes 3-column positions (x, y, width, height) for each panel, supports configurable panel width/height/spacing via constructor args, exposes a `get_panel_positions()` method returning ordered list of position dicts, and `render_layout()` returns a dict of panel positions keyed by panel symbol; unit tests in `tests/test_dashboard_layout.py` cover board creation, default positioning, custom sizing, position calculation correctness, and panel registration (≥ 6 test cases).

- [x] Task 4: Build DashboardVizRenderer for VR scene output
  - What: Create `DashboardVizRenderer` that converts panel data into VR-renderable geometry objects (meshes, colors, transforms) compatible with the `src.vr_renderer` and `src.vr_scene` patterns.
  - Files: `src/dashboard/viz_renderer.py` (create)
  - Done when: `DashboardVizRenderer` accepts a `DashboardBoard` and produces a list of VR scene objects, each with `type` (e.g., "gauge", "sparkline", "heatmap"), `geometry` (vertices/positions), `color` (hex or rgba), and `transform` (position/rotation/scale); `render_panel(panel)` method produces valid VR objects per panel type; `render_all()` renders all panels in the board; unit tests cover renderer creation, per-panel VR object generation, geometry validity, color encoding, and full board rendering (≥ 6 test cases).

- [ ] Task 5: Integrate panels with DashboardTicker and run end-to-end
  - What: Wire the dashboard panels to the `DashboardTicker` so that updating a ticker updates the corresponding panel in real-time; add integration tests and ensure the full pipeline (DataSource → Ticker → Panels → Board → VizRenderer) works end-to-end.
  - Files: `tests/test_dashboard_panels.py` (extend with integration tests), `tests/test_dashboard_layout.py` (extend with integration tests), `src/dashboard/panels.py` (extend with `bind_ticker(ticker)` method on `DashboardPanel`), `src/dashboard/layout.py` (extend `DashboardBoard` with `bind_ticker`), `src/dashboard/viz_renderer.py` (extend with ticker-aware rendering)
  - Done when: `DashboardPanel.bind_ticker(ticker)` links a panel to a `DashboardTicker` so that `ticker.update()` triggers `panel.update()` automatically; `DashboardBoard.bind_ticker(ticker)` binds the ticker to all child panels; `DashboardVizRenderer` can render from a live ticker; integration tests verify ticker-to-panel binding, panel-to-board propagation, and viz renderer output from live data (≥ 6 integration test cases).
