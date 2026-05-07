## Phase 1 — MVP: Data Ingestion + Single-Company Fraud Score

**Goal**: A working pipeline that ingests SEC filings for a single company,
runs a basic fraud detection analysis, and outputs a composite fraud score
with red-flag details.

### Deliverable

- CLI command `forensic analyze <TICKER>` that:
  1. Uses `sec_importer.fetcher` to resolve ticker → CIK and fetch the latest 10-K.
  2. Uses `sec_importer.parser.FilingParser` to parse the filing into structured items.
  3. Stores parsed data in `sec_importer.repository.SECDatabase`.
  4. Runs a **basic fraud detection module** that checks for:
     - Revenue recognition anomalies (revenue vs. receivables growth mismatch)
     - Related-party transaction flags
     - Auditor change / going-concern warnings
     - Restatement / amendment history
     - Unusual segment reporting changes
  5. Computes a **composite fraud score** (0–100) from weighted red-flag indicators.
  6. Outputs a JSON report with:
     - High-level summary (fraud score, risk level, top 3 red flags)
     - Detailed red-flag entries with evidence excerpts and severity

### Dependencies

- `sec_importer.fetcher` — `resolve_ticker_to_cik`, `get_latest_filing`, `download_filing_text`
- `sec_importer.parser` — `FilingParser`, `parse_filing`
- `sec_importer.repository` — `SECDatabase`
- `sec_importer.models` — `FilingModel`, `FilingItemModel`
- `sec_importer.config` — `Config`

### File Structure (Phase 1)

```
forensic/
├── state/
│   └── master_plan.md
├── src/
│   └── forensic/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # argparse CLI (analyze command)
│       ├── ingest.py            # Data ingestion using sec_importer
│       ├── red_flags.py         # Red-flag detection rules (basic set)
│       ├── scoring.py           # Composite fraud score computation
│       └── models.py            # Forensic-specific Pydantic models
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_red_flags.py
│   └── test_scoring.py
├── config.yaml
├── requirements.txt
└── README.md
```

### Success Criteria

- [ ] `forensic analyze AAPL` completes end-to-end without errors.
- [ ] Output JSON contains a `fraud_score` (0–100), `risk_level`, `summary`, and `red_flags` list.
- [ ] At least 5 distinct red-flag checks run against the filing.
- [ ] Composite score is deterministic given the same input data.
- [ ] All tests pass.

---