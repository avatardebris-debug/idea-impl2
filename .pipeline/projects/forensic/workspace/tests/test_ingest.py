"""Tests for forensic ingest module."""

import json

import pytest
from forensic.models import IngestResult


class TestIngestResult:
    def test_creation(self):
        result = IngestResult(
            ticker="AAPL",
            cik="320193",
            accession_no="0000320193-23-000047",
            filing_date="2023-10-27",
            filing_type="10-K",
            item_count=10,
        )
        assert result.ticker == "AAPL"
        assert result.cik == "320193"
        assert result.accession_no == "0000320193-23-000047"
        assert result.filing_date == "2023-10-27"
        assert result.filing_type == "10-K"
        assert result.item_count == 10

    def test_to_json(self):
        result = IngestResult(
            ticker="AAPL",
            cik="320193",
            accession_no="0000320193-23-000047",
            filing_date="2023-10-27",
            filing_type="10-K",
            item_count=10,
        )
        j = result.to_json()
        d = json.loads(j)
        assert d["ticker"] == "AAPL"
        assert d["filing_type"] == "10-K"

    def test_to_json_all_fields(self):
        result = IngestResult(
            ticker="MSFT",
            cik="0000789019",
            accession_no="0000789019-23-000050",
            filing_date="2023-10-25",
            filing_type="10-Q",
            item_count=5,
        )
        j = result.to_json()
        d = json.loads(j)
        assert d["cik"] == "0000789019"
        assert d["accession_no"] == "0000789019-23-000050"
        assert d["filing_date"] == "2023-10-25"
        assert d["item_count"] == 5

    def test_to_json_defaults(self):
        result = IngestResult(
            ticker="TSLA", 
            cik="1318605", 
            accession_no="0001318605-23-000010",
            filing_type="10-K",
            filing_date="2023-01-01"
        )
        j = result.to_json()
        d = json.loads(j)
        assert d["filing_date"] == "2023-01-01"
        assert d["filing_type"] == "10-K"
        assert d["item_count"] == 0
