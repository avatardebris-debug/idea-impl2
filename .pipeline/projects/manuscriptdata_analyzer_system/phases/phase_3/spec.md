# Phase 3 Specification: Multi-Platform Support & Production Polish

## 1. Overview
In Phase 3, the ManuscriptData Analyzer transforms into a production-ready application for authors. It introduces automated format detection for major publishing platforms, canonical data normalization, interactive CLI session management, and aggregated cross-platform reporting.

## 2. Core Features

### 2.1 Multi-Platform Parsers & Normalization
- Expand `csv_parser.py` (or create a `parsers/` package) with dedicated strategies for:
  - **Amazon KDP** (Kindle Direct Publishing)
  - **Kobo Writing Life**
  - **Apple Books for Authors**
  - **Barnes & Noble Press**
- Implement an automated sniffer to detect the platform from CSV headers.
- Normalize incoming data into a canonical schema so analytics can aggregate seamlessly across multiple storefronts.

### 2.2 Cross-Platform Analytics
- Upgrade the `analytics.py` engine to support grouped reporting by platform, as well as aggregated cross-platform totals (e.g., total sales of "Book A" across Amazon + Kobo).

### 2.3 Interactive CLI Dashboard
- Create an interactive dashboard (e.g., using `cmd` or `prompt_toolkit`) accessible via `manuscriptdata-analyzer dashboard`.
- Support interactive commands like `list books`, `view report <book_id>`, and `export`.

### 2.4 JSON Export
- Enhance the export functionality to support robust JSON dumping of all database state and analytics results, suitable for ingestion into BI tools.

## 3. Success Criteria
- [ ] Tool correctly auto-detects and parses KDP, Kobo, Apple, and B&N CSVs.
- [ ] Database correctly stores the `platform` and aggregates them accurately in the reporting engine.
- [ ] Interactive `dashboard` command works and maintains a session state.
- [ ] Reports can be exported as JSON via the CLI.
