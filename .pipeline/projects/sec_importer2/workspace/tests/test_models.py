"""Tests for SEC Importer 2 models."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from sec_importer.models import Company, Filing, FilingContent


class TestCompanyModel:
    """Tests for the Company model."""

    def test_create_company(self, session, sample_company):
        """Test creating a company record."""
        company = Company(**sample_company)
        session.add(company)
        session.commit()

        result = session.execute(
            select(Company).where(Company.ticker == "AAPL")
        ).scalar_one()
        assert result.ticker == "AAPL"
        assert result.name == "Apple Inc."
        assert result.cik == "0000320193"

    def test_company_unique_ticker(self, session, sample_company):
        """Test that ticker is unique."""
        company1 = Company(**sample_company)
        session.add(company1)
        session.commit()

        # Try to create duplicate
        company2 = Company(**sample_company)
        session.add(company2)
        with pytest.raises(Exception):
            session.commit()


class TestFilingModel:
    """Tests for the Filing model."""

    def test_create_filing(self, session, sample_filing):
        """Test creating a filing record."""
        filing = Filing(**sample_filing)
        session.add(filing)
        session.commit()

        result = session.execute(
            select(Filing).where(Filing.accession_number == sample_filing["accession_number"])
        ).scalar_one()
        assert result.ticker == "AAPL"
        assert result.filing_type == "10-K"
        assert result.filing_date == "2024-10-31"

    def test_filing_company_relationship(self, session, sample_company, sample_filing):
        """Test filing links to company."""
        company = Company(**sample_company)
        session.add(company)
        session.commit()

        filing = Filing(**sample_filing)
        session.add(filing)
        session.commit()

        result = session.execute(
            select(Filing).where(Filing.ticker == "AAPL")
        ).scalars().all()
        assert len(result) == 1
        assert result[0].ticker == "AAPL"


class TestFilingContentModel:
    """Tests for the FilingContent model."""

    def test_create_content(self, session, sample_filing, sample_xbrl_data):
        """Test creating filing content."""
        filing = Filing(**sample_filing)
        session.add(filing)
        session.commit()

        content = FilingContent(
            filing_id=filing.id,
            accession_number=sample_filing["accession_number"],
            content_type="xbrl",
            content_data=str(sample_xbrl_data),
        )
        session.add(content)
        session.commit()

        result = session.execute(
            select(FilingContent).where(FilingContent.filing_id == filing.id)
        ).scalar_one()
        assert result.content_type == "xbrl"
        assert result.accession_number == sample_filing["accession_number"]
