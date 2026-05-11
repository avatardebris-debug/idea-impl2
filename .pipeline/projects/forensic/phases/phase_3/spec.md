## Phase 3 — Capital Flow Analysis + Advanced Red Flags

**Goal**: Add capital flow analysis (operating, investing, financing cash flows)
and advanced red-flag detection (Benford's Law, M-Score, Beneish indicators).

### Deliverable

- CLI command `forensic capital <TICKER>` that:
  1. Extracts cash flow statement data from 10-K/10-Q filings.
  2. Analyzes capital flows:
     - Operating vs. investing vs. financing cash flow trends.
     - Capex-to-revenue ratios.
     - Debt issuance / repayment patterns.
     - Dividend and share repurchase trends.
  3. Runs advanced red-flag checks:
     - **Benford's Law test** on numerical values in filing text.
     - **M-Score** (Dechow et al.) for earnings manipulation detection.
     - **Beneish M-Score** for earnings manipulation detection.
     - **Altman Z-Score** for bankruptcy risk.
  4. Outputs a capital flow analysis report with:
     - Cash flow trend charts (JSON-encoded data for downstream viz).
     - Advanced red-flag results with scores and interpretations.

### Dependencies

- All Phase 1–2 modules.
- `matplotlib` — Optional charting support.

### File Structure (Phase 3 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── capital_flow.py      # Capital flow analysis
│       ├── advanced_flags.py    # Benford, M-Score, Beneish, Altman
│       └── ... (Phase 1–2 files)
├── tests/
│   ├── test_capital_flow.py
│   └── test_advanced_flags.py
```

### Success Criteria

- [ ] `forensic capital AAPL` completes end-to-end.
- [ ] At least 4 advanced red-flag checks run and produce interpretable results.
- [ ] Capital flow data is extractable and comparable across periods.

---

