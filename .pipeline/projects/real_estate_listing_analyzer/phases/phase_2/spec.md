## Phase 2 — Price Trend Analysis & Scoring
- Implement `TrendAnalyzer`:
  - 30/90/365-day price-per-sqft trend (slope via linear regression)
  - Days-on-market median and standard deviation
  - List-to-sale price ratio
  - Neighborhood score (0-100) combining income, schools, crime index)
- Implement `ComparablesFinder`: k-NN similarity on sqft, beds, baths, zip
- CLI: `real-estate-analyzer analyze --zip 90210 --beds 3 --budget 800000`
- Tests: synthetic listing data, regression assertions

