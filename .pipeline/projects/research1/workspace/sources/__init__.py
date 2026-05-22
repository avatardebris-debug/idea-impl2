"""sources/__init__.py — source plugin registry."""
from research1.sources.arxiv import search as arxiv_search
from research1.sources.pubmed import search as pubmed_search
from research1.sources.wikipedia import search as wikipedia_search
from research1.sources.web import search as web_search

SOURCES = {
    "arxiv":     arxiv_search,
    "pubmed":    pubmed_search,
    "wikipedia": wikipedia_search,
    "web":       web_search,
}

__all__ = ["SOURCES"]
