## Phase 2 — Supplier Integrations + Fulfillment Automation

> **Goal:** Make dropshipping actually work — connect stores to suppliers and automate order fulfillment.

### Description

Add the dropshipping-specific layer that differentiates Dropify from a generic store builder:
- Supplier marketplace / directory with product catalogs
- One-click product import from suppliers (with auto-pricing markup)
- Automated order forwarding to suppliers when a customer places an order
- Tracking number sync from suppliers back to the store
- Supplier performance metrics and reliability scoring

### Deliverables

1. **Supplier Directory**
   - Curated list of dropshipping suppliers (AliExpress, Spocket, CJ Dropshipping, etc.)
   - Supplier profiles with ratings, shipping times, product categories
   - Search and filter suppliers by category, location, shipping speed

2. **Product Import from Suppliers**
   - API connectors for top 3 suppliers
   - One-click import: fetch product data, images, pricing from supplier
   - Auto-markup configuration (e.g., "add 30% margin")
   - Sync schedule: periodic updates of supplier product data (price, stock)
   - Conflict resolution: handle duplicate products, out-of-stock items

3. **Automated Order Fulfillment**
   - When a customer order is placed → auto-forward to supplier
   - Supplier API integration for order placement
   - Status sync: pending → processing → shipped → delivered
   - Tracking number auto-population on customer order

4. **Fulfillment Dashboard**
   - Overview of pending, processing, shipped, failed orders
   - Manual override: manually fulfill or cancel orders
   - Supplier selection per product (multi-supplier support)
   - Profit margin calculator (sell price - supplier cost - fees)

5. **Inventory Sync Engine**
   - Background jobs (cron) to sync supplier stock levels
   - Low-stock alerts
   - Auto-disable products when out of stock at supplier
   - Webhook-based real-time sync where supplier APIs support it

### Dependencies

- **Phase 1 complete** — Store builder, product management, and checkout must work.
- Stripe API access (already integrated in Phase 1)
- Supplier API keys (AliExpress API, Spocket API, etc.)

### Success Criteria

| Criterion | Metric |
|-----------|--------|
| Supplier onboarding | User can connect a supplier account in < 3 minutes |
| Product import | Import 50 supplier products with < 5 minutes |
| Auto-fulfillment | 95% of orders auto-forwarded to supplier without manual intervention |
| Tracking sync | Tracking numbers appear in customer email within 2 hours of supplier update |
| Inventory accuracy | Stock levels synced within 1 hour of supplier change |
| Margin accuracy | Profit calculations accurate to within $0.01 |

### Key Technical Decisions

- **Sync strategy:** Hybrid — cron jobs every 15 min for stock/price, webhooks for critical events.
- **Retry mechanism:** Exponential backoff with dead-letter queue for failed supplier API calls.
- **Supplier abstracti