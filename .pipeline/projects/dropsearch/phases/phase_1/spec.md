## Phase 1 — MVP: Single-Store Product Extractor + Basic Report

**Description:** The smallest useful thing: scrape ONE competitor store, extract its product catalog (name, price, description, images), and generate a basic text report listing what the competitor sells and at what prices.

**Deliverable:** A CLI tool (`dropsearch scan <url>`) that outputs a plain-text product catalog report for a single store.

**Dependencies:** None (standalone tool).

**Success Criteria:**
- Successfully extracts 90%+ of product names, prices, and descriptions from a test Shopify/WordPress/WooCommerce store.
- Outputs a readable text/Markdown report with structured product listings.
- Handles basic anti-bot measures (user-agent rotation, polite delays).
- Runs end-to-end in under 60 seconds on a test store with <200 products.

---

#