# Master Ideas List

Ideas are processed top-to-bottom. The pipeline picks the first unchecked `[ ]` item.

## Format
`- [ ] **Title** — Description of what to build`

## Ideas

## Auto-Generated — 20260504_192327

---

### GROUP 1 — SIMILAR (niche analogues to existing projects)

- [ ] **Financial document analyzer** — Build a Python CLI that reads financial PDFs and CSVs, extracts key metrics (revenue, margins, ratios), and prints structured summary reports with trend analysis. requires: csv_analyzer
- [ ] **Invoice processor** — Tool that scans email attachments for invoices, extracts line items and totals via OCR or text parsing, and organizes them into a searchable ledger with CSV export. requires: email_tool
- [ ] **Resume and cover letter builder** — Python tool that takes a job description and candidate profile, then generates tailored resumes and cover letters using templating and LLM-assisted rewriting. requires: drop_servicing_tool
- [ ] **Real estate listing analyzer** — CLI tool that pulls property data from public APIs, analyzes price trends, neighborhood metrics, and generates comparative market reports in CSV or PDF. requires: Zillow
- [ ] **Contract clause extractor** — PDF and DOCX parser that identifies and extracts key contract clauses (termination, liability, NDAs) into a structured searchable database with export options.

### GROUP 2 — EXPANSION (new major features for existing projects)

- [ ] **Multi-table poker trainer** — Extend advantage player cardgame simulator to handle multi-table poker simulation with opponent modeling and bankroll tracking across sessions. requires: advantage_player_cardgame_simulator_training
- [ ] **Card composition calculator** — Add a deck composition analyzer to the cardgame simulator that calculates card counting advantage, true count, and running count across shuffle patterns. requires: advantage_player_cardgame_simulator_training
- [ ] **Book content repurposer** — Add a module to the AI author suite that takes a completed book and auto-generates blog posts, social media threads, newsletter articles, and course outlines from chapters. requires: ai_author_suite
- [ ] **CSV data pipeline builder** — Extend CSV analyzer with a visual pipeline builder that chains transformations (filter, join, pivot, aggregate) between multiple CSV files with export to SQL or JSON. requires: csv_analyzer
- [ ] **SOP marketplace** — Add a marketplace module to the drop servicing tool where users can publish, discover, and license SOPs with version control, ratings, and one-click import. requires: drop_servicing_tool

### GROUP 3 — INDEPENDENT (unrelated to existing work)

- [ ] **Local weather dashboard CLI** — Python CLI that fetches local weather data from OpenWeatherMap, displays current conditions and 7-day forecast in terminal with color-coded alerts for severe weather.
- [ ] **Meeting notes auto-summarizer** — Tool that takes raw meeting transcripts or audio recordings, identifies action items, decisions, and key topics, and outputs a structured summary with assignees and deadlines.
- [ ] **Personal finance tracker CLI** — Python CLI that imports bank CSV transactions, categorizes them by merchant patterns, generates monthly budget reports, and alerts on spending anomalies.
- [ ] **API mock server generator** — Tool that reads an OpenAPI/Swagger spec and generates a fully functional mock API server with configurable response delays, random data generation, and request logging.
- [ ] **Code review diff summarizer** — CLI tool that reads git diff output, summarizes changes by file and function, flags potential issues, and generates a human-readable review briefing.

### GROUP 4 — COMBINATION (merge 2+ existing projects)

- [ ] **Automated SEO content factory** — Combines ai_author_suite with dropship/service/ecommerce autoSEO autometa to generate SEO-optimized product descriptions and blog content at scale for ecommerce stores. requires: ai_author_suite, dropship/service/ecommerce. autoSEO autometa
- [ ] **Smart email-to-SOP executor** — Combines email_tool with drop_servicing_tool to automatically parse incoming emails, extract task requirements, and trigger SOP-based agentic workflows for execution. requires: email_tool, drop_servicing_tool
- [ ] **Card game training course platform** — Combines advantage_player_cardgame_simulator_training with tim ferriss learning tool to create interactive poker and blackjack training courses with spaced repetition and progress tracking. requires: advantage_player_cardgame_simulator_training, tim ferriss learning tool
- [ ] **Resume-to-job-applicant automator** — Combines drop_servicing_tool with fiverr job automation tool to analyze job listings, auto-generate tailored applications, and manage bulk outreach campaigns. requires: drop_servicing_tool, fiverr job automation tool
- [ ] **Video content SEO engine** — Combines dropship/service/ecommerce autoSEO autometa with youtube workflow tool to generate SEO titles, descriptions, tags, and transcripts for YouTube video catalogs at scale. requires: dropship/service/ecommerce. autoSEO autometa, youtube workflow tool

### GROUP 5 — BRIDGE (connectors and integrations)

- [ ] **CSV-to-SOP data mapper** — Bridge that reads CSV data and maps it to SOPInput schema fields for the drop servicing tool, enabling bulk data-driven SOP execution pipelines. requires: csv_analyzer, drop_servicing_tool
- [ ] **LLMClient bridge for AI Author** — Adapter that plugs the LLMClient protocol from drop_servicing_tool into the AI author suite so all modules share the same LLM interface and caching layer. requires: drop_servicing_tool, ai_author_suite
- [ ] **Cardgame simulator output to learning tool** — Bridge that exports Monte Carlo training results and strategy metrics from the cardgame simulator into the tim ferriss learning tool format for spaced repetition practice decks. requires: advantage_player_cardgame_simulator_training, tim ferriss learning tool
- [ ] **Email attachment to CSV pipeline** — Connector that extracts CSV attachments from emails processed by the email tool, runs them through the CSV analyzer, and routes results to a configured folder or webhook. requires: email_tool, csv_analyzer
- [ ] **SOP output to YouTube content feed** — Bridge that takes SOPStep outputs from the drop servicing tool and formats them into YouTube video scripts, titles, and thumbnail text via the youtube workflow tool pipeline. requires: drop_servicing_tool, youtube workflow tool

### GROUP 6 — HARNESS (pipeline/toolkit improvements)

- [ ] **Agent observability dashboard** — Build a real-time dashboard that tracks agent execution metrics (steps taken, LLM calls, costs, errors, duration) across all running pipeline projects with alerting on anomalies.
- [ ] **Shared LLM cost tracker** — Add a cost-tracking middleware to the LLMClient protocol that logs every LLM call's token usage and cost across all projects, with monthly budget alerts and per-project breakdowns.
- [ ] **Test fixture generator** — Build a tool that generates realistic test fixtures (CSV files, JSON payloads, mock API responses, sample documents) for any project by reading its existing test patterns and schemas.
- [ ] **Project dependency graph visualizer** — Tool that reads all project workspace files and MANIFEST.json to generate a visual dependency graph showing which projects depend on which shared tools and ideas.
- [ ] **Cross-project code linter** — CLI tool that runs consistent linting, type checking, and import analysis across all workspace projects, enforcing a shared style guide and flagging cross-project API mismatches.


