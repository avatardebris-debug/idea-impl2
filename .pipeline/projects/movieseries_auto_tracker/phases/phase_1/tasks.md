# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package skeleton with proper module layout, __init__.py, and setup.py so the project is importable.
  - Files: setup.py, movieseries_tracker/__init__.py, movieseries_tracker/models.py, movieseries_tracker/search.py, movieseries_tracker/watchlist.py, movieseries_tracker/cli.py, movieseries_tracker/services.py
  - Done when: `pip install -e .` succeeds and `import movieseries_tracker` works without errors.

- [ ] Task 2: Core data models
  - What: Define data classes for Title (movie/series), Episode, StreamingService, and WatchlistEntry. Include fields for title, type, year, streaming platforms, seasons/episodes, and watch progress.
  - Files: movieseries_tracker/models.py
  - Done when: All data classes are defined with proper fields and can be instantiated and serialized to/from dict/JSON.

- [ ] Task 3: Streaming search service
  - What: Implement a search module that queries a mock/streaming data source for titles across platforms (Netflix, Hulu, Prime, Disney+, free options). Supports search by title and filters by type (movie/series) and availability.
  - Files: movieseries_tracker/search.py, movieseries_tracker/services.py
  - Done when: Can search for a title string and return matching results with streaming platform info; can filter by type and availability.

- [ ] Task 4: Watchlist and continue-watching feature
  - What: Implement a watchlist module that lets users add/remove titles, track watch progress (season/episode), and retrieve a "continue watching" list with last-watched position. Persist data to a local JSON file.
  - Files: movieseries_tracker/watchlist.py
  - Done when: Can add a title to watchlist, mark progress, retrieve continue-watching list, and persist/reload from JSON.

- [ ] Task 5: CLI interface
  - What: Build a command-line interface with commands: search <query>, watchlist (list), add <title>, remove <title>, continue (show what to watch next), and details <title>.
  - Files: movieseries_tracker/cli.py
  - Done when: All CLI commands execute and display output correctly; `python -m movieseries_tracker` launches the CLI.