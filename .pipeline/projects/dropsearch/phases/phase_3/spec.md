## Phase 3 — Gameplan Generator: Full English Business Plan

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

1. **Which e-commerce platforms to support first?** Shopify is the most common for dr