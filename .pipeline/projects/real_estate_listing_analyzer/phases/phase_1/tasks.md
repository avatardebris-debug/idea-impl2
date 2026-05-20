# Phase 1 Tasks

- [x] Task 1: Implement the `DataFetcher` class with Zillow adapter
  - What: Complete the `DataFetcher` class in `fetcher.py` with a `ZillowAdapter` that fetches listings by ZIP code using the RapidAPI Zillow endpoint, parses the response, and returns a list of `Listing` objects.
  - Files: `real_estate_listing_analyzer/fetcher.py`
  - Done when: `DataFetcher.fetch_listings(zip_code, count=20)` returns a list of `Listing` objects with populated `zpid`, `address`, `city`, `state`, `price`, `beds`, `baths`, `sqft`, and `url` fields from the Zillow API response.

- [x] Task 2: Implement cache management for fetched listings
  - What: Add `save_cache(listings: list[Listing], zip_code: str) -> pathlib.Path` and `load_latest_cache(zip_code: str) -> list[Listing] | None` functions to `fetcher.py`. Cache should store listings as JSON in `~/.real_estate_cache/<zip_code>.json` with a TTL of 24 hours.
  - Files: `real_estate_listing_analyzer/fetcher.py`
  - Done when: `save_cache` writes valid JSON with timestamp, `load_latest_cache` returns listings if cache exists and is < 24h old, otherwise returns `None`.

- [x] Task 3: Implement the CLI `fetch` command
  - What: Complete the `_fetcher` function in `cli.py` to wire up the `fetch` subcommand. It should accept `--zip` and `--count` arguments, call `DataFetcher.fetch_listings()`, save to cache, and print a summary (count, median price, address range).
  - Files: `real_estate_listing_analyzer/cli.py`
  - Done when: Running `real-estate-analyzer fetch --zip 90210 --count 10` prints a formatted summary with listing count, median price, and address range without errors.

- [x] Task 4: Write unit tests for fetcher (cache and parsing)
  - What: Add tests in `tests/test_fetcher.py` for cache save/load (including TTL expiry), `Listing` dataclass, and a mock-based test for `DataFetcher.fetch_listings` that patches the HTTP call and verifies parsing.
  - Files: `tests/test_fetcher.py`
  - Done when: All new tests pass with `pytest tests/test_fetcher.py -v` and achieve 100% coverage on the cache and parsing logic.

- [x] Task 5: Write integration test for CLI fetch command
  - What: Add a test in `tests/test_fetcher.py` (or a new `tests/test_cli.py`) that patches `DataFetcher.fetch_listings` and verifies the CLI `fetch` command prints the expected summary output.
  - Files: `tests/test_fetcher.py` (or `tests/test_cli.py`)
  - Done when: The integration test passes, confirming the CLI fetch command correctly calls the fetcher and outputs the summary.