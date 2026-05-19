# DropStore Implementation Plan

## Overview
DropStore is a full-stack dropshipping automation platform that helps users discover profitable niches, find products, build catalogs, and sync them to Shopify stores.

## Architecture
- **Backend**: FastAPI with SQLAlchemy async, SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Single HTML file with vanilla JavaScript and CSS
- **Database**: SQLite for development, PostgreSQL for production
- **Testing**: pytest with async support

## Project Structure
```
workspace/
├── backend/
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   └── product.py      # SQLAlchemy models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── niche_service.py
│   │   ├── catalog_service.py
│   │   └── shopify_service.py
│   └── utils/
│       ├── __init__.py
│       └── database.py
├── shared/
│   ├── __init__.py
│   └── schemas.py          # Pydantic schemas
├── frontend/
│   ├── index.html          # Single-page application
│   └── src/
│       └── types/
│           └── dropstore.ts
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_niche_service.py
│   ├── test_catalog_service.py
│   └── test_shopify_service.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Implementation Steps

### Phase 1: Database Models and Utilities
1. Create `backend/utils/database.py` - Database engine and session setup
2. Create `backend/models/product.py` - SQLAlchemy models for Niche, Product, Catalog, etc.

### Phase 2: Core Services
3. Create `backend/services/niche_service.py` - Niche discovery and scoring
4. Create `backend/services/catalog_service.py` - Catalog management
5. Create `backend/services/shopify_service.py` - Shopify integration

### Phase 3: API Layer
6. Create `backend/app.py` - FastAPI application with all endpoints

### Phase 4: Frontend
7. Update `frontend/index.html` - Complete single-page application
8. Update `frontend/src/types/dropstore.ts` - TypeScript types

### Phase 5: Testing
9. Create `tests/conftest.py` - Test fixtures
10. Create test files for each service

### Phase 6: Configuration
11. Create `requirements.txt`
12. Create `docker-compose.yml`
13. Create `Dockerfile`
14. Create `README.md`

## Key Features
- Niche discovery with demand/supply scoring
- Product suggestions with margin calculations
- Catalog management
- Shopify store connection and product sync
- Responsive web interface
