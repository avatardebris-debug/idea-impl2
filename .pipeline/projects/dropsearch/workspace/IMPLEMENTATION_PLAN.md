# Implementation Plan: Multi-Store Competitor Analysis

## Overview
Build a system that scrapes competitor stores, detects supplier chains, analyzes product overlaps and price gaps, estimates profit margins, and generates actionable insights.

## Files to Create

### 1. `src/models/product.py`
- **Purpose**: Pydantic model for a scraped product
- **Fields**: name, price, description, image_url, url

### 2. `src/models/store_analysis.py`
- **Purpose**: Pydantic models for analysis results
- **Models**: ProductMatch, SupplierChain, StoreAnalysis, CompetitorComparison

### 3. `src/scraper/parsers/shopify.py`
- **Purpose**: Extract products from Shopify stores
- **Methods**: is_shopify(html), extract(html, base_url)
- **Approach**: JSON-LD parsing + CSS selector fallback

### 4. `src/scraper/parsers/woocommerce.py`
- **Purpose**: Extract products from WooCommerce stores
- **Methods**: is_woocommerce(html), extract(html, base_url)
- **Approach**: JSON-LD parsing + CSS selector fallback

### 5. `src/scraper/supplier_detector.py`
- **Purpose**: Detect supplier chains in HTML
- **Methods**: detect(html, base_url)
- **Approach**: Regex patterns for known supplier domains, prices, iframes

### 6. `src/analysis/overlap_detector.py`
- **Purpose**: Find matching products across stores
- **Methods**: detect_overlaps(stores)
- **Approach**: Fuzzy matching with rapidfuzz

### 7. `src/analysis/margin_analyzer.py`
- **Purpose**: Estimate profit margins
- **Methods**: analyze(stores)
- **Approach**: Industry-standard cost multipliers per supplier

### 8. `src/analysis/competitor_analyzer.py`
- **Purpose**: Main orchestrator for all analysis
- **Methods**: analyze_stores(stores) -> CompetitorComparison
- **Approach**: Coordinates overlap detection, margin analysis, and insight generation

## Implementation Order
1. Models (product.py, store_analysis.py)
2. Parsers (shopify.py, woocommerce.py)
3. Supplier detector (supplier_detector.py)
4. Analysis components (overlap_detector.py, margin_analyzer.py)
5. Main analyzer (competitor_analyzer.py)

## Key Design Decisions
- Use Pydantic for type safety
- Fuzzy matching for product overlap detection
- Confidence scores for supplier detection
- Modular components for each analysis type
