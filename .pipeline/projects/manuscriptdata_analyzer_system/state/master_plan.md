# Master Plan: ManuscriptData Analyzer System

## Goal
Merge the AI Author Suite with the CSV Analyzer to build a CLI tool that ingests CSV data (sales reports, reader demographics, content metrics) from book sales platforms, stores it in a SQLite database, and generates performance analytics and reports across published books.

## Phase 1: Data Ingestion Engine — Foundation
- **Description**: Build the core data ingestion pipeline — a CSV parser that handles book sales and demographics data formats, a SQLite schema for storing manuscript analytics, and a CLI interface for importing data and viewing basic summaries. This is a complete, working tool: you can import CSV files and get summary statistics on your own.
- **Deliverable**: A working CLI tool (`manuscriptdata_analyzer`) with commands for importing CSV files (sales, demographics, content metrics), storing them in SQLite, and displaying basic summary reports.
- **Dependencies**: none
- **Success criteria**:
  - CLI tool installs and runs with `--help` showing available commands
  - CSV parser auto-detects and imports sales data (columns: Date, Book Title, Units Sold, Revenue, Platform)
  - CSV parser auto-detects and imports demographics data (columns: Age Group, Gender, Country, Rating, Review Count)
  - CSV parser auto-detects and imports content metrics (columns: Chapter, Word Count, Read-Through Rate, Completion Rate)
  - SQLite database stores all imported data with proper schema and indexes
  - CLI `summary` command outputs formatted summary statistics (total sales, avg revenue, demographic breakdown)
  - Unit tests with fixture CSV files for all three data types pass

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

## Phase 3: Multi-Platform Support — Production Polish
- **Description**: Add platform-specific CSV format detection (Amazon KDP, Kobo Writing Life, Apple Books for Authors, Barnes & Noble Press), automated data normalization across platforms, and a CLI dashboard for interactive session management. This makes the tool production-ready for authors publishing across multiple platforms.
- **Deliverable**: Platform-specific parsers for 4 major book sales platforms, data normalization layer, and an interactive CLI dashboard with session management.
- **Dependencies**: Phase 1 (data ingestion engine, database schema), Phase 2 (analytics engine, report generation)
- **Success criteria**:
  - Platform-specific CSV parsers for Amazon KDP, Kobo, Apple Books, and Barnes & Noble Press
  - Data normalization layer maps all platform formats to the canonical schema
  - CLI dashboard supports interactive session management (list books, view reports, export data)
  - Cross-platform aggregated reports combine data from multiple platforms into unified views
  - Export to CSV/JSON for external analysis tools
  - Integration tests with real-world CSV samples from each platform pass

## Architecture Notes

### Data Model
The system uses a SQLite database with three core tables:
- **books**: Canonical book metadata (title, ISBN, author, publication_date, genre, cover_url)
- **sales_data**: Time-series sales records (book_id, date, platform, units_sold, revenue, currency, royalty_rate)
- **demographics_data**: Reader demographic snapshots (book_id, date, age_group, gender, country, avg_rating, review_count, read_through_rate)

### Design Decisions
- **SQLite over external DB**: Local-first, zero-config, matches the existing BudgetFlow Tracker pattern. Authors don't need a running database server.
- **CSV-first ingestion**: All data comes from CSV exports of sales platforms. No API integrations in scope — this keeps the tool simple and platform-agnostic.
- **Canonical schema**: Platform-specific CSVs are normalized into a unified schema during import, enabling cross-platform analysis.
- **CLI-first interface**: Follows the existing project conventions (BudgetFlow Tracker, CSV Analyzer). No web UI or GUI — pure CLI tool.
- **Modular parser architecture**: Each platform format has its own parser class implementing a common `PlatformParser` interface, enabling easy addition of new platforms.

### Reuse from Existing Code
- `src/core/database.py` — SQLite wrapper (Database class, connection management, transactions)
- `src/import/csv_parser.py` — CSV parsing patterns (format detection, column mapping, data type handling)
- `src/reports/generator.py` — Report generation patterns (formatted text output, CSV export)
- `src/ui/cli_dashboard.py` — CLI command routing and display patterns

### Tech Stack
- Python 3.10+
- SQLite3 (stdlib)
- argparse (stdlib)
- csv, datetime, collections (stdlib)
- pytest for testing

## Risks

1. **CSV format variability**: Sales platform CSVs change frequently and differ significantly between platforms. Mitigation: start with the 4 major platforms, use flexible column detection, and make the parser extensible for future formats.
2. **Data quality issues**: CSV exports may have missing values, inconsistent date formats, or encoding issues. Mitigation: robust error handling, data cleaning in the parser, and clear error messages to the user.
3. **Scope creep**: The AI Author Suite integration could tempt expanding into content analysis, keyword research, or cover design. Mitigation: strictly limit to data analysis — the tool ingests and analyzes CSV data, it does not generate content.
4. **Large dataset performance**: Authors with many books and years of data could hit SQLite performance limits. Mitigation: proper indexing on date and book_id columns; if needed, add pagination to queries in Phase 2.
5. **Currency conversion**: Multi-platform sales involve multiple currencies. Mitigation: Phase 1 stores raw currency data; Phase 2 adds optional currency conversion with a configurable exchange rate.
