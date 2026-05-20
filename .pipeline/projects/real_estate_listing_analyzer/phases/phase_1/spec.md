## Phase 1 — Core Data Fetching & Parsing
- Implement `DataFetcher` class with adapters for:
  - Zillow RapidAPI (property details, Zestimate, price history)
  - HUD Fair Market Rents API (neighborhood affordability baseline)
  - US Census ACS API (population, median income, school district)
- Implement `ListingParser` to normalize raw API responses into `Listing` dataclasses
- CLI entrypoint: `real-estate-analyzer fetch --zip 90210 --count 50`
- Output: raw JSON cache in `~/.real_estate_cache/`
- Tests: mock API responses, schema validation

