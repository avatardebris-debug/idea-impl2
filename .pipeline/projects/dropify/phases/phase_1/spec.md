## Phase 1 — MVP: Single-Store Store Builder + Checkout

> **Goal:** Prove the core loop — a user can create a store, add products, and accept their first order.

### Description

Build the foundational store builder that allows a single user to:
- Create and customize a basic online store (theme, branding, pages)
- Add products manually or via CSV import
- Configure a storefront with product listings, product detail pages, and cart
- Accept payments via Stripe and place orders

This is the smallest useful thing: a functional single-tenant store with a working checkout.

### Deliverables

1. **User Authentication**
   - Sign up / login / password reset
   - Basic profile management
   - JWT-based session management

2. **Store Creation & Management**
   - Create a store with a custom subdomain (e.g., `mystore.dropify.app`)
   - Basic store settings (name, logo, currency, timezone)
   - Store status toggle (active/draft)

3. **Product Management**
   - CRUD for products (name, description, price, images, inventory count)
   - Product categories/tags
   - CSV import for bulk product upload
   - Product variants (size, color, etc.)

4. **Storefront Engine**
   - Pre-built "Essentials" theme (minimal, responsive)
   - Dynamic storefront at `{store}.dropify.app`
   - Product listing page, product detail page
   - Shopping cart (client-side state + localStorage)
   - Checkout page with Stripe Elements integration
   - Order confirmation page

5. **Order Management (Basic)**
   - View orders in admin panel
   - Order status tracking (pending → paid → fulfilled → shipped)
   - Basic order details (items, totals, customer info)

### Dependencies

- **None** — This is the first phase. Foundation only.

### Success Criteria

| Criterion | Metric |
|-----------|--------|
| Store creation | User can create a store in < 2 minutes |
| Product import | User can add 10 products in < 5 minutes |
| Checkout flow | Complete a purchase end-to-end (storefront → cart → checkout → payment → confirmation) |
| Performance | Storefront LCP < 2.5s on 4G connection |
| Reliability | 99.5% uptime for MVP phase |
| Data integrity | No orphaned orders or payment mismatches |

### Key Technical Decisions

- **Multi-tenancy approach:** Row-level security in PostgreSQL with `tenant_id` on every table. Each store is a tenant.
- **Storefront routing:** DNS wildcard (`*.dropify.app`) → route to tenant store. Fallback: `dropify.app/s/{store-slug}`.
- **Cart strategy:** Client-side cart with localStorage, synced to server on checkout.
- **Payment flow:** Stripe Checkout (hosted) for simplicity in MVP. Redirect-based flow.

---