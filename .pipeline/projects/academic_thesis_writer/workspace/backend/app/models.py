"""Pydantic data models for the thesis writer."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────────

class CitationStyle(str, Enum):
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"


class SectionName(str, Enum):
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"


# ── Source ──────────────────────────────────────────────────────────────

class Source(BaseModel):
    """A single literature source."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    abstract: str = ""
    url: Optional[str] = None
    pdf_path: Optional[str] = None
    full_text: str = ""
    source_type: str = "manual"  # manual | url | pdf
    metadata_completeness: float = 0.0  # 0.0 – 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def completeness_pct(self) -> float:
        """Return metadata completeness as a percentage."""
        score = 0.0
        if self.title:
            score += 0.35
        if self.authors:
            score += 0.20
        if self.year:
            score += 0.15
        if self.abstract:
            score += 0.15
        if self.url:
            score += 0.10
        if self.full_text:
            score += 0.05
        return round(min(score, 1.0), 10)


# ── Citation / Bibliography ─────────────────────────────────────────────

class BibliographyEntry(BaseModel):
    """A formatted bibliography entry."""

    citation_key: str
    source_id: str
    style: CitationStyle
    formatted: str


class InlineCitation(BaseModel):
    """An inline citation marker in generated text."""

    citation_key: str
    source_id: str
    position: int = 0  # character offset in the draft


# ── Section ─────────────────────────────────────────────────────────────

class Section(BaseModel):
    """A section of the thesis draft."""

    name: SectionName
    content: str = ""
    inline_citations: List[InlineCitation] = Field(default_factory=list)


# Alias — some tests import DraftSection instead of Section
DraftSection = Section


# ── Draft ───────────────────────────────────────────────────────────────

class Draft(BaseModel):
    """A complete thesis draft."""

    topic: str
    sections: List[Section] = Field(default_factory=list)
    bibliography: List[BibliographyEntry] = Field(default_factory=list)
    citation_style: CitationStyle = CitationStyle.APA
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def full_text(self) -> str:
        """Return the entire draft as a single string."""
        parts: List[str] = [f"# {self.topic}"]
        for sec in self.sections:
            parts.append(f"## {sec.name.value.title().replace('_', ' ')}\n\n{sec.content}")
            for cit in sec.inline_citations:
                parts.append(f"\n[Inline: {cit.citation_key}]")
        parts.append("\n## References\n\n")
        for entry in self.bibliography:
            parts.append(f"[{entry.citation_key}] {entry.formatted}")
        return "\n\n".join(parts)


# ── Thesis Project ──────────────────────────────────────────────────────

class ThesisProject(BaseModel):
    """A thesis project containing sources and a draft."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    sources: List[Source] = Field(default_factory=list)
    draft: Optional[Draft] = None
    citation_style: CitationStyle = CitationStyle.APA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_source(self, source: Source) -> None:
        self.sources.append(source)
        self.updated_at = datetime.utcnow()

    def remove_source(self, source_id: str) -> bool:
        before = len(self.sources)
        self.sources = [s for s in self.sources if s.id != source_id]
        removed = len(self.sources) < before
        if removed:
            self.updated_at = datetime.utcnow()
        return removed
