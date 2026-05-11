"""Thesis generation engine."""

from __future__ import annotations

import logging
from typing import List, Optional

from ..models import (
    BibliographyEntry,
    CitationStyle,
    Draft,
    DraftSection,
    Source,
    ThesisConfig,
)
from ..ingestion import ManualEntrySource, PDFExtractor, URLFetcher
from .llm_client import LLMClient
from .prompts import (
    CITATION_FORMATS,
    build_abstract_prompt,
    build_bibliography_prompt,
    build_citation_prompt,
    build_conclusion_prompt,
    build_discussion_prompt,
    build_introduction_prompt,
    build_literature_review_prompt,
    build_methodology_prompt,
    build_results_prompt,
    build_section_prompt,
)

logger = logging.getLogger(__name__)


class ThesisEngine:
    """Orchestrates thesis generation from sources."""

    def __init__(self, config: ThesisConfig):
        self.config = config
        self.llm = LLMClient(config.llm_backend)
        self.sources: List[Source] = []
        self.draft: Optional[Draft] = None

    # ── Source management ────────────────────────────────

    def add_source(self, source: Source) -> None:
        """Add a source to the thesis."""
        self.sources.append(source)
        logger.info("Added source: %s (%s)", source.title, source.source_type)

    def add_sources(self, sources: List[Source]) -> None:
        """Add multiple sources."""
        self.sources.extend(sources)

    def remove_source(self, title: str) -> bool:
        """Remove a source by title."""
        for i, s in enumerate(self.sources):
            if s.title == title:
                self.sources.pop(i)
                return True
        return False

    # ── Source ingestion helpers ────────────────────────────────

    async def ingest_pdf(self, file_path: str) -> Source:
        """Ingest a PDF file and return a Source."""
        extracted = await PDFExtractor.extract(file_path)
        return ManualEntrySource.create(
            title=extracted.title or "Untitled PDF",
            authors=extracted.authors or ["Unknown"],
            year=extracted.year,
            abstract=extracted.abstract or "",
            url=extracted.url,
        )

    async def ingest_url(self, url: str) -> Source:
        """Ingest content from a URL and return a Source."""
        fetched = await URLFetcher.fetch(url)
        return ManualEntrySource.create(
            title=fetched.title or "Untitled Page",
            authors=fetched.authors or ["Unknown"],
            year=fetched.year,
            abstract=fetched.abstract or "",
            url=url,
        )

    # ── Draft management ────────────────────────────────

    def create_draft(self, title: str, topic: str) -> Draft:
        """Create a new draft."""
        self.draft = Draft(
            title=title,
            topic=topic,
            sections=[],
            bibliography=[],
            citation_style=self.config.citation_style,
        )
        return self.draft

    def get_draft(self) -> Draft:
        """Get the current draft."""
        if not self.draft:
            raise ValueError("No draft created. Call create_draft() first.")
        return self.draft

    # ── Section generation ────────────────────────────────

    async def generate_section(
        self,
        section_name: str,
        topic: str,
        sources: Optional[List[Source]] = None,
        previous_sections: Optional[str] = None,
    ) -> str:
        """Generate a single section."""
        srcs = sources or self.sources
        system, user = build_section_prompt(
            section_name, topic, srcs, self.config.citation_style, previous_sections
        )
        content = await self.llm.generate(system, user)
        return content

    async def generate_all_sections(self, topic: str) -> List[str]:
        """Generate all sections in order."""
        if not self.draft:
            raise ValueError("No draft created.")

        sections_config = self.config.sections
        all_sections: List[str] = []
        previous_summary = None

        for section_name in sections_config:
            logger.info("Generating section: %s", section_name)
            content = await self.generate_section(
                section_name, topic, previous_sections=previous_summary
            )
            all_sections.append(content)

            # Add to draft
            self.draft.sections.append(
                DraftSection(name=section_name, content=content)
            )

            # Build summary for next section
            previous_summary = content[:500] + "..." if len(content) > 500 else content

        return all_sections

    # ── Abstract generation ────────────────────────────────

    async def generate_abstract(self, topic: str) -> str:
        """Generate an abstract from section summaries."""
        if not self.draft:
            raise ValueError("No draft created.")

        section_summaries = [s.content[:300] for s in self.draft.sections]
        system, user = build_abstract_prompt(topic, section_summaries)
        return await self.llm.generate(system, user)

    # ── Bibliography generation ────────────────────────────────

    async def generate_bibliography(self) -> List[BibliographyEntry]:
        """Generate bibliography entries for all sources."""
        if not self.draft:
            raise ValueError("No draft created.")

        system, user = build_bibliography_prompt(
            self.sources, self.config.citation_style
        )
        raw = await self.llm.generate(system, user)

        # Parse bibliography entries (simple line-based parsing)
        entries = []
        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entries.append(BibliographyEntry(text=line))

        self.draft.bibliography = entries
        return entries

    # ── Citation formatting ────────────────────────────────

    async def format_citations(self) -> List[str]:
        """Format all citations in the draft."""
        if not self.draft:
            raise ValueError("No draft created.")

        system, user = build_citation_prompt(
            self.sources, self.config.citation_style
        )
        raw = await self.llm.generate(system, user)
        return [line.strip() for line in raw.strip().split("\n") if line.strip()]

    # ── Full thesis generation ────────────────────────────────

    async def generate_thesis(self, topic: str) -> Draft:
        """Generate a complete thesis."""
        if not self.draft:
            self.create_draft(f"Thesis on {topic}", topic)

        logger.info("Generating thesis on: %s", topic)

        # Generate all sections
        await self.generate_all_sections(topic)

        # Generate abstract
        abstract = await self.generate_abstract(topic)
        self.draft.abstract = abstract

        # Generate bibliography
        await self.generate_bibliography()

        # Format citations
        await self.format_citations()

        logger.info("Thesis generation complete: %d sections, %d bibliography entries",
                     len(self.draft.sections), len(self.draft.bibliography))
        return self.draft

    # ── Export ────────────────────────────────

    def export_markdown(self) -> str:
        """Export the draft as Markdown."""
        if not self.draft:
            raise ValueError("No draft to export.")

        md = f"# {self.draft.title}\n\n"
        md += f"**Topic:** {self.draft.topic}\n\n"
        md += f"**Citation Style:** {self.config.citation_style.value}\n\n"

        if self.draft.abstract:
            md += f"## Abstract\n\n{self.draft.abstract}\n\n"

        for section in self.draft.sections:
            md += f"## {section.name}\n\n{section.content}\n\n"

        if self.draft.bibliography:
            md += "## Bibliography\n\n"
            for entry in self.draft.bibliography:
                md += f"- {entry.text}\n"

        return md

    def export_text(self) -> str:
        """Export the draft as plain text."""
        return self.export_markdown().replace("# ", "").replace("**", "")
