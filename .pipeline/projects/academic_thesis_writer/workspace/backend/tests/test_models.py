"""Tests for Pydantic data models."""

import uuid
from datetime import datetime

import pytest

from app.models import (
    BibliographyEntry,
    CitationStyle,
    Draft,
    DraftSection,
    InlineCitation,
    Section,
    SectionName,
    Source,
    ThesisProject,
)


class TestCitationStyle:
    def test_enum_values(self):
        assert CitationStyle.APA.value == "apa"
        assert CitationStyle.MLA.value == "mla"
        assert CitationStyle.CHICAGO.value == "chicago"
        assert CitationStyle.IEEE.value == "ieee"

    def test_enum_members(self):
        assert len(CitationStyle) == 4


class TestSectionName:
    def test_enum_values(self):
        assert SectionName.ABSTRACT.value == "abstract"
        assert SectionName.INTRODUCTION.value == "introduction"
        assert SectionName.LITERATURE_REVIEW.value == "literature_review"
        assert SectionName.METHODOLOGY.value == "methodology"
        assert SectionName.RESULTS.value == "results"
        assert SectionName.DISCUSSION.value == "discussion"
        assert SectionName.CONCLUSION.value == "conclusion"

    def test_enum_members(self):
        assert len(SectionName) == 7


class TestSource:
    def test_default_values(self):
        source = Source(title="Test Title")
        assert source.authors == []
        assert source.year is None
        assert source.abstract == ""
        assert source.url is None
        assert source.pdf_path is None
        assert source.full_text == ""
        assert source.source_type == "manual"
        assert source.metadata_completeness == 0.0
        assert source.created_at is not None

    def test_id_is_uuid(self):
        source = Source(title="Test")
        assert source.id is not None
        # Verify it's a valid UUID
        uuid.UUID(source.id)

    def test_completeness_pct_empty(self):
        source = Source(title="Test")
        assert source.completeness_pct() == 0.35  # Only title

    def test_completeness_pct_full(self):
        source = Source(
            title="Test Title",
            authors=["Author One", "Author Two"],
            year=2023,
            abstract="This is an abstract.",
            url="https://example.com",
            full_text="Full text here.",
        )
        assert source.completeness_pct() == 1.0

    def test_completeness_pct_partial(self):
        source = Source(
            title="Test Title",
            authors=["Author One"],
            year=2023,
        )
        # title (0.35) + authors (0.20) + year (0.15) = 0.70
        assert source.completeness_pct() == 0.70

    def test_completeness_pct_capped_at_one(self):
        source = Source(
            title="Test",
            authors=["A"],
            year=2023,
            abstract="Abs",
            url="http://x",
            full_text="Text",
        )
        assert source.completeness_pct() == 1.0


class TestInlineCitation:
    def test_default_values(self):
        cite = InlineCitation(citation_key="key1", source_id="src1")
        assert cite.position == 0

    def test_custom_position(self):
        cite = InlineCitation(citation_key="key1", source_id="src1", position=42)
        assert cite.position == 42


class TestBibliographyEntry:
    def test_creation(self):
        entry = BibliographyEntry(
            citation_key="key1",
            source_id="src1",
            style=CitationStyle.APA,
            formatted="Author. (2023). Title.",
        )
        assert entry.citation_key == "key1"
        assert entry.source_id == "src1"
        assert entry.style == CitationStyle.APA
        assert entry.formatted == "Author. (2023). Title."


class TestSection:
    def test_default_values(self):
        section = Section(name=SectionName.INTRODUCTION)
        assert section.content == ""
        assert section.inline_citations == []

    def test_with_content(self):
        section = Section(name=SectionName.INTRODUCTION, content="Some content")
        assert section.content == "Some content"

    def test_with_inline_citations(self):
        cite = InlineCitation(citation_key="key1", source_id="src1", position=10)
        section = Section(name=SectionName.INTRODUCTION, inline_citations=[cite])
        assert len(section.inline_citations) == 1
        assert section.inline_citations[0].citation_key == "key1"


class TestDraft:
    def test_default_values(self):
        draft = Draft(topic="Test Topic")
        assert draft.sections == []
        assert draft.bibliography == []
        assert draft.citation_style == CitationStyle.APA
        assert draft.generated_at is not None

    def test_full_text_empty(self):
        draft = Draft(topic="Test Topic")
        text = draft.full_text()
        assert "Test Topic" in text
        assert "## References" in text

    def test_full_text_with_sections(self):
        section = Section(name=SectionName.INTRODUCTION, content="Intro content")
        draft = Draft(topic="Test Topic", sections=[section])
        text = draft.full_text()
        assert "## Introduction" in text
        assert "Intro content" in text

    def test_full_text_with_bibliography(self):
        entry = BibliographyEntry(
            citation_key="key1",
            source_id="src1",
            style=CitationStyle.APA,
            formatted="Author. (2023). Title.",
        )
        draft = Draft(topic="Test Topic", bibliography=[entry])
        text = draft.full_text()
        assert "[key1] Author. (2023). Title." in text

    def test_full_text_with_inline_citations(self):
        cite = InlineCitation(citation_key="key1", source_id="src1", position=10)
        section = Section(name=SectionName.INTRODUCTION, content="Content", inline_citations=[cite])
        draft = Draft(topic="Test Topic", sections=[section])
        text = draft.full_text()
        assert "[Inline: key1]" in text


class TestThesisProject:
    def test_default_values(self):
        project = ThesisProject(topic="Test Topic")
        assert project.sources == []
        assert project.draft is None
        assert project.citation_style == CitationStyle.APA
        assert project.created_at is not None
        assert project.updated_at is not None
        # Verify id is a valid UUID
        uuid.UUID(project.id)

    def test_add_source(self):
        project = ThesisProject(topic="Test Topic")
        source = Source(title="New Source")
        project.add_source(source)
        assert len(project.sources) == 1
        assert project.sources[0].title == "New Source"
        # updated_at should have changed
        assert project.updated_at > project.created_at

    def test_remove_source(self):
        project = ThesisProject(topic="Test Topic")
        source = Source(title="Source to remove")
        project.add_source(source)
        result = project.remove_source(source.id)
        assert result is True
        assert len(project.sources) == 0

    def test_remove_nonexistent_source(self):
        project = ThesisProject(topic="Test Topic")
        result = project.remove_source("nonexistent-id")
        assert result is False

    def test_update_timestamp_on_remove(self):
        project = ThesisProject(topic="Test Topic")
        source = Source(title="Source to remove")
        project.add_source(source)
        old_updated = project.updated_at
        import time
        time.sleep(0.01)
        project.remove_source(source.id)
        assert project.updated_at > old_updated
