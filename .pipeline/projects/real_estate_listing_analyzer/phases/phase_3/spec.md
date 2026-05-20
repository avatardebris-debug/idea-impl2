## Phase 3 — Report Generation (CSV + PDF)
- Implement `ReportBuilder`:
  - CSV export: one row per listing with all computed metrics
  - PDF export: CMA summary page + price trend chart (matplotlib)
  - Markdown export: ranked listing table with neighborhood highlights
- CLI: `real-estate-analyzer report --format pdf --out ./report.pdf`
- Implement `AlertEngine`: flag listings with >5% below-trend price as deals
- Tests: golden-file CSV comparison, PDF byte-size sanity check