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

4. **Threading model**: Reuse the existing `MockDataSource` pattern — a background thread generates metric updates at a configurable interv