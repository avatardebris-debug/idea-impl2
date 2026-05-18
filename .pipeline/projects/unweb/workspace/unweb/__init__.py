"""
unweb — Unmask the connections behind any news story.

Given a news story URL or raw text, maps:
  - People mentioned → their roles, affiliations, known funding sources
  - Organizations → who controls them, parent orgs, known donors
  - Cross-connections → shared board members, funders, political ties
  - Funding chains → who funds whom

Uses Wikipedia, OpenSecrets-style public data, DuckDuckGo, and an LLM
to synthesise a structured connection graph + narrative report.

Usage:
    python -m unweb "https://example.com/news-article"
    python -m unweb "article text..." --text-input
    python -m unweb "story about EPA and ExxonMobil" --text-input --output report.md
"""
__version__ = "0.1.0"
