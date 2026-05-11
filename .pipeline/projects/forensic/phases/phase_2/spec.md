## Phase 2 — Multi-Company Analysis + Earnings Prediction

**Goal**: Extend the suite to analyze multiple companies, compare them, and
add an earnings prediction module based on historical filing data.

### Deliverable

- CLI command `forensic compare <TICKER1> <TICKER2> ...` that:
  1. Ingests latest 10-K and 10-Q filings for all specified tickers.
  2. Normalizes financial line items across companies (revenue, COGS, operating
     income, net income, total assets, total liabilities, cash flow from ops,
     capex, working capital).
  3. Runs the Phase 1 red-flag checks on each company.
  4. Computes a **comparative fraud score** (relative ranking).
  5. Runs an **earnings prediction module** that:
     - Extracts historical quarterly earnings data from 10-Q filings.
     - Fits a simple linear regression or moving-average model.
     - Predicts next quarter's EPS and revenue.
     - Flags prediction confidence intervals.
  6. Outputs a comparative JSON report with:
     - Per-company fraud scores and red flags.
     - Comparative ranking.
     - Earnings predictions with confidence intervals.

### Dependencies

- All Phase 1 modules.
- `numpy` / `pandas` — For regression and time-series analysis.

### File Structure (Phase 2 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── compare.py           # Multi-company comparison logic
│       ├── earnings.py          # Earnings prediction module
│       ├── normalization.py     # Financial line-item normalization
│       └── ... (Phase 1 files)
├── tests/
│   ├── test_compare.py
│   ├── test_earnings.py
│   └── test_normalization.py
```

### Success Criteria

- [ ] `forensic compare AAPL MSFT GOOGL` completes end-to-end.
- [ ] Comparative report includes per-company fraud scores and rankings.
- [ ] Earnings predictions include point estimates and confidence intervals.
- [ ] Normalization handles at least 8 standard financial line items.

---

