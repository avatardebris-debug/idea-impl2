"""Tests for sec_importer integration."""

import pytest
from unittest.mock import MagicMock, patch


class TestSECImporter:
    @patch("sec_importer.api.resolve_ticker_to_cik")
    def test_resolve_ticker(self, mock_resolve):
        mock_resolve.return_value = "320193"
        from sec_importer.api import resolve_ticker_to_cik
        cik = resolve_ticker_to_cik("AAPL")
        assert cik == "320193"

    @patch("sec_importer.api.get_latest_filing")
    def test_get_latest_filing(self, mock_filing):
        mock_filing.return_value = {
            "accession_no": "0000320193-23-000047",
            "filing_type": "10-K",
            "filing_date": "2023-10-27",
        }
        from sec_importer.api import get_latest_filing
        filing = get_latest_filing("320193", "10-K")
        assert filing is not None
        assert filing["filing_type"] == "10-K"

    def test_filing_item_model(self):
        from sec_importer.models import FilingItemModel
        item = FilingItemModel(
            item_label="Item 1",
            item_content="Some content",
            item_type="text",
        )
        assert item.item_label == "Item 1"
        assert item.item_content == "Some content"
        assert item.item_type == "text"

    def test_filing_item_model_to_dict(self):
        from sec_importer.models import FilingItemModel
        item = FilingItemModel(
            item_label="Item 1",
            item_content="Some content",
            item_type="text",
        )
        d = item.to_dict()
        assert d["item_label"] == "Item 1"
        assert d["item_content"] == "Some content"
