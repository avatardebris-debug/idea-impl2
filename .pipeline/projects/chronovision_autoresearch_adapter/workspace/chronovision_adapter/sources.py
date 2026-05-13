"""Research paper sources — arxiv, openreview, biorxiv, NASA ADS, NBER.

Each source provides a unified query interface returning Paper objects.
Network calls are stubbed with configurable test data for offline testing.
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from chronovision_adapter.models import Paper

logger = logging.getLogger(__name__)


class PaperSource(ABC):
    """Abstract base for research paper sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        ...

    @abstractmethod
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        ...

    def _make_id(self, raw_id: str) -> str:
        return f"{self.source_name}:{raw_id}"


class ArxivSource(PaperSource):
    """ArXiv paper source (offline-capable with stub data)."""

    source_name = "arxiv"

    STUB_PAPERS = [
        Paper(
            paper_id="arxiv:2301.00001",
            title="Attention Is All You Need: A Retrospective",
            authors=["A. Vaswani", "N. Shazeer"],
            abstract="We revisit the transformer architecture five years later.",
            source="arxiv",
            published_date="2023-01-15",
            url="https://arxiv.org/abs/2301.00001",
            categories=["cs.CL", "cs.AI"],
            citation_count=15000,
            keywords=["transformer", "attention", "NLP"],
        ),
        Paper(
            paper_id="arxiv:2312.00042",
            title="Scaling Laws for Neural Language Models",
            authors=["J. Kaplan", "S. McCandlish"],
            abstract="We study empirical scaling laws for language model performance.",
            source="arxiv",
            published_date="2023-12-01",
            url="https://arxiv.org/abs/2312.00042",
            categories=["cs.LG", "cs.CL"],
            citation_count=3200,
            keywords=["scaling", "language models", "compute"],
        ),
        Paper(
            paper_id="arxiv:2406.00100",
            title="Constitutional AI: Harmlessness from AI Feedback",
            authors=["Y. Bai", "S. Kadavath"],
            abstract="We propose a method for training AI assistants using AI feedback.",
            source="arxiv",
            published_date="2024-06-10",
            url="https://arxiv.org/abs/2406.00100",
            categories=["cs.AI", "cs.CL"],
            citation_count=850,
            keywords=["constitutional AI", "alignment", "RLHF"],
        ),
    ]

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        q = query.lower()
        matches = [p for p in self.STUB_PAPERS if q in p.title.lower() or q in p.abstract.lower()
                    or any(q in kw for kw in p.keywords)]
        if not matches:
            matches = self.STUB_PAPERS  # return all if no match
        return matches[:max_results]

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        for p in self.STUB_PAPERS:
            if p.paper_id == paper_id:
                return p
        return None


class OpenReviewSource(PaperSource):
    """OpenReview paper source (offline stub)."""

    source_name = "openreview"

    STUB_PAPERS = [
        Paper(
            paper_id="openreview:ICLR2024-001",
            title="Learning to Reason with LLMs",
            authors=["OpenAI Research"],
            abstract="We explore multi-step reasoning in large language models.",
            source="openreview",
            published_date="2024-01-20",
            url="https://openreview.net/forum?id=ICLR2024-001",
            categories=["machine learning"],
            citation_count=420,
            keywords=["reasoning", "LLM", "chain of thought"],
        ),
    ]

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        q = query.lower()
        matches = [p for p in self.STUB_PAPERS if q in p.title.lower() or q in p.abstract.lower()
                    or any(q in kw for kw in p.keywords)]
        if not matches:
            matches = self.STUB_PAPERS
        return matches[:max_results]

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        for p in self.STUB_PAPERS:
            if p.paper_id == paper_id:
                return p
        return None


class BioRxivSource(PaperSource):
    """bioRxiv paper source (offline stub)."""

    source_name = "biorxiv"

    STUB_PAPERS = [
        Paper(
            paper_id="biorxiv:2024.03.001",
            title="AlphaFold3: Accurate Structure Prediction Beyond Proteins",
            authors=["J. Jumper", "R. Evans"],
            abstract="We extend protein structure prediction to nucleic acids and ligands.",
            source="biorxiv",
            published_date="2024-03-15",
            url="https://biorxiv.org/content/10.1101/2024.03.001",
            categories=["bioinformatics", "structural biology"],
            citation_count=2100,
            keywords=["protein folding", "AlphaFold", "structural biology"],
        ),
    ]

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        q = query.lower()
        matches = [p for p in self.STUB_PAPERS if q in p.title.lower() or q in p.abstract.lower()
                    or any(q in kw for kw in p.keywords)]
        if not matches:
            matches = self.STUB_PAPERS
        return matches[:max_results]

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        for p in self.STUB_PAPERS:
            if p.paper_id == paper_id:
                return p
        return None


class MultiSourceSearch:
    """Unified search across all paper sources."""

    def __init__(self, sources: Optional[List[PaperSource]] = None):
        self.sources = sources or [ArxivSource(), OpenReviewSource(), BioRxivSource()]

    def search_all(self, query: str, max_per_source: int = 5) -> List[Paper]:
        results: List[Paper] = []
        for src in self.sources:
            try:
                papers = src.search(query, max_results=max_per_source)
                results.extend(papers)
            except Exception as e:
                logger.warning("Search failed for %s: %s", src.source_name, e)
        return results

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        for src in self.sources:
            result = src.get_paper(paper_id)
            if result:
                return result
        return None

    @property
    def source_names(self) -> List[str]:
        return [s.source_name for s in self.sources]
