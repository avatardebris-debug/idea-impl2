# see_bs — News BS Detection

A Python library that scores news articles for "BS" (bullshit) using techniques inspired by Scott Adams and Scott Alexander.

## What It Does

`see_bs` applies several cognitive heuristics to news articles and returns a BS score (0–100) with a breakdown of which filters triggered and why.

### Filters Applied

| Filter | What It Checks |
|---|---|
| **Scott Alexander Rule** | Certainty language ("obviously", "undoubtedly") without evidence |
| **Gellman Amnesia** | Would you believe this claim if it came from the opposing side? |
| **Reporter Identity** | Does the source/outlet have a known bias? |
| **Incentive Alignment** | Who benefits from you believing this? |

## Installation

```bash
pip install -e .
```

Or install dev dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Python API

```python
from see_bs import filter_news, NewsArticle
from datetime import datetime

article = NewsArticle(
    title="Everyone Knows the Economy Is Collapsing",
    content="The economy is obviously in freefall. No one disputes the facts.",
    source="Patriot Daily",
    author="John Hawk",
    date=datetime.now(),
    outlet_bias="right",
    claim_type="factual",
    evidence_level="weak",
    author_track_record="mixed",
    incentives=["ad revenue from outrage clicks"],
)

result = filter_news(article)
print(f"BS Score: {result.bs_score:.1f} / 100")
print(f"Verdict:  {result.verdict}")
```

### CLI

```bash
# Run demo on built-in sample articles
see-bs --demo

# Analyze a JSON article from stdin
echo '{"title":"Test","content":"Obviously everyone agrees...","source":"Fake News","author":"Bob","date":"2025-01-01","outlet_bias":"extreme","claim_type":"factual","evidence_level":"none","author_track_record":"unreliable","incentives":["clicks"]}' | see-bs --stdin

# Analyze a JSON article from a file
see-bs --json article.json
```

## Project Structure

```
see_bs/
├── __init__.py    # Public API: filter_news, NewsArticle, ScoreEngine
├── __main__.py    # CLI entry point
├── engine.py      # Scoring engine
├── filters.py     # BS detection filters
├── models.py      # Data models
tests/
├── __init__.py
└── test_see_bs.py  # Unit + integration tests
pyproject.toml     # Package config
README.md          # This file
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT
