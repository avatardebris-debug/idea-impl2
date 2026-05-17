# Dropsearch

Product catalog extraction tool for e-commerce stores.

## Features

- **Multi-platform support**: Shopify, WooCommerce, and generic HTML stores
- **JSON-LD extraction**: Parses structured data from `<script type="application/ld+json">` tags
- **CSS fallback**: Falls back to CSS selectors when structured data is unavailable
- **Multiple output formats**: Markdown and plain text reports
- **CLI tool**: Command-line interface for quick extraction

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Extract from a local HTML file
dropsearch file://path/to/store.html

# Extract from a local HTML file with text output
dropsearch file://path/to/store.html -f text

# Extract to a file
dropsearch file://path/to/store.html -o report.md
```

## Project Structure

```
workspace/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── models/
│   │   ├── __init__.py
│   │   └── product.py      # Product data model
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── extractor.py    # Main extraction orchestrator
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── shopify.py
│   │       ├── woocommerce.py
│   │       └── generic.py
│   └── reporter/
│       ├── __init__.py
│       └── formatter.py    # Report formatting
├── tests/
│   ├── fixtures/
│   │   ├── shopify_store.html
│   │   ├── woocommerce_store.html
│   │   └── generic_store.html
│   └── test_product_extraction.py
├── pyproject.toml
└── requirements.txt
```

## Testing

```bash
pytest tests/ -v
```

## Roadmap

- [x] Product data model
- [x] Shopify parser (JSON-LD + CSS)
- [x] WooCommerce parser (JSON-LD + CSS)
- [x] Generic HTML parser (CSS)
- [x] Product extractor orchestrator
- [x] Report formatter (markdown + text)
- [x] CLI entry point
- [x] Tests with fixtures
- [ ] HTML fetching (Phase 2)
- [ ] Pagination support
- [ ] Rate limiting
- [ ] Output to CSV/JSON
