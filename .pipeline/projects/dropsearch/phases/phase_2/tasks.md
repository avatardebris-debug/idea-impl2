# Phase 2 Tasks

- [ ] Task 1: Multi-store data models and analysis orchestrator
  - What: Create data models for storing multi-store analysis results and an orchestrator class that fetches, extracts, and compares multiple competitor stores.
  - Files:
    - `src/models/store_analysis.py` — New Pydantic models: `StoreAnalysis` (stores_url, platform, products, supplier_info, raw_html), `ProductMatch` (product_name, price_at_store, price_at_source, overlap_score), `CompetitorComparison` (stores, product_overlaps, price_gaps, insights)
    - `src/scraper/multi_analyzer.py` — `MultiStoreAnalyzer` class: takes a list of URLs, fetches each via `BrowserFetcher`, extracts products via `ProductExtractor`, and aggregates results into `StoreAnalysis` objects
    - Update `src/cli.py` — Add `analyze` subcommand: `dropsearch analyze <url1> <url2> ...` that delegates to `MultiStoreAnalyzer`
  - Done when: `MultiStoreAnalyzer` can process 3 URLs, produce `StoreAnalysis` objects for each, and the CLI `dropsearch analyze` command runs without errors (with `file://` URLs for now).

- [ ] Task 2: Supplier chain detection engine
  - What: Build a `SupplierDetector` that scans competitor store HTML for embedded supplier links (AliExpress, CJ Dropshipping, Spocket, AliDrop, DSers, etc.) and extracts supplier pricing hints.
  - Files:
    - `src/scraper/supplier_detector.py` — `SupplierDetector` class with:
      - Pattern-based detection for supplier domains (aliexpress.com, cjdropshipping.com, spocket.co, alidrop.io, dsers.com, zendrop.com, doba.com, salehoo.com, etc.)
      - Detection of hidden supplier prices in data attributes, JSON blobs, and script tags
      - Detection of supplier API endpoints and iframe embeds
      - Returns `SupplierChain` objects: {source: str, confidence: float, detected_urls: list[str], estimated_cost: float | None}
    - `tests/fixtures/supplier_detection.html` — HTML fixture with embedded supplier links (AliExpress product links, CJ dropshipping data attributes, Spocket iframe, etc.)
    - `tests/test_supplier_detection.py` — Tests verifying detection of each supplier type, confidence scoring, and edge cases (no suppliers, ambiguous links)
  - Done when: `SupplierDetector` correctly identifies AliExpress, CJ Dropshipping, Spocket, and other supplier sources in 80%+ of test cases from the fixture; returns structured `SupplierChain` objects with confidence scores.

- [ ] Task 3: Margin analysis and product overlap detection
  - What: Build analysis modules that estimate profit margins and detect which products are sold by multiple competitors.
  - Files:
    - `src/analysis/margin_analyzer.py` — `MarginAnalyzer` class:
      - Estimates supplier cost from detected supplier chains (or uses industry-standard dropshipping cost multipliers: AliExpress ~30-40% of retail, CJ ~25-35%, Spocket ~45-55%)
      - Calculates gross margin: `(retail_price - estimated_cost) / retail_price * 100`
      - Produces `MarginEstimate` objects: {product_name, retail_price, estimated_cost, margin_pct, supplier_source}
    - `src/analysis/overlap_detector.py` — `OverlapDetector` class:
      - Compares product names across all `StoreAnalysis` objects
      - Uses fuzzy string matching (Levenshtein distance or token set ratio) to detect same products sold by different stores
      - Produces `ProductOverlap` objects: {product_name, stores: list[str], prices: dict[str, float], price_spread: float}
    - `tests/test_margin_analysis.py` — Tests for margin calculation with known supplier costs
    - `tests/test_overlap_detection.py` — Tests for product overlap detection with fuzzy matching
  - Done when: Margin analyzer produces accurate margin estimates for known supplier costs; overlap detector correctly identifies matching products across stores with fuzzy matching tolerance.

- [ ] Task 4: Comparative report formatter with actionable insights
  - What: Create a new report format that presents side-by-side competitor comparisons with actionable business insights.
  - Files:
    - `src/reporter/comparative_formatter.py` — `ComparativeReportFormatter` class:
      - `format_comparison(stores: list[StoreAnalysis], overlaps: list[ProductOverlap], margins: list[MarginEstimate])` → Markdown report
      - Sections: (1) Executive summary with top findings, (2) Side-by-side price table for overlapping products, (3) Supplier chain breakdown per competitor, (4) Margin analysis per product, (5) Pricing gap analysis (who undercuts whom), (6) Actionable insights (e.g., "Competitor A sources from AliExpress at $X, sells at $Y — 60% margin; you could source from CJ at $Z for a 70% margin")
    - Update `src/reporter/formatter.py` — Add `comparative` format option
    - Update `src/cli.py` — Add `--insights` flag to include actionable insights in output
  - Done when: `dropsearch analyze <url1> <url2> -f comparative` produces a structured Markdown report with all required sections; actionable insights are generated based on detected margins and supplier chains.

- [ ] Task 5: End-to-end integration and CLI polish
  - What: Wire all components together, add URL fetching to the `analyze` command, and write integration tests.
  - Files:
    - Update `src/cli.py` — Wire `BrowserFetcher` into the `analyze` command so real URLs work (not just `file://`)
    - Update `src/cli.py` — Add `-f comparative` format option, `--insights` flag, `--min-overlap` flag to filter overlaps by minimum store count
    - `tests/test_integration.py` — Integration tests using HTML fixtures that simulate 3+ stores with overlapping products and embedded supplier links
    - Update `requirements.txt` — Add `thefuzz` or `rapidfuzz` for fuzzy string matching (if not already present)
    - Update `pyproject.toml` — Add `rapidfuzz` to dependencies
  - Done when: `dropsearch analyze` works end-to-end with HTML fixtures; all integration tests pass; fuzzy matching dependency is installed; CLI flags `--insights` and `--min-overlap` function correctly.