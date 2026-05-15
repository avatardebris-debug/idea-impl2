"""Tests for the SEC filing parser module."""

import pytest
from sec_importer.parser import FilingParser, parse_filing
from sec_importer.models import FilingItemModel


# --- FilingParser.parse() ---

class TestFilingParserParse:
    def test_parse_text_filing(self):
        """Test parsing a text-based 10-K filing."""
        raw_text = """
Item 1. Business
Apple Inc. designs, manufactures, and sells consumer electronics.

Item 1A. Risk Factors
Investing in our stock involves risks.

Item 7. Management's Discussion and Analysis
Our revenue increased by 5% this year.
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")

        assert len(items) >= 3
        labels = [item.item_label for item in items]
        assert any("Item 1" in label for label in labels)
        assert any("Item 1A" in label for label in labels)
        assert any("Item 7" in label for label in labels)

    def test_parse_empty_text(self):
        """Test parsing empty text returns a single full-text item."""
        parser = FilingParser()
        items = parser.parse("", "10-K")
        assert len(items) == 1
        assert items[0].item_label == "Full Filing"
        assert items[0].item_content == ""

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only text."""
        parser = FilingParser()
        items = parser.parse("   \n  \n  ", "10-K")
        assert len(items) == 1
        assert items[0].item_label == "Full Filing"

    def test_parse_xbrl_filing(self):
        """Test parsing XBRL-formatted filing."""
        raw_text = """<?xml version="1.0"?>
<root>
<us-gaap:Revenue>1000000000000</us-gaap:Revenue>
<us-gaap:NetIncome>200000000000</us-gaap:NetIncome>
<us-gaap:EarningsPerShare>5.00 dollars per share</us-gaap:EarningsPerShare>
</root>
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")

        # Should parse XBRL elements
        assert len(items) > 0
        assert all(item.item_type == "xbrl_element" for item in items)

    def test_parse_xbrl_no_elements(self):
        """Test XBRL parsing when no elements are found."""
        raw_text = """<?xml version="1.0"?>
<root>
<empty></empty>
<empty></empty>
<empty></empty>
</root>
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")

        # Should fall back to full text
        assert len(items) == 1
        assert items[0].item_type == "xbrl_full"

    def test_parse_10q_filing(self):
        """Test parsing a 10-Q filing."""
        raw_text = """
PART I - FINANCIAL INFORMATION
Item 1. Financial Statements
Consolidated Balance Sheet
Assets: $100,000

Item 2. Management's Discussion
Revenue grew 10%.
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-Q")

        assert len(items) >= 2
        labels = [item.item_label for item in items]
        assert any("Financial" in label for label in labels)

    def test_parse_8k_filing(self):
        """Test parsing an 8-K filing."""
        raw_text = """
Item 2.01 Completion of Acquisition
We acquired Company X for $1 billion.

Item 9.01 Financial Statements
See Exhibit 99.1.
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "8-K")

        assert len(items) >= 2
        labels = [item.item_label for item in items]
        assert any("Item 2" in label for label in labels)


# --- Section classification ---

class TestSectionClassification:
    def test_classify_item(self):
        """Test classification of Item sections."""
        parser = FilingParser()
        assert parser._classify_section("Item 1. Business") == "item"
        assert parser._classify_section("Item 7. MD&A") == "item"

    def test_classify_financial(self):
        """Test classification of financial sections."""
        parser = FilingParser()
        assert parser._classify_section("Balance Sheet") == "financial_statement"
        assert parser._classify_section("Statements of Cash Flows") == "financial_statement"
        assert parser._classify_section("Notes to Financial Statements") == "financial_statement"

    def test_classify_mda(self):
        """Test classification of MD&A sections."""
        parser = FilingParser()
        assert parser._classify_section("Management's Discussion and Analysis") == "mda"

    def test_classify_risk(self):
        """Test classification of risk sections."""
        parser = FilingParser()
        assert parser._classify_section("Risk Factors") == "risk_factors"

    def test_classify_legal(self):
        """Test classification of legal sections."""
        parser = FilingParser()
        assert parser._classify_section("Legal Proceedings") == "legal"

    def test_classify_compensation(self):
        """Test classification of compensation sections."""
        parser = FilingParser()
        assert parser._classify_section("Executive Compensation") == "compensation"

    def test_classify_unknown(self):
        """Test classification of unknown sections."""
        parser = FilingParser()
        assert parser._classify_section("Some Random Section") == "other"


# --- get_sections() ---

class TestGetSections:
    def test_get_sections_returns_list(self):
        """Test get_sections returns a list."""
        parser = FilingParser()
        parser.parse("Item 1. Business\nTest content", "10-K")
        sections = parser.get_sections()
        assert isinstance(sections, list)


# --- get_summary() ---

class TestGetSummary:
    def test_get_summary_counts(self):
        """Test get_summary returns correct counts."""
        parser = FilingParser()
        parser.parse("""
Item 1. Business
Content here.

Item 2. Properties
More content.

Risk Factors
Danger!
""", "10-K")
        summary = parser.get_summary()
        assert isinstance(summary, dict)
        # Should have at least item and risk_factors types
        total = sum(summary.values())
        assert total >= 2


# --- parse_filing() convenience function ---

class TestParseFiling:
    def test_convenience_function(self):
        """Test the convenience parse_filing function."""
        raw_text = "Item 1. Business\nApple is a tech company."
        items = parse_filing(raw_text, "10-K")

        assert isinstance(items, list)
        assert len(items) >= 1
        assert isinstance(items[0], FilingItemModel)
        assert "Item 1" in items[0].item_label


# --- Edge cases ---

class TestEdgeCases:
    def test_section_with_no_content(self):
        """Test section header with no following content."""
        raw_text = """Item 1. Business
Item 2. Properties"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")
        # Should still parse Item 1 even if empty
        assert len(items) >= 1

    def test_mixed_case_headers(self):
        """Test parsing with mixed case section headers."""
        raw_text = """
item 1. business
content here.

ITEM 2. PROPERTIES
more content.
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")
        assert len(items) >= 2

    def test_section_with_special_characters(self):
        """Test section headers with special characters."""
        raw_text = """
Item 1A. Risk Factors (including "quoted" text)
Content with 'single quotes' and (parentheses).
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")
        assert len(items) >= 1
        assert any("Risk" in (item.item_label or "") for item in items)

    def test_long_filing(self):
        """Test parsing a long filing with many sections."""
        sections = "\n".join([f"Item {i}. Section {i}\nContent for section {i}." for i in range(1, 21)])
        parser = FilingParser()
        items = parser.parse(sections, "10-K")
        assert len(items) >= 20

    def test_filing_with_numbers_in_content(self):
        """Test that numbers in content don't confuse the parser."""
        raw_text = """
Item 1. Business
Revenue was $1,234,567,890 in 2021.
Growth rate: 12.5%.
"""
        parser = FilingParser()
        items = parser.parse(raw_text, "10-K")
        assert len(items) >= 1
        assert any("1,234,567,890" in (item.item_content or "") for item in items)
