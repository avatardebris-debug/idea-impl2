"""SEC filing content parsers.

Provides single and batch parsing for XBRL and HTML SEC filings.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .xbrl_parser import XBRLParser
from .html_parser import HTMLParser
from sec_importer.models import Filing

logger = logging.getLogger(__name__)

__all__ = [
    "XBRLParser",
    "HTMLParser",
    "parse_filing",
    "parse_filings",
    "parse_and_store",
    "parse_and_store_filings",
    "_parse_single_filing",
]

# Filing types that typically include XBRL data
XBRL_FILING_TYPES = {"10-K", "10-Q", "20-F", "11-K", "10-K/A", "10-Q/A", "20-F/A", "11-K/A"}


def _parse_single_filing(raw: Optional[dict]) -> Optional[Filing]:
    """Parse a single raw filing dict into a Filing ORM object.

    Args:
        raw: Raw filing dict from SEC API.

    Returns:
        Filing ORM object, or None if raw is None.
    """
    if raw is None:
        return None

    return Filing(
        ticker=raw.get("ticker", ""),
        filing_type=raw.get("form", raw.get("type", "")),
        filing_date=raw.get("filingDate", raw.get("filing_date", "")),
        accession_number=raw.get("accessionNumber", raw.get("accession_number", "")),
        document_url=raw.get("documentUrl", raw.get("document_url", "")),
        form_description=raw.get("formDescription", raw.get("form_description", "")),
        accepted_date=raw.get("acceptedDate", raw.get("accepted_date", "")),
        fill_url=raw.get("fillUrl", raw.get("fill_url", "")),
    )


def parse_filings(raw_filings: list[dict]) -> list[Filing]:
    """Normalize raw SEC filing dicts into Filing ORM objects.

    Args:
        raw_filings: List of dicts from SEC API (parallel arrays converted).

    Returns:
        List of Filing ORM objects.
    """
    if not raw_filings:
        return []

    return [_parse_single_filing(raw) for raw in raw_filings]


def parse_filing(filing: dict, content_type: str = "xbrl") -> dict:
    """Parse a single filing's content.

    Args:
        filing: Dict with filing metadata including document_url.
        content_type: 'xbrl' or 'html'.

    Returns:
        Dict with parse results.
    """
    url = filing.get("document_url", "")
    if not url:
        return {"status": "failed", "parse_error": "No document URL"}

    if content_type == "xbrl":
        parser = XBRLParser()
    else:
        parser = HTMLParser()

    try:
        result = parser.parse_from_url(url)
        return result
    finally:
        parser.close()


def parse_and_store(session, filing: Filing, content_type: str = "xbrl") -> dict:
    """Parse a filing's content and store it in the database.

    Args:
        session: SQLAlchemy session.
        filing: Filing ORM object.
        content_type: 'xbrl' or 'html'.

    Returns:
        Dict with parse status and result.
    """
    from sec_importer.storage import get_filing_content_data, upsert_filing_content

    # Check if content already exists
    existing = get_filing_content_data(session, filing.id, content_type)
    if existing and existing.get("parse_status") == "success":
        return {"status": "skipped", "parse_error": None}

    # Parse the filing
    url = filing.document_url or ""
    if not url:
        return {"status": "failed", "parse_error": "No document URL"}

    parser = None
    try:
        if content_type == "xbrl":
            parser = XBRLParser()
        else:
            parser = HTMLParser()

        result = parser.parse_from_url(url)
        parse_status = result.get("parse_status", "failed")
        parse_error = result.get("parse_error")

        # Store the result
        upsert_filing_content(
            session,
            filing_id=filing.id,
            content_type=content_type,
            content_data=result,
            parse_status=parse_status,
            parse_error=parse_error,
        )
        session.commit()

        return {
            "status": parse_status,
            "parse_error": parse_error,
            "sections": result.get("sections", {}),
        }
    except Exception as e:
        session.rollback()
        return {"status": "failed", "parse_error": str(e)}
    finally:
        if parser:
            parser.close()


def parse_and_store_filings(
    session,
    filings: list[Any],
    content_type: str = "xbrl",
    max_workers: int = 4,
) -> dict:
    """Parse XBRL/HTML content for a batch of filings and store results.

    Uses concurrent.futures.ThreadPoolExecutor for parallel downloads and parsing.

    Args:
        session: SQLAlchemy session.
        filings: List of Filing ORM objects or dicts with 'id' and 'document_url'.
        content_type: 'xbrl' or 'html'.
        max_workers: Number of concurrent threads.

    Returns:
        Summary dict with counts of parsed, failed, and skipped filings.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from sec_importer.storage import get_filing_content_data, upsert_filing_content
    from sec_importer.models import Filing

    if not filings:
        return {"parsed": 0, "failed": 0, "skipped": 0}

    # Filter to only filings that need parsing
    to_parse = []
    for f in filings:
        fid = f.id if isinstance(f, Filing) else f.get("id")
        url = f.document_url if isinstance(f, Filing) else f.get("document_url", "")
        if not url:
            continue
        existing = get_filing_content_data(session, fid, content_type)
        if existing and existing.get("parse_status") == "success":
            continue
        to_parse.append((fid, url))

    if not to_parse:
        return {"parsed": 0, "failed": 0, "skipped": len(filings)}

    summary = {"parsed": 0, "failed": 0, "skipped": 0}

    def _parse_one(args: tuple[int, str]) -> tuple[int, str, Optional[str]]:
        """Parse a single filing and return (filing_id, status, error)."""
        fid, url = args
        parser = None
        try:
            if content_type == "xbrl":
                parser = XBRLParser()
            else:
                parser = HTMLParser()

            result = parser.parse_from_url(url)
            parse_status = result.get("parse_status", "failed")
            parse_error = result.get("parse_error")

            upsert_filing_content(
                session,
                filing_id=fid,
                content_type=content_type,
                content_data=result,
                parse_status=parse_status,
                parse_error=parse_error,
            )
            return (fid, parse_status, parse_error)
        except Exception as e:
            return (fid, "failed", str(e))
        finally:
            if parser:
                parser.close()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_parse_one, args): args for args in to_parse}
        for future in as_completed(futures):
            fid, status, error = future.result()
            if status == "success":
                summary["parsed"] += 1
            else:
                summary["failed"] += 1
                logger.warning(f"Filing {fid} parse failed: {error}")

    summary["skipped"] = len(filings) - len(to_parse)
    return summary
