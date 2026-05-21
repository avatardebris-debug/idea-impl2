# Phase 1 Tasks

- [x] Task 1: Project scaffolding and core data models
  - What: Create the project directory structure, package setup, and core data models (BookReview, Gap, NicheProfile, TableOfContents). Define the data structures that represent reviews, identified gaps, niches, and the final TOC output.
  - Files: book_researcher/__init__.py, book_researcher/models.py, pyproject.toml
  - Done when: Package is importable (`from book_researcher.models import BookReview, Gap, NicheProfile, TableOfContents` works), data models have proper fields and type hints, pyproject.toml defines the package metadata.

- [x] Task 2: Review aggregator module
  - What: Build a module that can fetch and parse reviews from top-selling information books. Implement a generic ReviewAggregator interface with a concrete Amazon/Goodreads-style scraper (simulated with sample data for MVP). Include a method to extract "wish it also did X / didn't explain Y" style complaints from reviews.
  - Files: book_researcher/aggregator.py, book_researcher/aggregators/__init__.py, book_researcher/aggregators/sample_reviews.py
  - Done when: `ReviewAggregator.fetch_reviews(book_id)` returns a list of review dicts with text, rating, and source fields. Sample data module provides realistic mock reviews containing gap-indicating phrases.

- [x] Task 3: Gap extraction engine
  - What: Implement the core logic that identifies content gaps from reviews. Use keyword/phrase matching (e.g., "wish", "want", "lacks", "didn't explain", "missing", "should have covered") combined with simple NLP heuristics to extract gap statements. Group similar gaps by topic using basic text similarity (TF-IDF + cosine similarity).
  - Files: book_researcher/gap_extractor.py
  - Done when: `GapExtractor.extract(reviews)` returns a list of Gap objects with text, source_review, and topic fields. Similar gaps are grouped under the same topic. At least 80% of known gap phrases in sample data are correctly extracted.

- [x] Task 4: Niche profiler and TOC generator
  - What: Build the niche profiler that takes grouped gaps and identifies the most underserved niche (highest gap density, lowest existing coverage). Then implement an LLM-based TOC generator that takes the niche profile and produces a structured table of contents. For MVP, implement a template-based TOC generator alongside a placeholder LM call interface.
  - Files: book_researcher/niche_profiler.py, book_researcher/toc_generator.py
  - Done when: `NicheProfiler.analyze(gaps)` returns a NicheProfile with top_gap_topics, gap_count, and recommended_focus. `TOCGenerator.generate(niche_profile)` returns a structured TableOfContents with chapters and subtopics. Both template-based and LLM placeholder paths work.

- [x] Task 5: End-to-end pipeline and CLI entry point
  - What: Wire all modules into a single pipeline (BookResearcher class) that orchestrates: fetch reviews → extract gaps → profile niche → generate TOC. Build a CLI entry point (`python -m book_researcher --book-ids <ids>`) that runs the full pipeline and outputs the result as JSON.
  - Files: book_researcher/pipeline.py, book_researcher/cli.py
  - Done when: `BookResearcher.run(book_ids)` executes the full pipeline and returns a complete TOC. CLI accepts --book-ids flag, runs the pipeline, and prints JSON output. End-to-end test with sample data produces a valid TOC with at least 5 chapters.

- [x] Task 6: Tests and documentation
  - What: Write unit tests for all modules (aggregator, gap extractor, niche profiler, TOC generator, pipeline). Add a README with setup instructions, usage examples, and architecture overview.
  - Files: tests/test_aggregator.py, tests/test_gap_extractor.py, tests/test_niche_profiler.py, tests/test_toc_generator.py, tests/test_pipeline.py, README.md
  - Done when: All tests pass (pytest). README covers installation, usage, and architecture. Code coverage > 80% on core modules.