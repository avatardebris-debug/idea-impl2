# Dropsearch — Master Implementation Plan

## Idea Summary

**Dropsearch** is a dropship competitor intelligence tool. It spies on competitors' online stores, analyzes their product catalogs, pricing, marketing angles, and supplier sources — then produces a full English-language business gameplan describing the entire operation: what to sell, where to source it, how to price it, and how to market it.

---

## Core Deliverable

A **competitor intelligence report + actionable business gameplan** in plain English, generated from automated competitor store analysis. The user provides one or more competitor store URLs (or keywords/niches), and dropsearch returns:

1. A structured analysis of the competitor's product catalog, pricing tiers, and supplier chains.
2. A market gap analysis — what the competitor is missing or doing poorly.
3. A step-by-step business gameplan in full English: product selection, supplier sourcing, pricing strategy, marketing angles, and launch checklist.

---

## Architecture Notes

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Input Layer │────▶│  Scraping    │────▶│  Analysis Engine │
│  (URLs,      │     │  & Data      │     │  (LLM + Rules)   │
│   keywords)  │     │  Pipeline    │     │                  │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                          ┌────────▼─────────┐
                                          │  Gameplan        │
                                          │  Generator       │
                                          │  (LLM-driven)    │
                                          └────────┬─────────┘
                                                   │
                                          ┌────────▼─────────┐
                                          │  Output: Full    │
                                          │  English Report  │
                                          └──────────────────┘
```

**Key components:**
- **Input Layer**: Accepts competitor store URLs, niche keywords, or platform handles (Shopify stores, Amazon listings, Etsy shops).
- **Scraping Pipeline**: Headless browser + regex/HTML parsers to extract product data, prices, descriptions, images, reviews, and supplier hints (e.g., AliExpress/Spocket links in source code).
- **Analysis Engine**: Rule-based heuristics (margin calculations, review sentiment, price positioning) + LLM reasoning for gap analysis.
- **Gameplan Generator**: LLM-driven module that synthesizes all findings into a coherent, actionable business plan in plain English.

**Tech stack (recommended):**
- Python 3.11+
- Playwright or Selenium for scraping
- BeautifulSoup + lxml for HTML parsing
- OpenAI API or local LLM (Ollama) for analysis and gameplan generation
- SQLite or JSON files for intermediate data storage
- Pydantic for data models

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Competitor sites block scrapers (CAPTCHAs, rate limits) | High | Rotate user agents, add delays, use residential proxies as optional upgrade, fallback to public APIs (Amazon Product Advertising API, etc.) |
| E-commerce platforms change their HTML structure frequently | Medium | Use flexible CSS/XPath selectors with versioned parsers; add schema validation on extracted data |
| LLM hallucination in analysis/gameplan output | Medium | Ground all LLM output in extracted data; include source citations in the report; add a validation pass |
| Legal/ToS concerns with scraping | Medium | Add a compliance mode that uses only public APIs and publicly available data; include a ToS disclaimer |
| Data quality from poorly structured competitor sites | Medium | Fallback strategies per site type; confidence scores on extracted data; manual review option |

---

## Phase Breakdown

### Phase 1 — MVP: Single-Store Product Extractor + Basic Report

**Description:** The smallest useful thing: scrape ONE competitor store, extract its product catalog (name, price, description, images), and generate a basic text report listing what the competitor sells and at what prices.

**Deliverable:** A CLI tool (`dropsearch scan <url>`) that outputs a plain-text product catalog report for a single store.

**Dependencies:** None (standalone tool).

**Success Criteria:**
- Successfully extracts 90%+ of product names, prices, and descriptions from a test Shopify/WordPress/WooCommerce store.
- Outputs a readable text/Markdown report with structured product listings.
- Handles basic anti-bot measures (user-agent rotation, polite delays).
- Runs end-to-end in under 60 seconds on a test store with <200 products.

---

### Phase 2 — Intelligence Engine: Multi-Store Comparison + Supplier Detection

**Description:** Extend the MVP to handle multiple competitor stores simultaneously. Add supplier chain detection (find AliExpress, CJ Dropshipping, Spocket, or other dropship supplier links embedded in competitor store source code). Add margin analysis and price positioning comparison across competitors.

**Deliverable:** A CLI tool (`dropsearch analyze <url1> <url2> ...`) that compares 2+ competitors, detects their supplier chains, and produces a comparative analysis report with margin estimates and pricing gaps.

**Dependencies:** Phase 1 (product extraction must work).

**Success Criteria:**
- Correctly identifies supplier sources (AliExpress, CJ, Spocket, etc.) in 80%+ of test cases.
- Produces a side-by-side comparison of 3+ competitors with price, product overlap, and margin analysis.
- Detects product overlap between competitors (same products sold by multiple stores).
- Report includes actionable insights (e.g., "Competitor A sources from AliExpress at $X, sells at $Y — 60% margin; you could source from CJ at $Z for a 70% margin").

---

### Phase 3 — Gameplan Generator: Full English Business Plan

**Description:** The final phase: take the intelligence from Phase 2 and feed it into an LLM-powered gameplan generator. The LLM synthesizes all competitor data, market gaps, and supplier information into a comprehensive, step-by-step business gameplan in full English. This includes: product recommendations, supplier sourcing strategy, pricing strategy, marketing angles, store setup checklist, and launch timeline.

**Deliverable:** A complete CLI tool (`dropsearch plan <url1> <url2> ...`) that outputs a full English-language business gameplan document, ready for the user to execute.

**Dependencies:** Phase 2 (multi-store analysis with supplier detection).

**Success Criteria:**
- Gameplan is coherent, actionable, and covers all required sections (product selection, sourcing, pricing, marketing, launch).
- LLM output is grounded in extracted data — every recommendation cites a source (e.g., "Based on Competitor A's $45 price point and AliExpress cost of $12...").
- User can run the full pipeline end-to-end and receive a complete gameplan in under 5 minutes.
- Gameplan includes a prioritized action checklist with estimated costs and timelines.
- At least 80% of recommendations are deemed "actionable" by a human reviewer on test cases.

---

## Summary Table

| Phase | Scope | Deliverable | Key Value |
|-------|-------|-------------|-----------|
| **1** | Single-store scraping | Product catalog report | Know what a competitor sells and at what price |
| **2** | Multi-store comparison + supplier detection | Competitive intelligence report | Know who your competitors are, where they source from, and where the gaps are |
| **3** | LLM gameplan generator | Full English business plan | Get a ready-to-execute business strategy based on competitor intelligence |

---

## File Structure (Target)

```
projects/dropsearch/
├── state/
│   └── master_plan.md
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (dropsearch scan/analyze/plan)
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── browser.py      # Playwright headless browser setup
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── shopify.py
│   │   │   ├── woocommerce.py
│   │   │   └── generic.py
│   │   └── anti_detect.py  # User-agent rotation, delays
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── supplier_detector.py
│   │   ├── margin_calculator.py
│   │   └── comparator.py
│   ├── gameplan/
│   │   ├── __init__.py
│   │   ├── llm_engine.py
│   │   └── templates/
│   │       └── gameplan_prompt.jinja2
│   └── models/
│       ├── __init__.py
│       ├── product.py
│       ├── competitor.py
│       └── gameplan.py
├── tests/
│   ├── test_scraper.py
│   ├── test_analyzer.py
│   ├── test_gameplan.py
│   └── fixtures/
│       └── sample_store.html
├── requirements.txt
└── README.md
```

---

## Open Questions

1. **Which e-commerce platforms to support first?** Shopify is the most common for dropshipping stores. WooCommerce and Amazon come next.
2. **Should we support reverse-search (product image → supplier)?** This would be a powerful Phase 3+ feature.
3. **API vs. scraping trade-off:** For Amazon/Etsy, public APIs may be more reliable than scraping. Should we integrate those?
4. **Output format:** Should the gameplan be Markdown, PDF, or both?
5. **Multi-language support:** Should the gameplan support languages other than English?
