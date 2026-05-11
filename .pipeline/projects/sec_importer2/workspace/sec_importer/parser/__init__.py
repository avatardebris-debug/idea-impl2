"""SEC filing content parsers."""

from .xbrl_parser import XBRLParser
from .html_parser import HTMLParser

__all__ = ["XBRLParser", "HTMLParser"]


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


def parse_and_store(session, filing_id: int, content_type: str = "xbrl") -> dict:
    """Parse a filing's content and store it in the database.

    Args:
        session: SQLAlchemy session.
        filing_id: ID of the Filing record.
        content_type: 'xbrl' or 'html'.

    Returns:
        Dict with parse status and result.
    """
    from sec_importer.storage import get_filing_content_data, upsert_filing_content
    from sec_importer.models import Filing
    from sqlalchemy import select

    # Get the filing record
    filing = session.execute(select(Filing).where(Filing.id == filing_id)).scalar_one_or_none()
    if not filing:
        return {"status": "failed", "parse_error": f"Filing {filing_id} not found"}

    # Check if content already exists
    existing = get_filing_content_data(session, filing_id, content_type)
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
        parse_status = result.get("status", "failed")
        parse_error = result.get("parse_error")

        # Store the result
        upsert_filing_content(
            session,
            filing_id=filing_id,
            content_type=content_type,
            content_data=result,
            parse_status=parse_status,
            parse_error=parse_error,
        )
        session.commit()

        return {
            "status": parse_status,
            "parse_error": parse_error,
        }
    except Exception as e:
        session.rollback()
        return {"status": "failed", "parse_error": str(e)}
    finally:
        if parser:
            parser.close()
