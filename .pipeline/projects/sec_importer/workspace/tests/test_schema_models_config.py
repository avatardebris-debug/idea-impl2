"""Unit tests for schema, models, and config (Phase 2 Task 1)."""

import os
import sys
import tempfile
import pathlib

# Inject src path
_ws = pathlib.Path(__file__).parent
_src = _ws / ".." / "src"
if str(_src.resolve()) not in sys.path:
    sys.path.insert(0, str(_src.resolve()))

import pytest
import sqlite3
from sec_importer.schema import init_db, CREATE_COMPANIES_TABLE, CREATE_FILINGS_TABLE, CREATE_FILING_ITEMS_TABLE
from sec_importer.models import CompanyModel, FilingModel, FilingItemModel
from sec_importer.config import Config


# --- Schema tests ---

class TestSchema:
    def test_init_db_creates_tables(self, tmp_path):
        """Test init_db creates all tables."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "companies" in tables
        assert "filings" in tables
        assert "filing_items" in tables

    def test_init_db_creates_indexes(self, tmp_path):
        """Test init_db creates indexes."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "idx_filings_cik" in indexes
        assert "idx_filings_type" in indexes
        assert "idx_filings_date" in indexes
        assert "idx_filings_accession" in indexes

    def test_init_db_creates_primary_keys(self, tmp_path):
        """Test tables have correct primary keys."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(companies)")
        companies_cols = {row[1]: row[5] for row in cursor.fetchall()}
        assert companies_cols["cik"] == 1  # pk

        cursor.execute("PRAGMA table_info(filings)")
        filings_cols = {row[1]: row[5] for row in cursor.fetchall()}
        assert filings_cols["id"] == 1
        # accession_no is UNIQUE (not PK), so pk=0
        assert filings_cols["accession_no"] == 0

        cursor.execute("PRAGMA table_info(filing_items)")
        items_cols = {row[1]: row[5] for row in cursor.fetchall()}
        assert items_cols["id"] == 1
        conn.close()

    def test_init_db_with_existing_db(self, tmp_path):
        """Test init_db doesn't fail on existing database."""
        db_path = str(tmp_path / "test.db")
        conn1 = init_db(db_path)
        conn1.close()
        conn2 = init_db(db_path)
        conn2.close()


# --- Model tests ---

class TestCompanyModel:
    def test_valid_company(self):
        """Test valid company data validates."""
        company = CompanyModel(
            cik="0000320193",
            name="Apple Inc.",
            ticker="AAPL",
            sic="0000320193",
            industry="Technology",
            state="CA",
        )
        assert company.cik == "0000320193"
        assert company.name == "Apple Inc."

    def test_cik_padded(self):
        """Test CIK is zero-padded to 10 digits."""
        company = CompanyModel(cik="320193")
        assert company.cik == "0000320193"

    def test_invalid_cik(self):
        """Test invalid CIK raises validation error."""
        with pytest.raises(Exception):  # ValidationError
            CompanyModel(cik="abc123")

    def test_minimal_company(self):
        """Test company with only required field."""
        company = CompanyModel(cik="0000320193")
        assert company.cik == "0000320193"
        assert company.name is None

    def test_empty_cik(self):
        """Test empty CIK raises validation error."""
        with pytest.raises(Exception):
            CompanyModel(cik="")


class TestFilingModel:
    def test_valid_filing(self):
        """Test valid filing data validates."""
        filing = FilingModel(
            accession_no="0000320193-21-000099",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2021-01-29",
            accepted_date="20210129162513",
            file_url="https://www.sec.gov/Archives/edgar/full-text/000032019321000099.txt",
            is_xbrl=True,
        )
        assert filing.accession_no == "000032019321000099"
        assert filing.is_xbrl is True

    def test_accession_no_strips_dashes(self):
        """Test accession number dashes are stripped."""
        filing = FilingModel(
            accession_no="0000320193-21-000099",
            cik="0000320193",
            filing_type="10-K",
        )
        assert filing.accession_no == "000032019321000099"

    def test_invalid_accession_no(self):
        """Test invalid accession number raises error."""
        with pytest.raises(Exception):
            FilingModel(accession_no="abc", cik="0000320193", filing_type="10-K")

    def test_minimal_filing(self):
        """Test filing with only required fields."""
        filing = FilingModel(
            accession_no="000032019321000099",
            cik="0000320193",
            filing_type="10-K",
        )
        assert filing.filing_date is None
        assert filing.is_xbrl is False


class TestFilingItemModel:
    def test_valid_item(self):
        """Test valid filing item validates."""
        item = FilingItemModel(
            filing_id=1,
            accession_no="000032019321000099",
            item_label="Item 1",
            item_content="Business description...",
            item_type="text",
        )
        assert item.filing_id == 1
        assert item.item_label == "Item 1"

    def test_invalid_filing_id(self):
        """Test filing_id must be > 0."""
        with pytest.raises(Exception):
            FilingItemModel(filing_id=0, accession_no="000032019321000099")

    def test_minimal_item(self):
        """Test item with only required fields."""
        item = FilingItemModel(filing_id=1, accession_no="000032019321000099")
        assert item.item_label is None


# --- Config tests ---

class TestConfig:
    def test_defaults_loaded(self):
        """Test default values are applied."""
        config = Config()
        assert config.requests_per_second == 10
        assert config.rate_limit_delay == 0.1
        assert config.max_retries == 3
        assert config.base_backoff == 1.0
        assert config.log_level == "INFO"
        assert config.batch_size == 10
        assert config.timeout == 30

    def test_load_from_file(self, tmp_path):
        """Test loading config from YAML file."""
        config_content = """
database:
  db_path: /custom/path/test.db
rate_limiting:
  requests_per_second: 5
  max_retries: 5
logging:
  level: DEBUG
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)

        config = Config(str(config_file))
        assert config.db_path == "/custom/path/test.db"
        assert config.requests_per_second == 5
        assert config.max_retries == 5
        assert config.log_level == "DEBUG"
        # Unspecified keys should use defaults
        assert config.rate_limit_delay == 0.1

    def test_missing_file_uses_defaults(self):
        """Test missing config file falls back to defaults."""
        config = Config("/nonexistent/path/config.yaml")
        assert config.requests_per_second == 10
        assert config.db_path == "sec_importer.db"

    def test_to_dict(self):
        """Test to_dict returns full config."""
        config = Config()
        d = config.to_dict()
        assert "database" in d
        assert "rate_limiting" in d
        assert "logging" in d
        assert "importer" in d
