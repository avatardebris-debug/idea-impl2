# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and shared configuration
  - What: Initialize the full-stack project with FastAPI backend and Next.js frontend, set up directory structure, environment config, database schema, and shared types.
  - Files: Create `backend/` (FastAPI app, main.py, config.py, models/, schemas/, routers/, services/, utils/), `frontend/` (Next.js app with Tailwind), `shared/` (Pydantic schemas, TypeScript types), `docker-compose.yml` (PostgreSQL + Redis), `env.example`, `requirements.txt`, `package.json`
  - Done when: Project boots locally with `docker-compose up`, FastAPI serves on /docs, Next.js dev server runs, database and Redis containers are healthy, and shared Pydantic/TypeScript schemas are importable from both sides.

- [ ] Task 2: Niche Discovery Module
  - What: Build the niche finder with curated niche categories, demand/supply scoring, and a product suggestion engine that returns 20+ products per niche with margin data.
  - Files: `backend/services/niche_service.py`, `backend/services/product_finder.py`, `backend/routers/niches.py`, `backend/routers/products.py`, `frontend/app/niche/page.tsx`, `frontend/components/NicheSelector.tsx`, `frontend/components/ProductCard.tsx`, `shared/schemas.py`, `shared/types.ts`
  - Done when: A user selects a niche and receives 20+ product suggestions, each with title, image URL, estimated cost, suggested retail price, and margin percentage. The scoring data is sourced from public APIs (e.g., Google Trends, Amazon Best Sellers) or seeded mock data that mirrors real scoring logic.

- [ ] Task 3: Product Catalog Builder
  - What: Build the catalog builder that lets users filter, sort, and curate products into a catalog. Includes margin estimation, image/title optimization, and variant handling.
  - Files: `backend/services/catalog_service.py`, `backend/routers/catalog.py`, `backend/models/product.py`, `frontend/app/catalog/page.tsx`, `frontend/components/CatalogBuilder.tsx`, `frontend/components/ProductFilters.tsx`, `shared/schemas.py`
  - Done when: Users can filter products by margin range, price, and category; sort by margin or cost; add/remove products to/from a catalog; and see an optimized title/image for each product. The catalog persists to the database and can be retrieved and edited.

- [ ] Task 4: Shopify OAuth and Store Connection
  - What: Implement Shopify OAuth 2.0 flow so users can connect their Shopify store. Store OAuth tokens securely and verify the connection.
  - Files: `backend/services/shopify_service.py`, `backend/routers/shopify.py`, `backend/models/store.py`, `frontend/app/connect/page.tsx`, `frontend/components/ShopifyConnect.tsx`, `shared/schemas.py`
  - Done when: A user clicks "Connect Shopify Store," is redirected to Shopify's OAuth consent screen, returns with an access token, and sees their store name and status on the dashboard. Tokens are encrypted and stored in the database.

- [ ] Task 5: Shopify Sync Engine
  - What: Build the one-click product push engine that syncs catalog products to the connected Shopify store via Shopify Admin REST API. Handles product creation with title, description, images, price, and variants.
  - Files: `backend/services/sync_service.py`, `backend/routers/sync.py`, `backend/models/product.py`, `backend/models/store.py`, `frontend/app/sync/page.tsx`, `frontend/components/SyncButton.tsx`, `frontend/components/SyncStatus.tsx`, `shared/schemas.py`
  - Done when: A user can push 10+ products from their catalog to their Shopify store with one click. Products appear in Shopify with correct title, image, price, and variants. Sync status (pending, success, failed) is visible in the dashboard. Failed pushes include error messages.

- [ ] Task 6: Dashboard and End-to-End Integration
  - What: Build the basic dashboard that shows synced products, margins, store status, and sync history. Wire all modules together into a cohesive end-to-end flow.
  - Files: `frontend/app/dashboard/page.tsx`, `frontend/components/DashboardOverview.tsx`, `frontend/components/ProductTable.tsx`, `frontend/components/StoreStatusCard.tsx`, `frontend/components/SyncHistory.tsx`, `backend/routers/dashboard.py`, `backend/services/dashboard_service.py`, `shared/schemas.py`
  - Done when: A user can complete the full flow — select a niche, browse 20+ products, build a catalog, connect a Shopify store, push 10+ products, and see sync status and product list on the dashboard — in under 5 minutes. All success criteria from the Phase 1 spec are met.