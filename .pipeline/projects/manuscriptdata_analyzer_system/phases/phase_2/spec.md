## Phase 2: Analytics Engine — Performance Insights
- **Description**: Build the analytics layer on top of the Phase 1 data store. Add trend analysis, multi-book comparison, demographic deep-dives, and formatted report generation. This turns raw imported data into actionable publishing insights.
- **Deliverable**: Analytics engine with trend detection, cross-book comparison, demographic profiling, and multi-format report generation (text, CSV export).
- **Dependencies**: Phase 1 (data ingestion engine, database schema, CLI foundation)
- **Success criteria**:
  - Trend analysis calculates rolling averages and detects sales spikes/drops per book
  - Multi-book comparison ranks books by revenue, units sold, and reader engagement
  - Demographic profiler generates age/gender/country breakdowns with percentage distributions
  - Report generator produces formatted text reports and CSV exports of analytics
  - CLI `analyze` command outputs comprehensive performance report
  - CLI `compare` command outputs side-by-side book comparison
  - Unit tests for analytics engine pass with fixture data

