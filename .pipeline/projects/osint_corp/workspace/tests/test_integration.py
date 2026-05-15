"""
test_integration.py — Phase 3 integration tests for OSINT Corp.

Tests the full pipeline: models → sources → correlation → reporting.
No external APIs required (uses mock data).
"""

import json
import sys
import pathlib
import tempfile

import pytest

# Ensure project root is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from osint_corp.models.entities import (
    Company, Filing, Relationship, Location, Manifest, Contract, JobPosting,
)
from osint_corp.correlation import (
    correlate, deduplicate_companies, find_companies_by_name, _name_similarity,
)
from osint_corp.pipeline.orchestrator import PipelineOrchestrator
from osint_corp.reports.generator import ReportGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_companies():
    return [
        Company(name="Apple Inc", ticker="AAPL", cik="0000320193", source="sec"),
        Company(name="Microsoft Corporation", ticker="MSFT", cik="0000789019", source="sec"),
        Company(name="Apple Inc.", jurisdiction="US-CA", source="registry"),
        Company(name="Alphabet Inc", ticker="GOOGL", cik="0001652044", source="sec"),
    ]


@pytest.fixture
def sample_filings():
    return [
        Filing(company_name="Apple Inc.", filing_type="10-K",
               accession_number="0000320193-23-000106", filing_date="2023-11-03",
               ticker="AAPL", cik="0000320193"),
        Filing(company_name="Microsoft Corporation", filing_type="10-K",
               accession_number="0000789019-23-000012", filing_date="2023-07-27",
               ticker="MSFT", cik="0000789019"),
        Filing(company_name="Alphabet Inc.", filing_type="10-Q",
               accession_number="0001652044-23-000094", filing_date="2023-11-03",
               ticker="GOOGL", cik="0001652044"),
    ]


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_company_roundtrip(self):
        c = Company(name="Test Corp", ticker="TST", cik="123")
        d = c.to_dict()
        c2 = Company.from_dict(d)
        assert c2.name == "Test Corp"
        assert c2.ticker == "TST"
        assert c2.cik == "123"

    def test_company_json_roundtrip(self):
        c = Company(name="Test Corp", ticker="TST")
        j = c.to_json()
        c2 = Company.from_json(j)
        assert c2.name == c.name
        assert c2.ticker == c.ticker

    def test_filing_roundtrip(self):
        f = Filing(company_name="Apple", filing_type="10-K",
                   accession_number="ACC-001", ticker="AAPL")
        d = f.to_dict()
        f2 = Filing.from_dict(d)
        assert f2.company_name == "Apple"
        assert f2.filing_type == "10-K"
        assert f2.accession_number == "ACC-001"

    def test_relationship_roundtrip(self):
        r = Relationship(source_type="Company", source_id="AAPL",
                         target_type="Company", target_id="MSFT",
                         relationship_type="co_filer", confidence=0.8)
        d = r.to_dict()
        r2 = Relationship.from_dict(d)
        assert r2.relationship_type == "co_filer"
        assert r2.confidence == 0.8

    def test_location_model(self):
        loc = Location(city="Cupertino", state="CA", country="US",
                       latitude=37.33, longitude=-122.03)
        d = loc.to_dict()
        assert d["city"] == "Cupertino"
        loc2 = Location.from_dict(d)
        assert loc2.latitude == 37.33

    def test_manifest_model(self, sample_companies, sample_filings):
        m = Manifest(entities=sample_companies, filings=sample_filings)
        assert len(m.entities) == 4
        assert len(m.filings) == 3
        d = m.to_dict()
        assert "created_at" in d

    def test_contract_model(self):
        c = Contract(contract_type="lease", counterparty="Landlord LLC",
                     value=1_000_000, currency="USD")
        d = c.to_dict()
        assert d["value"] == 1_000_000
        c2 = Contract.from_dict(d)
        assert c2.counterparty == "Landlord LLC"

    def test_job_posting_model(self):
        jp = JobPosting(title="Data Engineer", company_name="Apple Inc",
                        location="Cupertino, CA", salary_min=150_000)
        d = jp.to_dict()
        assert d["title"] == "Data Engineer"
        jp2 = JobPosting.from_dict(d)
        assert jp2.salary_min == 150_000


# ---------------------------------------------------------------------------
# Correlation Tests
# ---------------------------------------------------------------------------

class TestCorrelation:
    def test_name_similarity_exact(self):
        assert _name_similarity("Apple Inc", "Apple Inc") == 1.0

    def test_name_similarity_normalized(self):
        score = _name_similarity("Apple Inc", "apple incorporated")
        assert score > 0.8  # Should normalize both

    def test_name_similarity_different(self):
        score = _name_similarity("Apple Inc", "Microsoft Corp")
        assert score < 0.5

    def test_correlate_by_ticker(self, sample_companies, sample_filings):
        rels = correlate(sample_companies, sample_filings)
        # Should find filing→company relationships via ticker match
        filed_by = [r for r in rels if r.relationship_type == "filed_by"]
        assert len(filed_by) >= 2  # AAPL + MSFT at minimum

    def test_correlate_co_filers(self, sample_companies, sample_filings):
        rels = correlate(sample_companies, sample_filings)
        co_filers = [r for r in rels if r.relationship_type == "co_filer"]
        # AAPL and GOOGL filed on same date (2023-11-03)
        assert len(co_filers) >= 1

    def test_deduplicate_companies(self, sample_companies):
        unique = deduplicate_companies(sample_companies)
        # Apple Inc and Apple Inc. should deduplicate
        assert len(unique) < len(sample_companies)
        tickers = [c.ticker for c in unique if c.ticker]
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_find_companies_by_name(self, sample_companies):
        matches = find_companies_by_name(sample_companies, "apple", threshold=0.5)
        assert len(matches) >= 1
        assert any("apple" in (m.name or "").lower() for m in matches)

    def test_correlate_empty_inputs(self):
        rels = correlate([], [])
        assert rels == []

    def test_correlate_no_matches(self):
        companies = [Company(name="Unknown Corp", ticker="UNK")]
        filings = [Filing(company_name="Other Inc", filing_type="10-K",
                          ticker="OTH", accession_number="ACC-999")]
        rels = correlate(companies, filings)
        # May still create a filed_by for the filing, but no co-filer
        co_filers = [r for r in rels if r.relationship_type == "co_filer"]
        assert len(co_filers) == 0


# ---------------------------------------------------------------------------
# Pipeline Orchestrator Tests
# ---------------------------------------------------------------------------

class TestPipelineOrchestrator:
    def test_orchestrator_instantiates(self):
        orch = PipelineOrchestrator()
        assert orch is not None

    def test_orchestrator_has_run_method(self):
        assert hasattr(PipelineOrchestrator, "run_pipeline")


# ---------------------------------------------------------------------------
# Report Generator Tests
# ---------------------------------------------------------------------------

class TestReportGenerator:
    def test_generator_instantiates(self):
        gen = ReportGenerator()
        assert gen is not None

    def test_generator_has_generate_method(self):
        assert hasattr(ReportGenerator, "generate_report")


# ---------------------------------------------------------------------------
# CLI Import Tests
# ---------------------------------------------------------------------------

class TestCLIImports:
    def test_cli_module_importable(self):
        from osint_corp import cli
        assert hasattr(cli, "app")

    def test_all_models_importable(self):
        from osint_corp.models.entities import (
            Company, Filing, Relationship, Location, Manifest, Contract, JobPosting
        )
        assert Company is not None
        assert Filing is not None

    def test_sources_importable(self):
        from osint_corp.sources import sec_importer
        from osint_corp.sources import corporate_registry
        assert sec_importer is not None
        assert corporate_registry is not None

    def test_analysis_importable(self):
        from osint_corp.analysis import financial, network, risk
        assert financial is not None


# ---------------------------------------------------------------------------
# JSON Export / File I/O Tests
# ---------------------------------------------------------------------------

class TestFileIO:
    def test_manifest_to_file(self, sample_companies, sample_filings):
        rels = correlate(sample_companies, sample_filings)
        m = Manifest(entities=sample_companies, filings=sample_filings, relationships=rels)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(m.to_json())
            path = f.name
        # Read back
        with open(path) as f:
            data = json.load(f)
        assert "entities" in data
        assert "filings" in data
        assert "relationships" in data
        pathlib.Path(path).unlink()

    def test_company_list_export(self, sample_companies):
        data = [c.to_dict() for c in sample_companies]
        j = json.dumps(data, indent=2)
        loaded = json.loads(j)
        assert len(loaded) == 4
        reconstructed = [Company.from_dict(d) for d in loaded]
        assert reconstructed[0].name == "Apple Inc"
