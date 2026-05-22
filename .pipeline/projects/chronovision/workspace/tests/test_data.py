"""Tests for the data layer."""

import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from chronovision.src.data.loader import DataLoader
from chronovision.src.data.sec_importer import SECImporter


class TestDataLoader:
    """Tests for DataLoader."""
    
    def test_init_with_db_url(self):
        """Test initialization with database URL."""
        loader = DataLoader(db_url="sqlite:///test.db")
        assert loader.db_url == "sqlite:///test.db"
    
    def test_init_without_db_url(self):
        """Test initialization without database URL."""
        loader = DataLoader()
        assert loader.db_url is None
    
    def test_get_all_tickers_empty(self):
        """Test getting all tickers from empty data."""
        loader = DataLoader()
        loader._load_data()
        tickers = loader.get_all_tickers()
        assert tickers == []
    
    def test_get_company(self):
        """Test getting company data."""
        loader = DataLoader()
        loader._load_data()
        
        # Add test data
        loader._companies = {
            "AAPL": {"company_name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
        }
        
        company = loader.get_company("AAPL")
        assert company is not None
        assert company["company_name"] == "Apple Inc."
    
    def test_get_company_not_found(self):
        """Test getting non-existent company."""
        loader = DataLoader()
        loader._load_data()
        company = loader.get_company("NONEXISTENT")
        assert company is None
    
    def test_get_stock_prices_empty(self):
        """Test getting stock prices with no data."""
        loader = DataLoader()
        loader._load_data()
        prices = loader.get_stock_prices("AAPL")
        assert prices.empty
    
    def test_get_financial_metrics_empty(self):
        """Test getting financial metrics with no data."""
        loader = DataLoader()
        loader._load_data()
        metrics = loader.get_latest_financial_metrics("AAPL")
        assert metrics == {}
    
    def test_get_filings_empty(self):
        """Test getting filings with no data."""
        loader = DataLoader()
        loader._load_data()
        filings = loader.get_filings(ticker="AAPL")
        assert filings.empty
    
    def test_get_prediction_dataset_empty(self):
        """Test getting prediction dataset with no data."""
        loader = DataLoader()
        loader._load_data()
        dataset = loader.get_prediction_dataset("AAPL", lookback=10, horizon=1)
        assert dataset["X"].size == 0
        assert dataset["y"].size == 0


class TestSECImporter:
    """Tests for SECImporter."""
    
    def test_init(self):
        """Test initialization."""
        importer = SECImporter(db_url="sqlite:///test.db")
        assert importer.db_url == "sqlite:///test.db"
    
    def test_import_all_data_empty(self):
        """Test importing data with no source."""
        importer = SECImporter()
        result = importer.import_all_data()
        assert result["status"] == "skipped"
        assert "No data source configured" in result["message"]
    
    def test_generate_synthetic_filings(self):
        """Test generating synthetic filings."""
        importer = SECImporter()
        importer.generate_synthetic_filings(10)
        assert len(importer._synthetic_filings) == 10
    
    def test_generate_synthetic_filings_invalid_count(self):
        """Test generating invalid number of filings."""
        importer = SECImporter()
        with pytest.raises(ValueError):
            importer.generate_synthetic_filings(-1)
    
    def test_generate_synthetic_filing_structure(self):
        """Test structure of generated synthetic filing."""
        importer = SECImporter()
        filing = importer._generate_single_synthetic_filing()
        
        assert "ticker" in filing
        assert "company_name" in filing
        assert "filing_type" in filing
        assert "filing_date" in filing
        assert "financial_metrics" in filing
        assert "sentiment" in filing
        assert "key_events" in filing


class TestFixtures:
    """Tests for fixture data."""
    
    def test_synthetic_filtures_load(self):
        """Test loading synthetic fixtures."""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "data",
            "fixtures",
            "synthetic_filings.json"
        )
        assert os.path.exists(fixture_path)
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        assert "filings" in data
        assert len(data["filings"]) > 0
