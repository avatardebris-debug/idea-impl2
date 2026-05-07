# Master Plan: Tableau Integration Module

## Goal
Add real-time data visualization dashboards to the card game simulator for tracking win rates, bankroll curves, and Nash equilibrium shifts. Leverages the existing `MockDataSource` → `Ticker` → `TickerPanel` → `TickerBoard` → VR rendering pipeline already in `src/`.

## Core Deliverable
A self-contained module (`src/dashboard/`) that produces card-game simulation metrics as real-time ticker streams, renders them as visual dashboard panels in the VR room, and connects them to an actual game engine backend.

---

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

## Phase 2: Dashboard Visualization Panels & VR Rendering

- **Description**: Build the visual dashboard components — specific panel types for each metric — and integrate them into the existing `TickerBoard` / VR rendering pipeline. This phase creates a `DashboardBoard` layout manager that arranges the three dashboard panels in the VR room.

- **Deliverable**:
  - `src/dashboard/panels.py` — Panel classes:
    - `WinRatePanel` (gauge-style display showing current win rate, confidence interval, and trend arrow)
    - `BankrollCurvePanel` (mini sparkline/area chart showing bankroll over time with profit/loss shading)
    - `NashEquilibriumPanel` (heatmap-style display showing distance from Nash equilibrium per strategy dimension)
  - `src/dashboard/layout.py` — `DashboardBoard` class (extends `TickerBoard`) that auto-positions the three panels in a 3-column layout
  - `src/dashboard/viz_renderer.py` — `DashboardVizRenderer` that converts panel data into VR-renderable geometry (using existing `src.vr_renderer` and `src.vr_scene`)
  - Integration of dashboard panels into the existing `TickerBoard` system (panels implement the same interface as `TickerPanel`)
  - Unit tests in `tests/test_dashboard_panels.py` and `tests/test_dashboard_layout.py`

- **Dependencies**: Phase 1 (DashboardDataSource, DashboardTicker, metric models)

- **Success criteria**:
  - All three panel types render correctly with metric-specific visual encodings (gauge, sparkline, heatmap)
  - `DashboardBoard` positions panels in a 3-column layout with configurable sizing
  - `DashboardVizRenderer` produces valid VR scene objects compatible with `src.vr_renderer.VRRenderer`
  - Panel-to-ticker binding works: updating a `DashboardTicker` updates the corresponding panel in real-time
  - All unit tests pass (≥ 20 test cases covering panel creation, layout calculation, renderer output, ticker-panel binding)

---

## Phase 3: Game Engine Integration & Interactive Controls

- **Description**: Connect the dashboard to an actual card game simulation backend, add interactive controls (filtering by game type, time window selection, pause/resume), and add export capabilities (PNG snapshots, CSV metric dumps).

- **Deliverable**:
  - `src/dashboard/game_bridge.py` — `GameBridge` class that plugs into the card game simulator (poker hold'em, blackjack, video poker) and feeds live game events into the `DashboardDataSource`
  - `src/dashboard/controls.py` — Interactive control layer:
    - Game type selector (hold'em, blackjack, stud, video poker)
    - Time window filter (last 100 hands, last 1000 hands, all-time)
    - Pause/resume real-time updates
    - Strategy comparison mode (show two strategies side-by-side)
  - `src/dashboard/export.py` — Export utilities:
    - `export_snapshot()` — renders current dashboard to PNG
    - `export_csv()` — dumps metric history to CSV
    - `export_json()` — dumps full dashboard state for persistence
  - `src/dashboard/demo_vr.py` — Full VR demo: launches the VR room with live game simulation feeding the dashboard
  - Integration tests in `tests/test_dashboard_integration.py`
  - Updated `requirements.txt` with any new dependencies (e.g., `Pillow` for PNG export, `matplotlib` for sparkline rendering)

- **Dependencies**: Phase 1 (data pipeline), Phase 2 (visualization panels)

- **Success criteria**:
  - `GameBridge` correctly translates game events (hand results, pot sizes, strategy outputs) into dashboard metric updates
  - Interactive controls filter and update the dashboard in real-time (< 200ms response time)
  - Strategy comparison mode renders two strategies simultaneously with distinct color coding
  - PNG snapshot captures all three panels at full resolution
  - CSV export produces valid, parseable output with correct column headers and timestamp ordering
  - Full VR demo runs end-to-end: game simulation → dashboard updates → VR rendering → user interaction
  - All integration tests pass (≥ 10 test cases covering game bridge, controls, export, and full pipeline)

---

## Architecture Notes

1. **Leverage existing infrastructure**: The project already has a mature real-time data pipeline (`MockDataSource` → `Ticker` → `TickerPanel` → `TickerBoard` → VR renderer). The dashboard module plugs into this exact pipeline by extending `Ticker` and `TickerPanel` with metric-specific fields.

2. **Module structure**: All new code lives under `src/dashboard/`. The module is self-contained and importable. It depends only on `src.ticker`, `src.data_source`, `src.panels`, `src.vr_renderer`, and `src.vr_scene` from the existing codebase.

3. **Data flow**: 
   ```
   Card Game Simulator → GameBridge → DashboardDataSource → DashboardTicker → DashboardPanel → DashboardVizRenderer → VR Scene
   ```

4. **Threading model**: Reuse the existing `MockDataSource` pattern — a background thread generates metric updates at a configurable interval, and the main thread reads them via thread-safe `get_tickers()` calls protected by `threading.Lock`.

5. **Metric computation**: 
   - Win rate: rolling window of (wins / total hands) with configurable window size
   - Bankroll curve: cumulative profit/loss per hand, stored as a list of (hand_index, bankroll) tuples
   - Nash equilibrium shift: distance metric (e.g., L2 norm) between current strategy profile and computed Nash equilibrium, updated after each hand

6. **No external Tableau dependency**: Despite the module name "Tableau Integration," this is a self-contained visualization module. If Tableau Desktop/Server connectivity is needed later, a separate export-to-TDE/FDE bridge can be added as a Phase 4 extension.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| **VR rendering complexity**: The existing VR renderer may not support custom chart geometries (sparklines, heatmaps). | Phase 2 includes a fallback: render panels as textured planes with canvas-drawn images instead of custom 3D geometry. |
| **Nash equilibrium computation cost**: Computing Nash equilibria in real-time during simulation is computationally expensive. | Use precomputed equilibrium tables for standard game types; compute shifts via perturbation analysis rather than full re-solution. Fall back to approximate Nash if computation exceeds threshold. |
| **Thread safety**: Multiple components reading/writing ticker state concurrently. | All shared state goes through `DashboardDataSource`'s lock-protected interface. Panels read snapshots, not live references. |
| **Scope creep**: Dashboard panels could become arbitrarily complex. | Strict scope: gauge, sparkline, heatmap only. No drill-down, no cross-filtering beyond time window. Export is PNG/CSV/JSON only. |
| **Existing codebase coupling**: Changes to `src.ticker` or `src.panels` could break the dashboard. | Dashboard extends (not modifies) existing classes. Write integration tests that verify backward compatibility with existing ticker/panel consumers. |
