# Code Review — Phase 2

## Blocking Bugs
- **RESOLVED: Test symbol case mismatch** — `tests/test_layout.py` already expects `"WIN_RATE"` and `"BANKROLL"` (uppercase), matching the source code in `panels.py`. All 11 tests in `test_layout.py` pass.

## Non-Blocking Notes
- `renderers.py` already has the correct imports for `WinRatePanel`, `BankrollCurvePanel`, and `NashEquilibriumPanel` (imported at top of file).
- `panels.py` mutable default argument for `confidence_interval` is low-risk since tuples are immutable, but should be typed as `tuple[float, float]`.
- Grid layout in `layout.py` is fragile on panel removal (panels stored in flat list, accessed via linear index).
- `price` attribute in `tickers.py` is repurposed for win rate — consider renaming.
- Magic numbers for Nash thresholds in `panels.py` should be constants.
- Missing tests for `TableauDashboard.__post_init__` default panels and `TableauRESTRenderer` exception handling.

## Verdict
PASS — blocking bug has been resolved. All tests in `test_layout.py` pass.
