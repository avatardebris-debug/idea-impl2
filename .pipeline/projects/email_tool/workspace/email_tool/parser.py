"""Email parser for reading .eml files and extracting email content."""

import email
from email import policy
from email.parser import BytesParser, Parser
from email.message import EmailMessage
from email.header import decode_header
from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from email_tool.models import Email


def _decode_mime_word(value: str) -> str:
    """Decode MIME encoded words (e.g., =?UTF-8?B?VGhpcyA=?=)."""
    if not value:
        return ""
    
    decoded_parts = []
    for encoded_text, encoding in decode_header(value):
        if isinstance(encoded_text, bytes):
            try:
                decoded_parts.append(encoded_text.decode(encoding or 'utf-8'))
            except (UnicodeDecodeError, LookupError):
                decoded_parts.append(encoded_text.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(encoded_text)
    
    return ''.join(decoded_parts)


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse email date string into datetime object."""
    if not date_str:
        return None
    
    try:
        # Try RFC 2822 format first
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed
    except (ValueError, TypeError):
        pass
    
    # Try common formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def _get_header_value(msg: EmailMessage, header_name: str) -> Optional[str]:
    """Get a header value, decoding MIME encoded words if necessary."""
    value = msg.get(header_name)
    if value:
        return _decode_mime_word(value)
    return None


def _get_addresses(msg: EmailMessage, header_name: str) -> List[str]:
    """Get email addresses from a header, handling multiple addresses."""
    value = msg.get(header_name)
    if not value:
        return []
    
    # Parse address headers (From, To, Cc, Bcc)
    # email.utils.getaddresses() expects a list of strings, not a single string
    # email.utils.parseaddr() parses a single address and returns (display_name, email)
    addresses = []
    
    # Parse each address individually
    for addr_str in str(value).split(','):
        addr_str = addr_str.strip()
        if addr_str:
            display_name, email_addr = email.utils.parseaddr(addr_str)
            if email_addr:  # Only add if there's a valid email address
                addresses.append(email_addr)
    
    return addresses


def _extract_attachments(msg: EmailMessage) -> List[str]:
    """Extract attachment filenames from email."""
    attachments = []
    
    for part in msg.walk():
        # Skip multipart containers
        if part.get_content_maintype() == 'multipart':
            continue
        
        # Check if this is an attachment by looking at Content-Disposition header
        disposition = part.get('Content-Disposition')
        if disposition:
            try:
                disposition_lower = disposition.lower()
                # Count as attachment if disposition says 'attachment' or 'inline'
                if 'attachment' in disposition_lower or 'inline' in disposition_lower:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(_decode_mime_word(filename))
            except Exception:
                continue
    
    return attachments


def _extract_body_parts(msg: EmailMessage) -> Tuple[Optional[str], Optional[str]]:
    """Extract plain text and HTML body parts from email."""
    body_plain = None
    body_html = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Skip attachments
            if 'attachment' in content_disposition.lower():
                continue
            
            if content_type == 'text/plain' and body_plain is None:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_plain = payload.decode('utf-8', errors='replace')
                    else:
                        body_plain = payload
                except Exception:
                    body_plain = part.get_payload()
            elif content_type == 'text/html' and body_html is None:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_html = payload.decode('utf-8', errors='replace')
                    else:
                        body_html = payload
                except Exception:
                    body_html = part.get_payload()
    else:
        # Single part email
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8', errors='replace')
            
            if content_type == 'text/plain':
                body_plain = payload
            elif content_type == 'text/html':
                body_html = payload
            else:
                # Unknown content type, treat as plain text
                body_plain = payload
        except Exception:
            body_plain = msg.get_payload()
    
    # Strip whitespace from body content
    if body_plain:
        body_plain = body_plain.strip()
    if body_html:
        body_html = body_html.strip()
    
    # Return None for body fields if they are empty strings
    if body_plain == '':
        body_plain = None
    if body_html == '':
        body_html = None
    
    return body_plain, body_html


def parse_email_file(filepath: str | Path) -> Optional[Email]:
    """
    Parse an .eml file and return an Email object.
    
    Args:
        filepath: Path to the .eml file.
    
    Returns:
        Email object if parsing succeeds, None otherwise.
    """
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Email file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        return _parse_email_message(msg)
    except Exception as e:
        print(f"Error parsing email file {filepath}: {e}")
        return None


def parse_email_content(content: str | bytes) -> Optional[Email]:
    """
    Parse email content (string or bytes) and return an Email object.
    
    Args:
        content: Email content as string or bytes.
    
    Returns:
        Email object if parsing succeeds, None otherwise.
    """
    try:
        if isinstance(content, str):
            msg = Parser(policy=policy.default).parsestr(content)
        else:
            msg = BytesParser(policy=policy.default).parsebytes(content)
        
        return _parse_email_message(msg)
    except Exception as e:
        print(f"Error parsing email content: {e}")
        return None


def _parse_email_message(msg: EmailMessage) -> Email:
    """Parse an email message into an Email object."""
    # Extract headers
    from_addr = _get_header_value(msg, 'From') or ''
    to_addrs = _get_addresses(msg, 'To')
    subject = _get_header_value(msg, 'Subject') or ''
    date = _parse_date(_get_header_value(msg, 'Date'))
    
    # Extract body parts
    body_plain, body_html = _extract_body_parts(msg)
    
    # Extract attachments
    attachments = _extract_attachments(msg)
    
    # Collect raw headers
    raw_headers = {}
    for key in ['From', 'To', 'Cc', 'Bcc', 'Subject', 'Date', 'Message-ID', 
                'In-Reply-To', 'References', 'X-Priority', 'Importance']:
        value = msg.get(key)
        if value:
            raw_headers[key] = _decode_mime_word(value)
    
    # Convert empty strings to None for body fields
    if body_plain == '':
        body_plain = None
    if body_html == '':
        body_html = None
    
    return Email(
        from_addr=from_addr,
        to_addrs=to_addrs,
        subject=subject,
        date=date,
        body_plain=body_plain,
        body_html=body_html,
        attachments=attachments,
        raw_headers=raw_headers
    )


class EmailParser:
    """Parser class for email files and content."""
    
    def __init__(self):
        """Initialize the email parser."""
        pass
    
    def parse_batch(self, directory: str | Path) -> List[Email]:
        """
        Parse all .eml files in a directory (recursively).
        
        Args:
            directory: Path to directory containing .eml files.
        
        Returns:
            List of Email objects.
        """
        directory = Path(directory)
        if not directory.exists():
            return []
        
        emails = []
        for eml_file in directory.rglob("*.eml"):
            email = self.parse_file(eml_file)
            if email:
                emails.append(email)
        
        return emails
    
    def parse(self, source: str | Path | bytes) -> Optional[Email]:
        """
        Parse email from a file path or content string/bytes.
        
        Args:
            source: Path to .eml file or email content string/bytes.
        
        Returns:
            Email object if parsing succeeds, None otherwise.
        """
        if isinstance(source, bytes):
            return self.parse_content(source)
        elif isinstance(source, str):
            # If the string contains newlines it's email content, not a path
            if '\n' in source:
                return self.parse_content(source)
            else:
                return self.parse_file(source)
        else:
            # Path object
            return self.parse_file(source)
    
    @staticmethod
    def parse_file(filepath: str | Path) -> Optional[Email]:
        """
        Parse an .eml file and return an Email object.
        
        Args:
            filepath: Path to the .eml file.
        
        Returns:
            Email object if parsing succeeds, None otherwise.
        """
        return parse_email_file(filepath)
    
    @staticmethod
    def parse_content(content: str | bytes) -> Optional[Email]:
        """
        Parse email content (string or bytes) and return an Email object.
        
        Args:
            content: Email content as string or bytes.
        
        Returns:
            Email object if parsing succeeds, None otherwise.
        """
        return parse_email_content(content)
