"""Tests for SEC Importer models."""

import pytest
from sec_importer.models import (
    CompanyModel,
    FilingModel,
    FilingItemModel,
    XBRLFactModel,
    FilingSchemaConfig,
)


class TestCompanyModel:
    def test_valid_company(self):
        company = CompanyModel(cik="12345", name="Test Corp", ticker="TEST")
        assert company.cik == "0000012345"
        assert company.name == "Test Corp"
        assert company.ticker == "TEST"

    def test_cik_zero_padding(self):
        company = CompanyModel(cik="1")
        assert company.cik == "0000000001"

    def test_empty_cik_raises(self):
        with pytest.raises(ValueError, match="CIK cannot be empty"):
            CompanyModel(cik="")

    def test_invalid_cik_raises(self):
        with pytest.raises(ValueError, match="Invalid CIK"):
            CompanyModel(cik="abc123")


class TestFilingModel:
    def test_valid_filing(self):
        filing = FilingModel(
            accession_no="0000320193-23-000106",
            cik="320193",
            filing_type="10-K",
        )
        assert filing.accession_no == "000032019323000106"
        assert filing.cik == "320193"
        assert filing.filing_type == "10-K"

    def test_accession_no_strips_dashes(self):
        filing = FilingModel(
            accession_no="0000320193-23-000106",
            cik="320193",
            filing_type="10-K",
        )
        assert "-" not in filing.accession_no

    def test_empty_accession_no_raises(self):
        with pytest.raises(ValueError, match="Accession number cannot be empty"):
            FilingModel(accession_no="", cik="123", filing_type="10-K")

    def test_invalid_accession_no_raises(self):
        with pytest.raises(ValueError, match="Invalid accession number"):
            FilingModel(accession_no="abc-def-ghi", cik="123", filing_type="10-K")


class TestFilingItemModel:
    def test_valid_item(self):
        item = FilingItemModel(filing_id=1, accession_no="000032019323000106", item_label="Item 1")
        assert item.filing_id == 1
        assert isinstance(item.filing_id, int)
        assert item.item_label == "Item 1"
        assert item.item_type == "text"

    def test_filing_id_is_int(self):
        item = FilingItemModel(filing_id=42, accession_no="123")
        assert item.filing_id == 42
        assert type(item.filing_id) is int

    def test_default_item_type(self):
        item = FilingItemModel(filing_id=1, accession_no="123")
        assert item.item_type == "text"


class TestXBRLFactModel:
    def test_valid_fact(self):
        fact = XBRLFactModel(
            filing_id=1,
            tag="us-gaap:Assets",
            value="1000000",
            unit="USD",
        )
        assert fact.tag == "us-gaap:Assets"
        assert fact.value == "1000000"
        assert fact.unit == "USD"

    def test_value_is_string(self):
        fact = XBRLFactModel(filing_id=1, tag="test", value=123)
        assert fact.value == "123"
        assert isinstance(fact.value, str)


class TestFilingSchemaConfig:
    def test_valid_config(self):
        config = FilingSchemaConfig(
            namespace="http://www.sec.gov/Archives/edgar/filerinfo",
            prefix="edgar",
        )
        assert config.namespace == "http://www.sec.gov/Archives/edgar/filerinfo"
        assert config.prefix == "edgar"

    def test_empty_namespace_raises(self):
        with pytest.raises(ValueError, match="Namespace cannot be empty"):
            FilingSchemaConfig(namespace="", prefix="test")
