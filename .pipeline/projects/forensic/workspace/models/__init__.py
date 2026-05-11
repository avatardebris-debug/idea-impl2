"""Forensic ingest models."""

from dataclasses import dataclass, field


@dataclass
class IngestResult:
    """Result of ingesting a filing."""
    ticker: str
    cik: str
    accession_no: str
    filing_date: str = None
    filing_type: str = None
    item_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
            "filing_type": self.filing_type,
            "item_count": self.item_count,
        }
