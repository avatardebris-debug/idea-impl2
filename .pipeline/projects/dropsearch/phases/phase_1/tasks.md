# Phase 1 Tasks

- [x] Task 1: Project scaffolding and dependency setup
  - What: Create the initial project structure with requirements, entry point, and CLI framework.
  - Files:
    - `src/__init__.py`
    - `src/cli.py` — CLI entry point using `click` or `argparse` with `dropsearch scan <url>` command
    - `src/models/product.py` — Pydantic model for Product (name, price, description, image_url, url)
    - `requirements.txt` — dependencies: playwright, beautifulsoup4, lxml, click, fake-useragent
    - `README.md` — basic project readme with install/run instructions
  - Done when: `pip install -r requirements.txt` succeeds; `dropsearch scan https://example.com` runs without import errors and prints a usage message.

- [x] Task 2: Browser-based page fetcher with anti-bot basics
  - What: Build a reusable page-fetching module that loads a URL via Playwright (headless Chromium), handles user-agent rotation, polite delays, and returns the rendered HTML.
  - Files:
    - `src/scraper/__init__.py`
    - `src/scraper/browser.py` — Playwright headless browser setup, page load, HTML extraction
    - `src/scraper/anti_detect.py` — User-agent rotation via fake-useragent, random delays, basic stealth headers
  - Done when: Fetching a real store URL (e.g., a public Shopify demo store) returns valid HTML; user-agent rotates across calls; no Playwright errors on standard stores.

- [x] Task 3: Product catalog extractor with multi-platform selectors
  - What: Build the core scraping logic that parses the fetched HTML and extracts product name, price, description, and image URL. Support Shopify and WooCommerce product listing pages with robust CSS/XPath selectors.
  - Files:
    - `src/scraper/parsers/__init__.py`
    - `src/scraper/parsers/shopify.py` — Shopify-specific product selectors (JSON-LD + CSS)
    - `src/scraper/parsers/woocommerce.py` — WooCommerce-specific product selectors (JSON-LD + CSS)
    - `src/scraper/parsers/generic.py` — Generic HTML parser with broad CSS selectors for unknown stores
    - `src/scraper/extractor.py` — Orchestrator that detects platform and delegates to the right parser
  - Done when: Extracting products from a Shopify store, WooCommerce store, and a generic HTML page all return correctly parsed product objects with name, price, description, and image_url.

- [x] Task 4: Report formatter and CLI integration
  - What: Add report formatting (Markdown and plain text) and wire it into the CLI so users can output structured reports.
  - Files:
    - `src/reporter/__init__.py`
    - `src/reporter/formatter.py` — ReportFormatter with markdown and text output
    - Update `src/cli.py` — Add `-f` / `--format` flag (markdown/text), `-o` / `--output` flag for file output
  - Done when: `dropsearch scan https://example.com -f markdown -o report.md` produces a valid Markdown file with product details.

- [x] Task 5: Tests and fixtures
  - What: Write comprehensive tests for all parsers, the extractor, and the formatter using HTML fixtures.
  - Files:
    - `tests/__init__.py`
    - `tests/fixtures/shopify_store.html` — HTML fixture simulating a Shopify product listing
    - `tests/fixtures/woocommerce_store.html` — HTML fixture simulating a WooCommerce product listing
    - `tests/fixtures/generic_store.html` — HTML fixture simulating a generic store page
    - `tests/test_product_extraction.py` — Tests for ShopifyParser, WooCommerceParser, GenericParser, ProductExtractor, ReportFormatter
  - Done when: All tests pass with `pytest tests/ -v`.

# Phase 2 Tasks

- [ ] Task 6: Pagination support
  - What: Handle paginated product listings (e.g., Shopify's `?page=2`, WooCommerce's `/page/2/`) and follow links to extract products from all pages.
  - Files:
    - Update `src/scraper/browser.py` — Add pagination link detection and navigation
    - Update `src/scraper/extractor.py` — Add pagination loop with deduplication
  - Done when: Scanning a multi-page store extracts products from all pages without duplicates.

- [ ] Task 7: Rate limiting and politeness
  - What: Add configurable rate limiting between requests and respect `robots.txt`.
  - Files:
    - `src/scraper/rate_limiter.py` — Token bucket or fixed-delay rate limiter
    - `src/scraper/robots.py` — robots.txt parser and compliance
  - Done when: Scanning a large store respects rate limits and does not violate robots.txt.

- [ ] Task 8: Output to CSV/JSON
  - What: Add CSV and JSON output formats to the report formatter.
  - Files:
    - Update `src/reporter/formatter.py` — Add CSV and JSON formatting methods
    - Update `src/cli.py` — Add `-f csv` and `-f json` format options
  - Done when: `dropsearch scan https://example.com -f json -o products.json` produces valid JSON output.

- [ ] Task 9: URL fetching integration
  - What: Wire the browser fetcher into the CLI so real URLs can be scanned (not just local files).
  - Files:
    - Update `src/cli.py` — Replace `file://`-only support with real URL fetching via `browser.py`
    - Update `src/scraper/browser.py` — Ensure robust error handling for failed fetches
  - Done when: `dropsearch scan https://realstore.com` fetches the page, extracts products, and outputs a report.

- [ ] Task 10: Final integration testing and polish
  - What: End-to-end testing on real stores, error handling polish, and documentation updates.
  - Files:
    - `tests/test_integration.py` — Integration tests on real store URLs (with mock network if needed)
    - Update `README.md` — Complete documentation with all flags, examples, and troubleshooting
  - Done when: Full end-to-end scan of a real store works reliably; README is complete.