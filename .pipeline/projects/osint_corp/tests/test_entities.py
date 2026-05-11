"""Tests for models/entities module."""

import pytest
from osint_corp.models.entities import Company, Filing, Relationship


class TestCompany:
    """Tests for the Company model."""

    def test_create_company(self):
        """Test creating a Company instance."""
        company = Company(
            name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            sector="Technology",
        )
        assert company.name == "Test Corp"
        assert company.ticker == "TEST"
        assert company.cik == "0000000001"
        assert company.sector == "Technology"
        assert company.industry is None
        assert company.metadata == {}

    def test_create_company_minimal(self):
        """Test creating a Company with minimal fields."""
        company = Company(name="Minimal Corp")
        assert company.name == "Minimal Corp"
        assert company.ticker is None
        assert company.cik is None

    def test_company_to_dict(self):
        """Test Company serialization."""
        company = Company(
            name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            sector="Technology",
            metadata={"key": "value"},
        )
        d = company.to_dict()
        assert d["name"] == "Test Corp"
        assert d["ticker"] == "TEST"
        assert d["metadata"]["key"] == "value"

    def test_company_from_dict(self):
        """Test Company deserialization."""
        d = {
            "name": "Test Corp",
            "ticker": "TEST",
            "cik": "0000000001",
            "sector": "Technology",
            "industry": "Software",
            "metadata": {"key": "value"},
        }
        company = Company.from_dict(d)
        assert company.name == "Test Corp"
        assert company.ticker == "TEST"
        assert company.sector == "Technology"
        assert company.metadata["key"] == "value"

    def test_company_str(self):
        """Test Company string representation."""
        company = Company(name="Test Corp", ticker="TEST")
        assert "Test Corp" in str(company)
        assert "TEST" in str(company)


class TestFiling:
    """Tests for the Filing model."""

    def test_create_filing(self):
        """Test creating a Filing instance."""
        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            accession_number="0000000001-24-000001",
            url="https://example.com/filing",
        )
        assert filing.company_cik == "0000000001"
        assert filing.filing_type == "10-K"
        assert filing.accession_number == "0000000001-24-000001"

    def test_create_filing_minimal(self):
        """Test creating a Filing with minimal fields."""
        filing = Filing(company_cik="0000000001", filing_type="10-K")
        assert filing.company_cik == "0000000001"
        assert filing.filing_type == "10-K"

    def test_filing_to_dict(self):
        """Test Filing serialization."""
        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            metadata={"key": "value"},
        )
        d = filing.to_dict()
        assert d["company_cik"] == "0000000001"
        assert d["filing_type"] == "10-K"
        assert d["metadata"]["key"] == "value"

    def test_filing_from_dict(self):
        """Test Filing deserialization."""
        d = {
            "company_cik": "0000000001",
            "filing_type": "10-K",
            "filing_date": "2024-01-15",
            "accession_number": "0000000001-24-000001",
            "url": "https://example.com/filing",
            "metadata": {"key": "value"},
        }
        filing = Filing.from_dict(d)
        assert filing.company_cik == "0000000001"
        assert filing.filing_type == "10-K"
        assert filing.metadata["key"] == "value"


class TestRelationship:
    """Tests for the Relationship model."""

    def test_create_relationship(self):
        """Test creating a Relationship instance."""
        rel = Relationship(
            source_name="Company A",
            target_name="Company B",
            relationship_type="subsidiary",
            strength=0.8,
        )
        assert rel.source_name == "Company A"
        assert rel.target_name == "Company B"
        assert rel.relationship_type == "subsidiary"
        assert rel.strength == 0.8

    def test_create_relationship_minimal(self):
        """Test creating a Relationship with minimal fields."""
        rel = Relationship(source_name="A", target_name="B")
        assert rel.source_name == "A"
        assert rel.target_name == "B"
        assert rel.strength == 0.5  # default

    def test_relationship_to_dict(self):
        """Test Relationship serialization."""
        rel = Relationship(
            source_name="A",
            target_name="B",
            relationship_type="parent",
            metadata={"key": "value"},
        )
        d = rel.to_dict()
        assert d["source_name"] == "A"
        assert d["relationship_type"] == "parent"
        assert d["metadata"]["key"] == "value"

    def test_relationship_from_dict(self):
        """Test Relationship deserialization."""
        d = {
            "source_name": "A",
            "target_name": "B",
            "relationship_type": "subsidiary",
            "strength": 0.9,
            "metadata": {"key": "value"},
        }
        rel = Relationship.from_dict(d)
        assert rel.source_name == "A"
        assert rel.strength == 0.9
        assert rel.metadata["key"] == "value"
