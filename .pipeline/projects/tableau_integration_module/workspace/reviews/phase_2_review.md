# Phase 2 Code Review: Dashboard Module

## Executive Summary

Phase 2 delivers a well-structured dashboard module with clear separation of concerns across models, tickers, panels, layout, and rendering. The architecture is clean and the tests are comprehensive. However, there are several **critical issues** that need attention before merging:

1. **`renderers.py` has a missing import** (`WinRatePanel`, `BankrollCurvePanel`, `NashEquilibriumPanel` are used in `TableauDashboard.__post_init__` but not imported)
2. **`panels.py` has a mutable default argument bug** (`confidence_interval: tuple = (0.0, 1.0)`)
3. **`renderers.py` CSV rendering has a structural issue** — `render_panel` writes headers every time, which would produce duplicate headers if called multiple times
4. **`renderers.py` REST renderer has hardcoded URL construction** that may not work with all Tableau Server configurations
5. **`layout.py` grid layout is fragile** — panels are stored in a flat list but accessed via row-major indexing, which breaks if panels are removed from the middle

---

## 1. Critical Issues

### 1.1 Missing Imports in `renderers.py` (BLOCKER)

**File:** `src/dashboard/renderers.py`, line ~140

```python
@dataclass
class TableauDashboard:
    def __post_init__(self):
        if not self.panels:
            self.panels = [
                WinRatePanel(),
                BankrollCurvePanel(),
                NashEquilibriumPanel(),
            ]
```

`WinRatePanel`, `BankrollCurvePanel`, and `NashEquilibriumPanel` are used but **never imported**. This will raise `NameError` at instantiation time.

**Fix:**
```python
from src.dashboard.panels import (
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
```

### 1.2 Mutable Default Argument in `panels.py` (BUG)

**File:** `src/dashboard/panels.py`, line ~78

```python
@dataclass
class WinRatePanel(DashboardPanel):
    confidence_interval: tuple = (0.0, 1.0)  # BUG: mutable default
```

While tuples are immutable, the real issue is that `dataclass` with mutable defaults can cause unexpected sharing in some contexts. More importantly, this should be `tuple[float, float]` for type clarity, and ideally use `field(default_factory=tuple)` or just leave it as-is since tuples are immutable. **This is low-risk but worth noting for consistency.**

Actually, since tuples are immutable, this is **not a bug** in the traditional mutable-default sense. However, it should be typed: `confidence_interval: tuple[float, float] = (0.0, 1.0)`.

### 1.3 CSV Panel Rendering Produces Duplicate Headers (BUG)

**File:** `src/dashboard/renderers.py`, `TableauCSVRenderer.render_panel`

```python
def render_panel(self, panel: DashboardPanel) -> str:
    data = panel.render_data()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=self.delimiter)

    if self.include_header:
        writer.writerow(data.keys())  # Always writes header

    writer.writerow(data.values())
    return output.getvalue()
```

If `render_panel` is called multiple times (e.g., for multiple panels), each call produces a CSV string with its own header. This is **not a bug per se** since each call returns an independent string, but it's misleading. The docstring should clarify this behavior.

### 1.4 Layout Grid is Fragile on Panel Removal (DESIGN ISSUE)

**File:** `src/dashboard/layout.py`

```python
def get_panel_at(self, row: int, col: int) -> Optional[DashboardPanel]:
    index = row * self.columns + col
    if 0 <= index < len(self.panels):
        return self.panels[index]
    return None
```

Panels are stored in a flat list, and `get_panel_at` computes a linear index. If you add panels at (0,0) and (0,1), then remove the panel at (0,0), the panel that was at (0,1) shifts to index 0, so `get_panel_at(0,1)` now returns `None` instead of the panel. The grid layout is **not resilient to removals**.

**Recommendation:** Either:
- Use a 2D array (`List[List[Optional[DashboardPanel]]]`) internally, or
- Document that panels must not be removed from the middle of the grid, or
- Re-index all panels after removal

---

## 2. Important Issues

### 2.1 `DashboardTicker.price` Misleading Naming

**File:** `src/dashboard/tickers.py`

```python
def update_from_state(self, state: DashboardState) -> None:
    ...
    self.price = self.current_win_rate.value if self.current_win_rate else 0.0
```

The `price` attribute is repurposed to hold the win rate value. This is confusing because `price` typically means monetary value. Consider renaming to `display_value` or `metric_value`.

### 2.2 `price_color` Logic: Equal to 0.5 Returns "white"

**File:** `src/dashboard/tickers.py`

```python
if self.current_win_rate.value > 0.5:
    return "green"
elif self.current_win_rate.value < 0.5:
    return "red"
else:
    return "white"
```

This is intentional (test confirms it), but "white" for exactly 0.5 is semantically odd. Consider "gray" or "neutral" for clarity.

### 2.3 `WinRatePanel` Confidence Interval Uses Hardcoded Z-Score

**File:** `src/dashboard/panels.py`

```python
z = 1.96  # 95%
```

This is fine for a default, but consider making it configurable or at least documented as "95% confidence interval".

### 2.4 `BankrollCurvePanel.sparkline` Copies List Every Update

**File:** `src/dashboard/panels.py`

```python
self.sparkline = list(bh.history) if bh.history else [self.current_bankroll]
```

This is fine for correctness, but if `bh.history` is large, this creates a new list every update. Consider whether this is necessary or if a reference could be used.

### 2.5 `NashEquilibriumPanel.heatmap_color` Thresholds Are Magic Numbers

**File:** `src/dashboard/panels.py`

```python
if nd.distance < 0.05:
    self.heatmap_color = "green"
elif nd.distance < 0.15:
    self.heatmap_color = "yellow"
else:
    self.heatmap_color = "red"
```

These thresholds should be constants or configurable. Consider:

```python
NASH_GREEN_THRESHOLD = 0.05
NASH_YELLOW_THRESHOLD = 0.15
```

### 2.6 `TableauRESTRenderer` Has No Retry Logic

**File:** `src/dashboard/renderers.py`

```python
try:
    response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
    self.last_response = response
    return response
except requests.RequestException:
    self.last_response = None
    return None
```

Silently swallowing all `requests.RequestException` and returning `None` makes debugging difficult. Consider logging the exception or returning the exception for caller inspection.

---

## 3. Minor Issues & Suggestions

### 3.1 `panels.py` — `confidence_interval` Type Annotation

```python
confidence_interval: tuple = (0.0, 1.0)
```

Should be:
```python
confidence_interval: tuple[float, float] = (0.0, 1.0)
```

### 3.2 `panels.py` — `trend_arrow` Logic Could Be Simplified

```python
if self._previous_win_rate == 0.0:
    self.trend_arrow = "→"
elif wr.value > self._previous_win_rate + 0.005:
    self.trend_arrow = "↑"
elif wr.value < self._previous_win_rate - 0.005:
    self.trend_arrow = "↓"
else:
    self.trend_arrow = "→"
```

The `0.005` threshold is a "dead zone" to prevent flickering. This is reasonable but should be documented as a constant:

```python
TREND_DEAD_ZONE = 0.005
```

### 3.3 `layout.py` — `get_layout_info` Returns Panel Symbols as Lowercase

```python
"panels": [
    {"symbol": p.symbol, "type": type(p).__name__}
    for p in self.panels
],
```

`p.symbol` for `WinRatePanel` is `"WIN_RATE"` (uppercase), but the test expects `"win_rate"` (lowercase). Let me check...

**Test says:**
```python
assert info["panels"][0]["symbol"] == "win_rate"
```

**Source says:**
```python
symbol: str = "WIN_RATE"
```

**This is a TEST BUG.** The test expects lowercase but the source produces uppercase. Either the test or the source is wrong.

### 3.4 `renderers.py` — `TableauDashboard.render()` Builds State from Ticker

```python
def render(self) -> Any:
    if self.ticker is None:
        return None
    state = DashboardState(
        win_rate=self.ticker.current_win_rate,
        bankroll=self.ticker.bankroll_history,
        nash_distance=self.ticker.nash_distance,
        timestamp=self.ticker.timestamp,
    )
    return self.renderer.render(state)
```

This builds a `DashboardState` from the ticker, but the panels have already been updated from the ticker. The state is built fresh rather than using panel data. This is fine but slightly inconsistent — why not use panel `render_data()` results?

### 3.5 `tickers.py` — `to_dict()` Always Serializes All Metrics

```python
def to_dict(self) -> dict:
    return {
        "symbol": self.symbol,
        "price": self.price,
        "timestamp": self.timestamp,
        "previous_price": self.previous_price,
        "current_win_rate": self.current_win_rate.to_dict(),
        "bankroll_history": self.bankroll_history.to_dict(),
        "nash_distance": self.nash_distance.to_dict(),
    }
```

If any metric is `None` (which shouldn't happen per `__init__` but could if someone sets it manually), `to_dict()` will crash. Consider defensive checks.

### 3.6 `panels.py` — `BankrollCurvePanel.profit_loss` Is Derived, Not Stored

```python
self.profit_loss = self.current_bankroll - self.initial_bankroll
```

This is computed on every update. Since `initial_bankroll` is hardcoded to `1000.0`, this is fine, but consider making `initial_bankroll` configurable.

### 3.7 `renderers.py` — `TableauCSVRenderer.render()` Always Writes One Row

The `render` method writes exactly one row of data. If you want to render multiple timesteps, you'd need to call it multiple times. This is fine for a single snapshot but could be confusing.

### 3.8 `layout.py` — No Validation on `rows`/`columns` Being Positive

```python
def set_grid_dimensions(self, rows: int, columns: int) -> None:
    total_cells = rows * columns
    if len(self.panels) > total_cells:
        raise ValueError(...)
```

If `rows=0` or `columns=0`, `total_cells=0`, and any panels will raise `ValueError`. This is technically correct but could be clearer with an explicit check:

```python
if rows <= 0 or columns <= 0:
    raise ValueError("Rows and columns must be positive")
```

---

## 4. Test Issues

### 4.1 Test 3.3: Symbol Case Mismatch

**File:** `tests/dashboard/test_layout.py`

```python
assert info["panels"][0]["symbol"] == "win_rate"
```

But `WinRatePanel.symbol = "WIN_RATE"`. The test should be:

```python
assert info["panels"][0]["symbol"] == "WIN_RATE"
```

### 4.2 Missing Test for `TableauDashboard.__post_init__` Default Panels

There's no test verifying that `TableauDashboard()` creates the three default panels.

### 4.3 Missing Test for `TableauRESTRenderer` Exception Handling

There's no test verifying that `render` returns `None` on network failure.

### 4.4 Missing Test for `DashboardBoard` with Panels at Initialization

The test `test_init_too_many_panels` exists, but there's no test for successful initialization with panels.

### 4.5 `TestDashboardTickerUpdate.test_update_updates_timestamp` Is Flaky

```python
before = time.time()
dt.update(20.0)
after = time.time()
assert before <= dt.timestamp <= after
```

This is technically correct but could fail under extreme load. Consider using `time.monotonic()` or a mock.

---

## 5. Architecture & Design Observations

### 5.1 Good: Clear Separation of Concerns

- **Models**: Pure data classes
- **Tickers**: Data aggregation and serialization
- **Panels**: Metric computation and visual encoding
- **Layout**: Grid management
- **Renderers**: Output format strategies

### 5.2 Good: Strategy Pattern for Renderers

`TableauRenderer` base class with `CSV` and `REST` subclasses is a clean implementation of the strategy pattern.

### 5.3 Good: Panel Binding Pattern

`bind_ticker()` / `update_from_bound_ticker()` allows panels to be loosely coupled to their data source.

### 5.4 Concern: `TableauDashboard` and `DashboardBoard` Do Similar Things

Both manage panels. `TableauDashboard` is focused on rendering, `DashboardBoard` on layout. Consider whether these should be unified or if the distinction is clear enough.

### 5.5 Concern: No Caching in Panels

`WinRatePanel.update()` computes Wilson score CI on every call. If called frequently, this could be optimized with caching.

### 5.6 Suggestion: Add `__repr__` to Data Classes

For debugging, `__repr__` methods would be helpful on `DashboardTicker`, `DashboardPanel` subclasses, and `DashboardBoard`.

---

## 6. Summary of Required Fixes

| Priority | Issue | File | Lines |
|----------|-------|------|-------|
| **BLOCKER** | Missing imports in `renderers.py` | `renderers.py` | ~140 |
| **BUG** | Test expects lowercase symbol, source uses uppercase | `test_layout.py` | ~95 |
| **DESIGN** | Grid layout breaks on panel removal | `layout.py` | ~45 |
| **DESIGN** | `price` attribute repurposed for win rate | `tickers.py` | ~50 |
| **MINOR** | Magic numbers for Nash thresholds | `panels.py` | ~130 |
| **MINOR** | No logging on REST failure | `renderers.py` | ~110 |
| **MINOR** | Missing test for default panels in `TableauDashboard` | `test_renderers.py` | N/A |
| **MINOR** | Missing test for REST exception handling | `test_renderers.py` | N/A |

---

## 7. Recommendation

**Do not merge** until the BLOCKER (missing imports) and the TEST BUG (symbol case mismatch) are fixed. The DESIGN issues (grid fragility, price naming) should be addressed in a follow-up PR. The remaining items are nice-to-haves.

**Overall quality: 7/10** — Clean architecture, good test coverage, but a few critical oversights prevent immediate merge.
