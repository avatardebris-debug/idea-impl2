"""Parser for SEC EDGAR Full-Text Search API responses."""

from __future__ import annotations

from typing import Any

from osint_corp.models.entities import Filing


class SECParser:
    """Parse raw SEC API JSON responses into structured Filing objects."""

    @staticmethod
    def parse_response(raw: dict[str, Any]) -> list[Filing]:
        """Parse a SEC API response dict into a list of Filing objects."""
        filings = []
        hits = raw.get("hits", {}).get("hits", [])
        if not hits:
            return filings

        for hit in hits:
            source = hit.get("source", {})
            filing = Filing(
                company_name=source.get("companyName", ""),
                ticker=source.get("ticker", ""),
                cik=source.get("cik", ""),
                filing_type=source.get("formType", ""),
                filing_date=source.get("filingDate", ""),
                accession_number=source.get("accessionNumber", ""),
                url=source.get("url", ""),
                source="sec_edgar",
                metadata=source,
            )
            filings.append(filing)
        return filings

    @staticmethod
    def parse_latest(raw: dict[str, Any]) -> list[Filing]:
        """Parse the 'latest' endpoint response."""
        return SECParser.parse_response(raw)
