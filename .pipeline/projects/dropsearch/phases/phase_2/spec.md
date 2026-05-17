## Phase 2 — Intelligence Engine: Multi-Store Comparison + Supplier Detection

**Description:** Extend the MVP to handle multiple competitor stores simultaneously. Add supplier chain detection (find AliExpress, CJ Dropshipping, Spocket, or other dropship supplier links embedded in competitor store source code). Add margin analysis and price positioning comparison across competitors.

**Deliverable:** A CLI tool (`dropsearch analyze <url1> <url2> ...`) that compares 2+ competitors, detects their supplier chains, and produces a comparative analysis report with margin estimates and pricing gaps.

**Dependencies:** Phase 1 (product extraction must work).

**Success Criteria:**
- Correctly identifies supplier sources (AliExpress, CJ, Spocket, etc.) in 80%+ of test cases.
- Produces a side-by-side comparison of 3+ competitors with price, product overlap, and margin analysis.
- Detects product overlap between competitors (same products sold by multiple stores).
- Report includes actionable insights (e.g., "Competitor A sources from AliExpress at $X, sells at $Y — 60% margin; you could source from CJ at $Z for a 70% margin").

---

#