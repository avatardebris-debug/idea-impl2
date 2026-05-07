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
        assert repo.exists_by_cik("0000000000") is False
        conn.close()


class TestFilingRepository:
    def test_upsert_and_get(self, tmp_path):
        """Test upsert and retrieval of a filing."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        # Insert company first (FK constraint)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        repo = FilingRepository(conn)

        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            accepted_date="2024-10-25T16:30:00",
            file_url="https://example.com/filing.html",
            is_xbrl=True,
        )
        repo.upsert(filing)

        result = repo.get_by_accession_no("0000320193-24-000047")
        assert result is not None
        assert result["filing_type"] == "10-K"
        conn.close()

    def test_upsert_updates_existing(self, tmp_path):
        """Test upsert updates an existing filing."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        repo = FilingRepository(conn)

        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing.html",
        )
        repo.upsert(filing)

        # Update the filing
        filing.filing_type = "10-K (Updated)"
        repo.upsert(filing)

        result = repo.get_by_accession_no("0000320193-24-000047")
        assert result["filing_type"] == "10-K (Updated)"
        conn.close()

    def test_exists_by_accession_no(self, tmp_path):
        """Test exists_by_accession_no."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        repo = FilingRepository(conn)

        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing.html",
        )
        repo.upsert(filing)

        assert repo.exists_by_accession_no("0000320193-24-000047") is True
        assert repo.exists_by_accession_no("0000000000-00-000000") is False
        conn.close()

    def test_get_new_filings(self, tmp_path):
        """Test get_new_filings returns filings with file_url."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        repo = FilingRepository(conn)

        # Insert filings with and without file_url
        filing1 = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing1.html",
        )
        filing2 = FilingModel(
            accession_no="0000320193-24-000048",
            cik="0000320193",
            filing_type="10-Q",
            filing_date="2024-10-26",
            file_url=None,
        )
        repo.upsert(filing1)
        repo.upsert(filing2)

        results = repo.get_new_filings()
        assert len(results) == 1
        # Model strips dashes from accession_no
        assert results[0]["accession_no"] == "000032019324000047"
        conn.close()

    def test_get_new_filings_with_filters(self, tmp_path):
        """Test get_new_filings with filters."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        repo = FilingRepository(conn)

        filing1 = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing1.html",
        )
        filing2 = FilingModel(
            accession_no="0000320193-24-000048",
            cik="0000320193",
            filing_type="10-Q",
            filing_date="2024-10-26",
            file_url="https://example.com/filing2.html",
        )
        repo.upsert(filing1)
        repo.upsert(filing2)

        # Filter by filing_type
        results = repo.get_new_filings(filing_type="10-K")
        assert len(results) == 1
        assert results[0]["filing_type"] == "10-K"

        # Filter by cik
        results = repo.get_new_filings(cik="0000320193")
        assert len(results) == 2
        conn.close()


class TestFilingItemRepository:
    def test_upsert_and_get(self, tmp_path):
        """Test upsert and retrieval of a filing item."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        # Insert company and filing first
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        filing_repo = FilingRepository(conn)
        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing.html",
        )
        filing_id = filing_repo.upsert(filing)

        repo = FilingItemRepository(conn)

        item = FilingItemModel(
            filing_id=filing_id,
            accession_no="0000320193-24-000047",
            item_label="Item 1A",
            item_content="Risk factors...",
            item_type="text",
        )
        repo.upsert(item)

        results = repo.get_by_filing_id(filing_id)
        assert len(results) == 1
        assert results[0]["item_label"] == "Item 1A"
        conn.close()

    def test_bulk_insert(self, tmp_path):
        """Test bulk insert of filing items."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        filing_repo = FilingRepository(conn)
        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing.html",
        )
        filing_id = filing_repo.upsert(filing)

        repo = FilingItemRepository(conn)

        items = [
            FilingItemModel(
                filing_id=filing_id,
                accession_no="0000320193-24-000047",
                item_label=f"Item {i}",
                item_content=f"Content {i}",
                item_type="text",
            )
            for i in range(5)
        ]
        count = repo.bulk_insert(items)
        assert count == 5

        results = repo.get_by_filing_id(filing_id)
        assert len(results) == 5
        conn.close()

    def test_bulk_insert_empty(self, tmp_path):
        """Test bulk insert with empty list."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        repo = FilingItemRepository(conn)

        count = repo.bulk_insert([])
        assert count == 0
        conn.close()


class TestDeduplicationManager:
    def test_mark_and_check_seen(self):
        """Test marking and checking seen items."""
        conn = sqlite3.connect(":memory:")
        dedup = DeduplicationManager(conn)

        dedup.mark_seen_accession("0000320193-24-000047")
        assert dedup.is_accession_seen("0000320193-24-000047") is True
        assert dedup.is_accession_seen("0000000000-00-000000") is False

        dedup.mark_seen_cik("0000320193")
        assert dedup.is_cik_seen("0000320193") is True
        assert dedup.is_cik_seen("0000000000") is False
        conn.close()

    def test_is_in_db(self, tmp_path):
        """Test checking if items exist in database."""
        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        dedup = DeduplicationManager(conn)

        # Insert a company first
        company_repo = CompanyRepository(conn)
        company_repo.upsert(CompanyModel(cik="0000320193", name="Apple Inc."))

        # Insert a filing
        filing_repo = FilingRepository(conn)
        filing = FilingModel(
            accession_no="0000320193-24-000047",
            cik="0000320193",
            filing_type="10-K",
            filing_date="2024-10-25",
            file_url="https://example.com/filing.html",
        )
        filing_repo.upsert(filing)

        assert dedup.is_accession_in_db("0000320193-24-000047") is True
        assert dedup.is_accession_in_db("0000000000-00-000000") is False
        assert dedup.is_cik_in_db("0000320193") is True
        assert dedup.is_cik_in_db("0000000000") is False
        conn.close()


class TestRateLimiter:
    def test_acquire_tokens(self):
        """Test token acquisition."""
        limiter = RateLimiter(requests_per_second=100)
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start
        # Should be very fast since tokens start full
        assert elapsed < 0.1

    def test_rate_limiting(self):
        """Test that rate limiting actually delays requests."""
        limiter = RateLimiter(requests_per_second=10)
        # Exhaust tokens
        for _ in range(10):
            limiter.acquire()

        # Next acquire should take some time
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05  # At least 0.1s for 10 req/s

    def test_wait_between(self):
        """Test wait_between delays appropriately."""
        limiter = RateLimiter(delay=0.05)
        last_time = time.monotonic() - 0.01  # Just 10ms ago
        start = time.monotonic()
        limiter.wait_between(last_time)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.03  # Should wait ~0.04s

    def test_execute_with_retry_success(self):
        """Test execute_with_retry on success."""
        limiter = RateLimiter()
        call_count = 0

        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = limiter.execute_with_retry(success_func)
        assert result == "success"
        assert call_count == 1

    def test_execute_with_retry_failure(self):
        """Test execute_with_retry raises after max retries."""
        limiter = RateLimiter(max_retries=2)

        def failing_func():
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            limiter.execute_with_retry(failing_func)

    def test_reset(self):
        """Test resetting the token bucket."""
        limiter = RateLimiter(requests_per_second=10)
        # Exhaust tokens
        for _ in range(10):
            limiter.acquire()

        assert limiter.available_tokens < 1.0
        limiter.reset()
        assert limiter.available_tokens >= 10.0

    def test_available_tokens(self):
        """Test available_tokens property."""
        limiter = RateLimiter(requests_per_second=10)
        assert limiter.available_tokens >= 10.0

        limiter.acquire()
        # Should have slightly less than 10 due to time elapsed
        assert limiter.available_tokens < 10.5


class TestSECDatabase:
    def test_context_manager(self, tmp_path):
        """Test SECDatabase as context manager."""
        db_path = str(tmp_path / "test.db")
        with SECDatabase(db_path) as db:
            assert db.conn is not None
            assert db.rate_limiter is not None
            assert db.companies is not None
            assert db.filings is not None
            assert db.items is not None
            assert db.dedup is not None

    def test_full_workflow(self, tmp_path):
        """Test a full import workflow."""
        db_path = str(tmp_path / "test.db")
        with SECDatabase(db_path) as db:
            # Insert company
            company = CompanyModel(
                cik="0000320193",
                name="Apple Inc.",
                ticker="AAPL",
                sic="3571",
                industry="Consumer Electronics",
                state="CA",
            )
            company_id = db.companies.upsert(company)
            assert company_id > 0

            # Insert filing
            filing = FilingModel(
                accession_no="0000320193-24-000047",
                cik="0000320193",
                filing_type="10-K",
                filing_date="2024-10-25",
                accepted_date="2024-10-25T16:30:00",
                file_url="https://example.com/filing.html",
                is_xbrl=True,
            )
            filing_id = db.filings.upsert(filing)
            assert filing_id > 0

            # Insert filing items
            items = [
                FilingItemModel(
                    filing_id=filing_id,
                    accession_no="0000320193-24-000047",
                    item_label="Item 1A",
                    item_content="Risk factors...",
                    item_type="text",
                ),
                FilingItemModel(
                    filing_id=filing_id,
                    accession_no="0000320193-24-000047",
                    item_label="Item 7",
                    item_content="Management discussion...",
                    item_type="text",
                ),
            ]
            db.items.bulk_insert(items)

            # Verify
            company_result = db.companies.get_by_cik("0000320193")
            assert company_result is not None
            assert company_result["name"] == "Apple Inc."

            filing_result = db.filings.get_by_accession_no("0000320193-24-000047")
            assert len(filing_result) == 1
            assert filing_result[0]["filing_type"] == "10-K"

            items_result = db.items.get_by_filing_id(filing_id)
            assert len(items_result) == 2

    def test_deduplication_prevents_duplicates(self, tmp_path):
        """Test that deduplication prevents duplicate filings."""
        db_path = str(tmp_path / "test.db")
        with SECDatabase(db_path) as db:
            # Insert company first
            company = CompanyModel(cik="0000320193", name="Apple Inc.")
            db.companies.upsert(company)

            filing = FilingModel(
                accession_no="0000320193-24-000047",
                cik="0000320193",
                filing_type="10-K",
                filing_date="2024-10-25",
                file_url="https://example.com/filing.html",
            )

            # Insert twice
            id1 = db.filings.upsert(filing)
            id2 = db.filings.upsert(filing)

            # Should return same ID (upsert behavior)
            assert id1 == id2

            # Only one record in DB
            results = db.filings.get_by_accession_no("0000320193-24-000047")
            assert len(results) == 1
