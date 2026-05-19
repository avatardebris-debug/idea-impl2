## Phase 2 — Supplier Integration + Automated Price & Inventory Management

### Description
Expand the platform to connect directly with supplier APIs, enabling automated product import, real-time price/inventory sync, and margin optimization. This turns the store from a manual setup into a self-managing system.

### Deliverable
- **Multi-Supplier API Integration**: Connect to AliExpress (via DSers/Spocket API), CJDropshipping, or similar
- **Automated Product Import**: Auto-import products from suppliers into the catalog with one click
- **Price & Inventory Sync Engine**: Scheduled jobs that update prices and stock levels from suppliers
- **Margin Optimizer**: Rule-based pricing engine (e.g., "always markup 40% over landed cost")
- **Alert System**: Low-stock, price-change, and supplier-issue notifications

### Dependencies
- Phase 1 must be complete (catalog + Shopify sync foundation)

### Success Criteria
- [ ] User can import products from ≥2 supplier sources
- [ ] Price/inventory updates run automatically on a configurable schedule (default: every 6 hours)
- [ ] Margin calculations are accurate within 2% of actual supplier pricing
- [ ] User receives alerts for ≥95% of critical supplier events
- [ ] Sync failures are logged and retryable without data loss

---

