"""Integration tests for repository layer and rate limiter (Phase 2 Task 2)."""

import sys
import time
import tempfile
import pathlib
import sqlite3

# Inject src path
_ws = pathlib.Path(__file__).parent
_src = _ws / ".." / "src"
if str(_src.resolve()) not in sys.path:
    sys.path.insert(0, str(_src.resolve()))

import pytest
from sec_importer.schema import init_db
from sec_importer.models import CompanyModel, FilingModel, FilingItemModel
from sec_importer.repository import (
    SECDatabase,
    CompanyRepository,
    FilingRepository,
    FilingItemRepository,
    DeduplicationManager,
)
from sec_importer.rate_limiter import RateLimiter


# --- Repository tests ---

class TestCompanyRepository:
    def test_upsert_and_get(self, tmp_path):
        """Test upsert and retrieval of a company."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = CompanyRepository(conn)

        company = CompanyModel(
            cik="0000320193",
            name="Apple Inc.",
            ticker="AAPL",
            sic="3571",
            industry="Consumer Electronics",
            state="CA",
        )
        repo.upsert(company)

        result = repo.get_by_cik("0000320193")
        assert result is not None
        assert result["name"] == "Apple Inc."
        assert result["ticker"] == "AAPL"
        conn.close()

    def test_upsert_updates_existing(self, tmp_path):
        """Test upsert updates an existing company."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = CompanyRepository(conn)

        company = CompanyModel(cik="0000320193", name="Apple Inc.", ticker="AAPL")
        repo.upsert(company)

        # Update the company
        company.name = "Apple Inc. (Updated)"
        repo.upsert(company)

        result = repo.get_by_cik("0000320193")
        assert result["name"] == "Apple Inc. (Updated)"
        conn.close()

    def test_exists_by_cik(self, tmp_path):
        """Test exists_by_cik."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = CompanyRepository(conn)

        company = CompanyModel(cik="0000320193", name="Apple Inc.")
        repo.upsert(company)

        assert repo.exists_by_cik("0000320193") is True
        assert repo.exists_by_cik("0000999999") is False
        conn.close()


class TestFilingRepository:
    def test_upsert_and_get(self, tmp_path):
        """Test upsert and retrieval of a filing."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingRepository(conn)

        # Insert company first (FK requirement)
        conn.execute(
            "INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            ("0000320193", "Apple Inc.", "AAPL"),
        )
        conn.commit()

        filing = FilingModel(
            accession_no="0000320193-21-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2021-10-29",
            accepted_date="2021-10-29T16:08:27",
            file_url="https://www.sec.gov/Archives/edgar/data/320193/000032019321000047/0000320193-21-000047-index.htm",
            is_xbrl=True,
        )
        repo.upsert(filing)

        results = repo.get_by_accession_no("0000320193-21-000047")
        assert len(results) == 1
        assert results[0]["filing_type"] == "10-K"
        conn.close()

    def test_exists_by_accession_no(self, tmp_path):
        """Test exists_by_accession_no."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingRepository(conn)

        # Insert company first (FK requirement)
        conn.execute(
            "INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            ("0000320193", "Apple Inc.", "AAPL"),
        )
        conn.commit()

        filing = FilingModel(
            accession_no="0000320193-21-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2021-10-29",
        )
        repo.upsert(filing)

        assert repo.exists_by_accession_no("0000320193-21-000047") is True
        assert repo.exists_by_accession_no("0000999999-21-000001") is False
        conn.close()

    def test_get_new_filings(self, tmp_path):
        """Test get_new_filings returns filings with file_url."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingRepository(conn)

        # Insert company first (FK requirement)
        conn.execute(
            "INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            ("0000320193", "Apple Inc.", "AAPL"),
        )
        conn.commit()

        # Filing with file_url
        filing1 = FilingModel(
            accession_no="0000320193-21-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2021-10-29",
            file_url="https://example.com/filing1.htm",
        )
        repo.upsert(filing1)

        # Filing without file_url
        filing2 = FilingModel(
            accession_no="0000320193-21-000048",
            cik="0000320193",
            filing_type="10-Q",
            filing_date="2022-01-28",
        )
        repo.upsert(filing2)

        new_filings = repo.get_new_filings()
        assert len(new_filings) == 1
        assert new_filings[0]["accession_no"] == "000032019321000047"
        conn.close()


class TestFilingItemRepository:
    def test_upsert_and_get(self, tmp_path):
        """Test upsert and retrieval of a filing item."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingItemRepository(conn)

        # Insert company and filing first (FK requirements)
        conn.execute(
            "INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            ("0000320193", "Apple Inc.", "AAPL"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO filings (accession_no, cik, filing_type, filing_date) VALUES (?, ?, ?, ?)",
            ("0000320193-21-000047", "0000320193", "10-K", "2021-10-29"),
        )
        conn.commit()

        item = FilingItemModel(
            filing_id="0000320193-21-000047",
            accession_no="0000320193-21-000047",
            item_label="Item 1",
            item_content="Business overview content",
            item_type="text",
        )
        repo.upsert(item)

        results = repo.get_by_filing_id("0000320193-21-000047")
        assert len(results) == 1
        assert results[0]["item_label"] == "Item 1"
        conn.close()

    def test_bulk_insert(self, tmp_path):
        """Test bulk insert of filing items."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingItemRepository(conn)

        # Insert company and filing first (FK requirements)
        conn.execute(
            "INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            ("0000320193", "Apple Inc.", "AAPL"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO filings (accession_no, cik, filing_type, filing_date) VALUES (?, ?, ?, ?)",
            ("0000320193-21-000047", "0000320193", "10-K", "2021-10-29"),
        )
        conn.commit()

        items = [
            FilingItemModel(filing_id="0000320193-21-000047", accession_no="0000320193-21-000047", item_label="Item 1", item_content="Content 1"),
            FilingItemModel(filing_id="0000320193-21-000047", accession_no="0000320193-21-000047", item_label="Item 1A", item_content="Content 2"),
            FilingItemModel(filing_id="0000320193-21-000047", accession_no="0000320193-21-000047", item_label="Item 7", item_content="Content 3"),
        ]
        ids = repo.bulk_insert(items)
        assert len(ids) == 3

        results = repo.get_by_filing_id("0000320193-21-000047")
        assert len(results) == 3
        conn.close()


class TestDeduplicationManager:
    def test_mark_and_check_cik(self, tmp_path):
        """Test marking and checking CIK deduplication."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        dedup = DeduplicationManager(conn)

        assert dedup.mark_cik_seen("0000320193") is True
        assert dedup.mark_cik_seen("0000320193") is False  # Duplicate
        assert dedup.is_cik_seen("0000320193") is True
        assert dedup.is_cik_seen("0000999999") is False
        conn.close()

    def test_mark_and_check_accession(self, tmp_path):
        """Test marking and checking accession deduplication."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        dedup = DeduplicationManager(conn)

        assert dedup.mark_accession_seen("0000320193-21-000047") is True
        assert dedup.mark_accession_seen("0000320193-21-000047") is False  # Duplicate
        assert dedup.is_accession_seen("0000320193-21-000047") is True
        assert dedup.is_accession_seen("0000999999-21-000001") is False
        conn.close()

    def test_is_cik_in_db(self, tmp_path):
        """Test is_cik_in_db checks the companies table."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        dedup = DeduplicationManager(conn)

        # Insert a company
        conn.execute("INSERT INTO companies (cik, name) VALUES (?, ?)", ("0000320193", "Apple"))
        conn.commit()

        assert dedup.is_cik_in_db("0000320193") is True
        assert dedup.is_cik_in_db("0000999999") is False
        conn.close()

    def test_is_accession_in_db(self, tmp_path):
        """Test is_accession_in_db checks the filings table."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        dedup = DeduplicationManager(conn)

        # Insert company first (FK requirement)
        conn.execute("INSERT OR IGNORE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
                     ("0000320193", "Apple Inc.", "AAPL"))
        conn.commit()

        # Insert a filing
        conn.execute("INSERT INTO filings (accession_no, cik, filing_type, filing_date) VALUES (?, ?, ?, ?)",
                     ("000032019321000047", "0000320193", "10-K", "2021-10-29"))
        conn.commit()

        assert dedup.is_accession_in_db("0000320193-21-000047") is True
        assert dedup.is_accession_in_db("0000999999-21-000001") is False
        conn.close()


class TestSECDatabase:
    def test_context_manager(self, tmp_path):
        """Test SECDatabase context manager initializes all repositories."""
        db_path = str(tmp_path / "test.db")
        with SECDatabase(db_path) as db:
            assert db.conn is not None
            assert db.companies is not None
            assert db.filings is not None
            assert db.items is not None
            assert db.dedup is not None
            assert db.rate_limiter is not None

    def test_upsert_company_via_sec_db(self, tmp_path):
        """Test upserting a company through SECDatabase."""
        db_path = str(tmp_path / "test.db")
        with SECDatabase(db_path) as db:
            company = CompanyModel(cik="0000320193", name="Apple Inc.", ticker="AAPL")
            db.companies.upsert(company)

            result = db.companies.get_by_cik("0000320193")
            assert result is not None
            assert result["name"] == "Apple Inc."


# --- Rate Limiter tests ---

class TestRateLimiter:
    def test_basic_acquire(self):
        """Test basic token acquisition."""
        rl = RateLimiter(requests_per_second=10)
        rl.acquire()
        assert rl.available_tokens < 1.0

    def test_wait(self):
        """Test wait method."""
        rl = RateLimiter(delay=0.01)
        start = time.monotonic()
        rl.wait()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.005  # Should have waited at least some time

    def test_wait_between(self):
        """Test wait_between method."""
        rl = RateLimiter(requests_per_second=10)
        last_time = time.monotonic() - 0.5  # 0.5 seconds ago
        start = time.monotonic()
        rl.wait_between(last_time)
        elapsed = time.monotonic() - start
        # Should have waited ~0.5 seconds
        assert elapsed >= 0.4

    def test_execute_with_retry(self):
        """Test execute_with_retry with successful call."""
        rl = RateLimiter(requests_per_second=10, max_retries=2)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = rl.execute_with_retry(func)
        assert result == "success"
        assert call_count == 1

    def test_execute_with_retry_retries_on_failure(self):
        """Test execute_with_retry retries on failure."""
        rl = RateLimiter(requests_per_second=10, max_retries=2, base_backoff=0.01)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = rl.execute_with_retry(func)
        assert result == "success"
        assert call_count == 2

    def test_execute_with_retry_exhausts_retries(self):
        """Test execute_with_retry raises after exhausting retries."""
        rl = RateLimiter(requests_per_second=10, max_retries=2, base_backoff=0.01)

        def func():
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            rl.execute_with_retry(func)

    def test_reset(self):
        """Test reset method."""
        rl = RateLimiter(requests_per_second=10)
        rl.acquire()
        assert rl.available_tokens < 1.0
        rl.reset()
        assert rl.available_tokens == 10.0

    def test_context_manager(self):
        """Test rate limiter as context manager."""
        with RateLimiter() as rl:
            assert rl is not None

    def test_invalid_requests_per_second(self):
        """Test that invalid requests_per_second raises ValueError."""
        with pytest.raises(ValueError):
            RateLimiter(requests_per_second=0)

    def test_invalid_delay(self):
        """Test that invalid delay raises ValueError."""
        with pytest.raises(ValueError):
            RateLimiter(delay=-1)

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises ValueError."""
        with pytest.raises(ValueError):
            RateLimiter(max_retries=-1)
