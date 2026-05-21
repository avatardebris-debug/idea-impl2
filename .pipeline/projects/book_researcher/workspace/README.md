# Book Researcher

Find underserved book niches by analyzing reviews of top-selling information books.

## Overview

Book Researcher scans reviews from top-selling information books (via Amazon, Goodreads, etc.), identifies content gaps ("I wish it also covered X"), clusters those gaps into marketable niche profiles, and generates a table of contents for a book that would fill those gaps.

## Installation

```bash
pip install book-researcher
```

## Quick Start

### CLI

```bash
book-researcher --book-title "Deep Learning" --book-title "Python Crash Course"
```

### Python API

```python
from book_researcher.pipeline import run_pipeline

results = run_pipeline(book_titles=["Deep Learning", "Python Crash Course"])
for toc in results:
    print(toc.title)
    for chapter in toc.chapters:
        print(f"  - {chapter.title}")
```

## Architecture

```
reviews -> gaps -> niches -> TOC
```

1. **Aggregator** (`aggregator.py`, `aggregators/`): Fetches book reviews from various sources.
2. **Gap Extractor** (`gap_extractor.py`): Identifies content gaps from review text using phrase matching and TF-IDF clustering.
3. **Niche Profiler** (`niche_profiler.py`): Clusters gaps by topic and scores them to find marketable niches.
4. **TOC Generator** (`toc_generator.py`): Builds a table of contents from the top niche profiles.
5. **Pipeline** (`pipeline.py`): Wires everything together end-to-end.

## Data Models

- `BookReview`: A single review with book_id, text, rating, source, etc.
- `Gap`: A content gap with text, source review, and topic.
- `NicheProfile`: A clustered niche with topic, score, gap_count, and representative_gaps.
- `TableOfContents`: The final output with title and list of TOCChapter objects.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Project Structure

```
book_researcher/
├── __init__.py
├── models.py          # Core data models
├── aggregator.py      # Review aggregator interface
├── aggregators/       # Concrete aggregator implementations
│   ├── __init__.py
│   └── sample_reviews.py
├── gap_extractor.py   # Gap extraction engine
├── niche_profiler.py  # Niche clustering and scoring
├── toc_generator.py   # TOC generation from niches
├── pipeline.py        # End-to-end pipeline
└── cli.py             # CLI entry point
tests/
├── __init__.py
├── test_aggregator.py
├── test_gap_extractor.py
├── test_niche_profiler.py
├── test_toc_generator.py
└── test_pipeline.py
```

## License

MIT
