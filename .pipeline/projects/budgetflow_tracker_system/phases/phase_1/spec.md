## Phase 1 — MVP: Core Transaction Engine & Categorization
> *"The smallest useful thing: ingest transactions, categorize them, and see where money went."*

#### Description
Build the foundational data layer and categorization pipeline. Users can import bank transaction CSVs, have them auto-categorized, and view spending summaries by category. This is the irreducible core — without it, nothing else works.

#### Deliverables
1. **SQLite schema & migration system** — Tables for `accounts`, `transactions`, `categories`, `budgets`, `transaction_rules`.
2. **CSV import pipeline** — Auto-detects bank format, maps columns, validates data, bulk-inserts into SQLite.
3. **Rule-based categorization engine** — User defines rules (e.g., "merchant contains 'Starbucks' → Category: Food & Drink"); engine applies rules to imported transactions.
4. **CLI dashboard** — Terminal-based view showing spending by category over a configurable date range.
5. **Budget creation UI (CLI)** — Set monthly budgets per category; view progress bars showing spend vs. budget.

#### Dependencies
- None (this is the foundation phase).

#### Success Criteria
- [ ] User can import a CSV from any major US bank (Chase, Wells Fargo, Bank of America, Capital One) and see transactions loaded.
- [ ] Auto-categorization correctly classifies ≥80% of transactions on first pass (using default rules).
- [ ] User can view a spending summary by category for any date range in the CLI.
- [ ] Budget creation and progress tracking works for at least 3 categories.
- [ ] All data is stored locally in SQLite — no network calls.

---

#