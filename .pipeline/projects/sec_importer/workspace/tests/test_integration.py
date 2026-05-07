"""Integration tests for the SEC importer pipeline.

Tests the full workflow: fetch -> parse -> store.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from sec_importer.fetcher import (
    resolve_ticker_to_cik,
    get_cik_submissions,
    get_latest_filing,
    download_filing_text,
)
from sec_importer.parser import FilingParser
from sec_importer.repository import CompanyRepository, FilingRepository, FilingItemRepository
from sec_importer.models import CompanyModel, FilingModel, FilingItemModel


@pytest.fixture
def db_path():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def mock_filing_text():
    """Return mock 10-K filing text."""
    return """
<Item 1. Business>
Apple Inc. designs, manufactures, and sells consumer electronics, software, and services.

<Item 1A. Risk Factors>
Investing in our stock involves risks.

<Item 7. Management's Discussion and Analysis>
Our revenue increased by 5% this year compared to the prior year.

<Consolidated Statements of Income>
Revenue: $365,817,000
Cost of Revenue: $213,481,000
Gross Margin: $152,336,000
"""


@pytest.fixture
def mock_company():
    """Return a mock company."""
    return CompanyModel(
        cik="0000320193",
        name="Apple Inc.",
        sic="3663",
        industry="Consumer Electronics",
    )


@pytest.fixture
def mock_filing():
    """Return a mock filing."""
    return FilingModel(
        accession_no="000032019321000099",
        cik="0000320193",
        filing_type="10-K",
        filing_date="2021-01-29",
    )


class TestFetchParseStore:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self, db_path, mock_filing_text, mock_company, mock_filing):
        """Test the full fetch-parse-store pipeline."""
        # Setup repositories
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            # Step 1: Store company
            company_id = company_repo.insert_company(mock_company)
            assert company_id > 0

            # Step 2: Store filing
            filing_id = filing_repo.insert_filing(mock_filing)
            assert filing_id > 0

            # Step 3: Parse filing
            parser = FilingParser()
            items = parser.parse(mock_filing_text, "10-K")

            # Step 4: Store items
            for item in items:
                item.filing_id = filing_id
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            # Verify all data
            stored_company = company_repo.get_company_by_cik("0000320193")
            assert stored_company is not None
            assert stored_company['name'] == "Apple Inc."

            stored_filing = filing_repo.get_filing_by_accession_no("000032019321000099")
            assert stored_filing is not None
            assert stored_filing['filing_type'] == "10-K"

            stored_items = item_repo.get_by_accession_no("000032019321000099")
            assert len(stored_items) > 0

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_empty_filing(self, db_path, mock_company, mock_filing):
        """Test pipeline with empty filing text."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            company_id = company_repo.insert_company(mock_company)
            filing_id = filing_repo.insert_filing(mock_filing)

            parser = FilingParser()
            items = parser.parse("", "10-K")

            for item in items:
                item.filing_id = filing_id
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            # Should have one "Full Filing" item
            stored_items = item_repo.get_by_accession_no(mock_filing.accession_no)
            assert len(stored_items) == 1
            assert stored_items[0]['item_label'] == "Full Filing"

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_multiple_filings(self, db_path):
        """Test pipeline with multiple filings for the same company."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            # Insert company
            company = CompanyModel(cik="0000320193", name="Apple Inc.")
            company_repo.insert_company(company)

            # Insert multiple filings
            filings = [
                FilingModel(
                    accession_no="000032019321000099",
                    cik="0000320193",
                    filing_type="10-K",
                    filing_date="2021-01-29",
                ),
                FilingModel(
                    accession_no="000032019321000100",
                    cik="0000320193",
                    filing_type="10-Q",
                    filing_date="2021-04-30",
                ),
            ]

            filing_ids = []
            for filing in filings:
                filing_id = filing_repo.insert_filing(filing)
                filing_ids.append(filing_id)

            # Parse and store items for each filing
            parser = FilingParser()
            for i, filing in enumerate(filings):
                filing_text = f"<Item {i+1}. Business>Test content for filing {i+1}</Item>"
                items = parser.parse(filing_text, filing.filing_type)

                for item in items:
                    item.filing_id = filing_ids[i]
                    item.accession_no = filing.accession_no
                    item_repo.insert_filing_item(item)

            # Verify all data
            company = company_repo.get_company_by_cik("0000320193")
            assert company is not None

            filings = filing_repo.get_filings_by_cik("0000320193")
            assert len(filings) == 2

            for filing in filings:
                items = item_repo.get_by_accession_no(filing['accession_no'])
                assert len(items) > 0

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_duplicate_filing(self, db_path, mock_company, mock_filing):
        """Test pipeline with duplicate filing (should update, not insert)."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            company_id = company_repo.insert_company(mock_company)
            filing_id1 = filing_repo.insert_filing(mock_filing)

            # Parse and store items
            parser = FilingParser()
            items = parser.parse("<Item 1>Test</Item>", "10-K")
            for item in items:
                item.filing_id = filing_id1
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            # Insert duplicate filing
            filing_id2 = filing_repo.insert_filing(mock_filing)
            assert filing_id1 == filing_id2  # Should return same ID

            # Items should still be there
            stored_items = item_repo.get_by_accession_no(mock_filing.accession_no)
            assert len(stored_items) > 0

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_invalid_filing_type(self, db_path, mock_company, mock_filing):
        """Test pipeline with invalid filing type."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            company_id = company_repo.insert_company(mock_company)
            filing_id = filing_repo.insert_filing(mock_filing)

            parser = FilingParser()
            items = parser.parse("<Item 1>Test</Item>", "INVALID")

            # Should still create items
            for item in items:
                item.filing_id = filing_id
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            stored_items = item_repo.get_by_accession_no(mock_filing.accession_no)
            assert len(stored_items) > 0

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_large_filing(self, db_path, mock_company, mock_filing):
        """Test pipeline with large filing text."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            company_id = company_repo.insert_company(mock_company)
            filing_id = filing_repo.insert_filing(mock_filing)

            # Create large filing text
            large_text = "<Item 1>" + "A" * 100000 + "</Item>"

            parser = FilingParser()
            items = parser.parse(large_text, "10-K")

            for item in items:
                item.filing_id = filing_id
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            stored_items = item_repo.get_by_accession_no(mock_filing.accession_no)
            assert len(stored_items) > 0

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()

    def test_pipeline_with_special_characters(self, db_path, mock_company, mock_filing):
        """Test pipeline with special characters in filing text."""
        company_repo = CompanyRepository(db_path)
        company_repo.init_db()

        filing_repo = FilingRepository(db_path)
        filing_repo.init_db()

        item_repo = FilingItemRepository(db_path)
        item_repo.init_db()

        try:
            company_id = company_repo.insert_company(mock_company)
            filing_id = filing_repo.insert_filing(mock_filing)

            # Create filing text with special characters
            special_text = """
<Item 1>
Company name: Apple Inc. (NASDAQ: AAPL)
Revenue: $100,000,000.00
Growth: 10.5%
Description: "Best" company & industry leader!
</Item>
"""

            parser = FilingParser()
            items = parser.parse(special_text, "10-K")

            for item in items:
                item.filing_id = filing_id
                item.accession_no = mock_filing.accession_no
                item_repo.insert_filing_item(item)

            stored_items = item_repo.get_by_accession_no(mock_filing.accession_no)
            assert len(stored_items) > 0
            assert any("Apple Inc." in (item.get('item_content') or "") for item in stored_items)

        finally:
            company_repo.close()
            filing_repo.close()
            item_repo.close()
