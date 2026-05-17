"""
research1 — Multi-source research assistant.

Given a topic, searches highly credible sources (arXiv, PubMed, Wikipedia,
credible web domains) and synthesises results into a structured markdown report.

Usage:
    python -m research1 "quantum error correction" --depth 5 --output report.md
    python -m research1 "CRISPR gene editing" --sources arxiv pubmed web
"""
__version__ = "0.1.0"
__all__ = ["sources", "researcher", "summarizer", "report", "cli"]
