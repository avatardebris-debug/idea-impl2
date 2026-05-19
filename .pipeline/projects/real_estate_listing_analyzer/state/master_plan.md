# Real Estate Listing Analyzer — Master Plan

## Overview
CLI tool that fetches property listings from public/free APIs (Zillow RapidAPI,
Redfin public endpoints, HUD data), analyzes price trends and neighborhood
metrics, and generates comparative market analysis (CMA) reports in CSV or PDF.

## Phase 1 — Core Data Fetching & Parsing
- Implement `DataFetcher` class with adapters for:
  - Zillow RapidAPI (property details, Zestimate, price history)
  - HUD Fair Market Rents API (neighborhood affordability baseline)
  - US Census ACS API (population, median income, school district)
- Implement `ListingParser` to normalize raw API responses into `Listing` dataclasses
- CLI entrypoint: `real-estate-analyzer fetch --zip 90210 --count 50`
- Output: raw JSON cache in `~/.real_estate_cache/`
- Tests: mock API responses, schema validation

## Phase 2 — Price Trend Analysis & Scoring
- Implement `TrendAnalyzer`:
  - 30/90/365-day price-per-sqft trend (slope via linear regression)
  - Days-on-market median and standard deviation
  - List-to-sale price ratio
  - Neighborhood score (0-100) combining income, schools, crime index)
- Implement `ComparablesFinder`: k-NN similarity on sqft, beds, baths, zip
- CLI: `real-estate-analyzer analyze --zip 90210 --beds 3 --budget 800000`
- Tests: synthetic listing data, regression assertions

## Phase 3 — Report Generation (CSV + PDF)
- Implement `ReportBuilder`:
  - CSV export: one row per listing with all computed metrics
  - PDF export: CMA summary page + price trend chart (matplotlib)
  - Markdown export: ranked listing table with neighborhood highlights
- CLI: `real-estate-analyzer report --format pdf --out ./report.pdf`
- Implement `AlertEngine`: flag listings with >5% below-trend price as deals
- Tests: golden-file CSV comparison, PDF byte-size sanity check
