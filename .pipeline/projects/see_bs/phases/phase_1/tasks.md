# Phase 1 Tasks

- [x] Task 1: Project scaffolding and package structure
  - What: Create the Python package layout for `see_bs` with proper `__init__.py` and module organization
  - Files: `see_bs/__init__.py`, `see_bs/models.py`, `see_bs/engine.py`, `see_bs/filters.py`, `see_bs/__main__.py`
  - Done when: Package is importable (`import see_bs` works), package has a `__version__` and exposes a top-level `filter_news` function

- [x] Task 2: News article data model
  - What: Define the `NewsArticle` dataclass/Pydantic model with fields for title, content, source, author, date, and metadata needed for BS analysis
  - Files: `see_bs/models.py`
  - Done when: `NewsArticle` can be instantiated with required fields, supports serialization (to_dict/from_dict), and all BS-relevant fields (source, author, outlet_bias, claim_type, evidence_level) are present

- [x] Task 3: BS detection filters — Scott Adams techniques
  - What: Implement the core BS detection logic as composable filter functions:
    - Scott Alexander rule: flag claims that would be embarrassing if the opposite were true
    - Gellman Amnesia: simulate how the same story would read if from the opposing viewpoint
    - Reporter identity analysis: weight credibility based on who is reporting (source outlet, author track record)
    - Incentive alignment check: flag stories where the reporter/outlet has a conflict of interest
  - Files: `see_bs/filters.py`
  - Done when: Each filter is a standalone function `filter_<name>(article) -> dict` returning a score and explanation; all filters can be called on a sample article without errors

- [x] Task 4: Scoring engine and aggregation
  - What: Build the engine that runs all filters on an article, aggregates scores into a composite BS score (0–100), and produces a readable breakdown
  - Files: `see_bs/engine.py`
  - Done when: `ScoreEngine.analyze(article) -> AnalysisResult` returns a BS score, per-filter breakdown, and summary text; works with a sample article

- [x] Task 5: Public API and demo
  - What: Wire the public API (`see_bs.filter_news()`) and a minimal CLI/demo that processes sample articles and prints results
  - Files: `see_bs/__init__.py`, `see_bs/__main__.py`
  - Done when: `from see_bs import filter_news` works and returns structured results; `python -m see_bs` runs a demo with built-in sample articles and prints a readable BS report