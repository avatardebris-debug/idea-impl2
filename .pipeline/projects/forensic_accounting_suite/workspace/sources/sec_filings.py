"""SEC filing data source with mock/sample data."""

from __future__ import annotations

from datetime import date
from typing import Optional

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.core.models import SEC_Filing


# ------------------------------------------------------------------
# Mock / sample SEC filing data
# ------------------------------------------------------------------

_SAMPLE_FILINGS: list[dict] = [
    {
        "filing_id": "SEC-20240001",
        "accession_number": "0001234567-24-000001",
        "company_name": "Acme Holdings Inc",
        "company_cik": "0001234567",
        "filing_type": "10-K",
        "filing_date": date(2024, 3, 30),
        "period_end_date": date(2023, 12, 31),
        "document_url": "https://www.sec.gov/Archives/edgar/data/1234567/000123456724000001.htm",
        "sic_code": "5013",
        "industry": "Wholesale - Durable Goods",
        "revenue": 50000000.0,
        "net_income": 5000000.0,
        "total_assets": 100000000.0,
        "total_liabilities": 40000000.0,
        "shareholders_equity": 60000000.0,
        "filing_text_summary": "Annual report with strong revenue growth driven by international expansion.",
        "source_db": "SEC EDGAR",
    },
    {
        "filing_id": "SEC-20240002",
        "accession_number": "0001234567-24-000002",
        "company_name": "Acme Holdings Inc",
        "company_cik": "0001234567",
        "filing_type": "10-Q",
        "filing_date": date(2024, 5, 15),
        "period_end_date": date(2024, 3, 31),
        "document_url": "https://www.sec.gov/Archives/edgar/data/1234567/000123456724000002.htm",
        "sic_code": "5013",
        "industry": "Wholesale - Durable Goods",
        "revenue": 12000000.0,
        "net_income": 1200000.0,
        "total_assets": 105000000.0,
        "total_liabilities": 42000000.0,
        "shareholders_equity": 63000000.0,
        "filing_text_summary": "Q1 2024 quarterly report showing continued growth.",
        "source_db": "SEC EDGAR",
    },
    {
        "filing_id": "SEC-20240003",
        "accession_number": "0001234568-24-000001",
        "company_name": "Titan Defense Systems",
        "company_cik": "0001234568",
        "filing_type": "10-K",
        "filing_date": date(2024, 4, 15),
        "period_end_date": date(2023, 12, 31),
        "document_url": "https://www.sec.gov/Archives/edgar/data/1234568/000123456824000001.htm",
        "sic_code": "3364",
        "industry": "Machinery, Military Combat Vehicles",
        "revenue": 200000000.0,
        "net_income": 20000000.0,
        "total_assets": 500000000.0,
        "total_liabilities": 200000000.0,
        "shareholders_equity": 300000000.0,
        "filing_text_summary": "Annual report highlighting defense contract wins and R&D investments.",
        "source_db": "SEC EDGAR",
    },
    {
        "filing_id": "SEC-20240004",
        "accession_number": "0001234569-24-000001",
        "company_name": "Global Procurement Services LLC",
        "company_cik": "0001234569",
        "filing_type": "8-K",
        "filing_date": date(2024, 6, 1),
        "period_end_date": None,
        "document_url": "https://www.sec.gov/Archives/edgar/data/1234569/000123456924000001.htm",
        "sic_code": "5416",
        "industry": "Services-Prepackaged Software",
        "revenue": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "shareholders_equity": None,
        "filing_text_summary": "Current report announcing a major government contract award.",
        "source_db": "SEC EDGAR",
    },
    {
        "filing_id": "SEC-20240005",
        "accession_number": "0001234570-24-000001",
        "company_name": "Meridian Logistics GmbH",
        "company_cik": "0001234570",
        "filing_type": "20-F",
        "filing_date": date(2024, 8, 1),
        "period_end_date": date(2023, 12, 31),
        "document_url": "https://www.sec.gov/Archives/edgar/data/1234570/000123457024000001.htm",
        "sic_code": "4931",
        "industry": "Warehouse, Custodial Operations",
        "revenue": 75000000.0,
        "net_income": 7500000.0,
        "total_assets": 150000000.0,
        "total_liabilities": 50000000.0,
        "shareholders_equity": 100000000.0,
        "filing_text_summary": "Annual report for foreign private issuer with operations across Europe.",
        "source_db": "SEC EDGAR",
    },
]


class SEC_FilingSource(DataSource[SEC_Filing]):
    """Mock SEC filing data source."""

    def __init__(self, entries: Optional[list[dict]] = None):
        self._entries: list[SEC_Filing] = [
            SEC_Filing(**e) for e in (entries or _SAMPLE_FILINGS)
        ]

    def query(self, **kwargs) -> list[SEC_Filing]:
        """Filter SEC filings by keyword arguments.

        Supported filters:
            company_name (str) — case-insensitive partial match
            company_cik (str) — exact match
            filing_type (str) — case-insensitive partial match
            filing_date_from (date) — inclusive start
            filing_date_to (date) — inclusive end
            min_revenue (float) — minimum revenue
            max_revenue (float) — maximum revenue
            min_net_income (float) — minimum net_income
            max_net_income (float) — maximum net_income
            keyword (str) — case-insensitive search across all text fields
        """
        results = list(self._entries)

        company_name = kwargs.get("company_name")
        if company_name:
            results = [
                e for e in results
                if company_name.lower() in e.company_name.lower()
            ]

        company_cik = kwargs.get("company_cik")
        if company_cik:
            results = [e for e in results if e.company_cik == company_cik]

        filing_type = kwargs.get("filing_type")
        if filing_type:
            results = [
                e for e in results
                if filing_type.lower() in e.filing_type.lower()
            ]

        filing_from = kwargs.get("filing_date_from")
        if filing_from:
            results = [
                e for e in results
                if e.filing_date and e.filing_date >= filing_from
            ]

        filing_to = kwargs.get("filing_date_to")
        if filing_to:
            results = [
                e for e in results
                if e.filing_date and e.filing_date <= filing_to
            ]

        min_revenue = kwargs.get("min_revenue")
        if min_revenue is not None:
            results = [
                e for e in results
                if e.revenue is not None and e.revenue >= min_revenue
            ]

        max_revenue = kwargs.get("max_revenue")
        if max_revenue is not None:
            results = [
                e for e in results
                if e.revenue is not None and e.revenue <= max_revenue
            ]

        min_net_income = kwargs.get("min_net_income")
        if min_net_income is not None:
            results = [
                e for e in results
                if e.net_income is not None and e.net_income >= min_net_income
            ]

        max_net_income = kwargs.get("max_net_income")
        if max_net_income is not None:
            results = [
                e for e in results
                if e.net_income is not None and e.net_income <= max_net_income
            ]

        keyword = kwargs.get("keyword")
        if keyword:
            kw_lower = keyword.lower()

            def _match_keyword(e: SEC_Filing) -> bool:
                text_fields = [
                    e.filing_id, e.accession_number, e.company_name,
                    e.company_cik, e.filing_type, e.document_url,
                    e.sic_code, e.industry, e.filing_text_summary,
                ]
                return any(kw_lower in (t or "").lower() for t in text_fields)

            results = [e for e in results if _match_keyword(e)]

        return results

    def fetch_all(self) -> list[SEC_Filing]:
        return list(self._entries)

    def get_by_id(self, record_id: str) -> SEC_Filing | None:
        for entry in self._entries:
            if entry.filing_id == record_id:
                return entry
        return None
