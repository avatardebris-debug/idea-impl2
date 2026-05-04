# Phase 1 Tasks

- [ ] Task 1: Project setup and directory structure
  - What: Create the project skeleton with pyproject.toml, requirements.txt, and package layout for the SEO tool CLI
  - Files: pyproject.toml, requirements.txt, seo_tool/__init__.py, seo_tool/cli.py, seo_tool/analyzer.py, seo_tool/scorer.py, seo_tool/models.py, tests/__init__.py
  - Done when: pyproject.toml is valid and `pip install -e .` succeeds; package imports work; requirements.txt lists dependencies (requests, beautifulsoup4, lxml, click)

- [ ] Task 2: Data models and metadata extraction
  - What: Implement the core data model (SEOReport) and the HTML parsing logic that fetches a URL and extracts SEO-relevant metadata (title, meta description, meta keywords, H1-H6 headings, images with alt text, canonical link, Open Graph tags, word count, link count, internal vs external links)
  - Files: seo_tool/models.py, seo_tool/analyzer.py
  - Done when: Analyzer.fetch_and_parse(url) returns an SEOReport with all fields populated; handles missing tags gracefully (defaults to empty/None); handles HTTP errors with a clear exception

- [ ] Task 3: SEO scoring engine
  - What: Implement the scoring logic that evaluates an SEOReport against common SEO best practices and produces a numeric score (0-100) with category breakdowns (title, meta_description, headings, images, links, content_length, og_tags)
  - Files: seo_tool/scorer.py
  - Done when: Scorer.score(report) returns a dict with total_score (0-100) and category_scores; title score = 10 if present and length 30-60 chars else 0; meta_description score = 10 if present and length 120-160 chars else 0; each category weighted to sum to 100; clear pass/fail reasons per category

- [ ] Task 4: CLI entry point with output formatting
  - What: Implement the CLI using click that accepts a URL, runs the analyzer and scorer, and prints a formatted SEO report (score, category breakdown, issues/warnings)
  - Files: seo_tool/cli.py
  - Done when: `seo-tool https://example.com` prints a readable report with total score, category scores, and actionable issues; supports --json flag for machine-readable output; supports --output FILE to write report to file; returns exit code 0 on success, non-zero on error

- [ ] Task 5: Unit tests for Phase 1
  - What: Write comprehensive tests covering the analyzer (with mocked HTTP responses), scorer (with crafted SEOReport objects), and CLI (with click CliRunner)
  - Files: tests/test_analyzer.py, tests/test_scorer.py, tests/test_cli.py
  - Done when: All tests pass with `pytest`; analyzer tests cover valid HTML, missing tags, and HTTP errors; scorer tests cover edge cases (empty report, max-length fields, boundary values); CLI tests cover --json and --output flags; test coverage >= 80%