"""Tests for citation formatters (APA, MLA, Chicago, IEEE)."""

import pytest
from app.citation.formatters.apa import APAFormatter
from app.citation.formatters.mla import MLAFormatter
from app.citation.formatters.chicago import ChicagoFormatter
from app.citation.formatters.ieee import IEEEFormatter
from app.models import Source


@pytest.fixture
def journal_source():
    return Source(
        title="Deep Learning for Natural Language Processing",
        authors=["Smith, John", "Doe, Jane"],
        year=2023,
        abstract="A comprehensive survey of deep learning techniques.",
        url="https://example.com/article",
        source_type="url",
    )


@pytest.fixture
def book_source():
    return Source(
        title="The Art of Academic Writing",
        authors=["Brown, Alice"],
        year=2020,
        abstract="",
        url=None,
        source_type="manual",
    )


@pytest.fixture
def conference_source():
    return Source(
        title="Transformer Models in Vision",
        authors=["Lee, Minho", "Kim, Soo"],
        year=2022,
        abstract="",
        url="https://example.com/paper",
        source_type="url",
    )


class TestAPAFormatter:
    def test_format_journal(self, journal_source):
        entry = APAFormatter.format(journal_source, "Smith2023")
        assert "Smith, J., & Doe, J." in entry.formatted
        assert "(2023)" in entry.formatted
        assert "Deep Learning for Natural Language Processing" in entry.formatted

    def test_format_book(self, book_source):
        entry = APAFormatter.format(book_source, "Brown2020")
        assert "Brown, A." in entry.formatted
        assert "(2020)" in entry.formatted

    def test_format_inline(self, journal_source):
        inline = APAFormatter.format_inline(journal_source, page="42")
        assert "Smith & Doe, 2023, p. 42" in inline

    def test_format_inline_no_page(self, journal_source):
        inline = APAFormatter.format_inline(journal_source)
        assert "Smith & Doe, 2023" in inline


class TestMLAFormatter:
    def test_format_journal(self, journal_source):
        entry = MLAFormatter.format(journal_source, "Smith")
        assert "Smith, John, and Jane Doe." in entry.formatted
        assert "2023" in entry.formatted

    def test_format_book(self, book_source):
        entry = MLAFormatter.format(book_source, "Brown")
        assert "Brown, Alice." in entry.formatted

    def test_format_inline(self, journal_source):
        inline = MLAFormatter.format_inline(journal_source, page="42")
        assert "Smith 42" in inline


class TestChicagoFormatter:
    def test_format_journal(self, journal_source):
        entry = ChicagoFormatter.format(journal_source, "Smith2023")
        assert "Smith, John, and Jane Doe." in entry.formatted
        assert "2023" in entry.formatted

    def test_format_book(self, book_source):
        entry = ChicagoFormatter.format(book_source, "Brown2020")
        assert "Brown, Alice." in entry.formatted

    def test_format_inline(self, journal_source):
        inline = ChicagoFormatter.format_inline(journal_source, page="42")
        assert "Smith and Doe 2023, 42" in inline


class TestIEEEFormatter:
    def test_format_journal(self, journal_source):
        entry = IEEEFormatter.format(journal_source, "[1]")
        assert "[1]" in entry.formatted
        assert "J. Smith" in entry.formatted
        assert "2023" in entry.formatted

    def test_format_book(self, book_source):
        entry = IEEEFormatter.format(book_source, "[2]")
        assert "[2]" in entry.formatted
        assert "A. Brown" in entry.formatted

    def test_format_inline(self, journal_source):
        inline = IEEEFormatter.format_inline(journal_source, page="42")
        assert "[1]" in inline


class TestFormatterConsistency:
    def test_all_formatters_produce_non_empty(self, journal_source):
        for formatter_cls in [APAFormatter, MLAFormatter, ChicagoFormatter, IEEEFormatter]:
            entry = formatter_cls.format(journal_source, "test_key")
            assert len(entry.formatted) > 0
            assert entry.key is not None
