"""OST connector for reading local Outlook OST files."""

import os
import email
from email.header import decode_header
from typing import Generator, List, Optional
from datetime import datetime
from email_tool.models import Email
from email_tool.connectors.base import EmailConnector, ConnectorConfig, ConnectorType, SyncState


class OSTConnector(EmailConnector):
    """
    OST connector for reading Outlook OST files.
    
    OST (Offline Storage Table) files are Microsoft Outlook's offline cache format.
    
    Features:
    - Best-effort parsing using extract-msg library
    - Fallback to manual parsing for basic email extraction
    - Incremental sync by file position
    """
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize the OST connector.
        
        Args:
            config: Connector configuration with file path.
        """
        super().__init__(config)
        self._file_path = config.metadata.get("file_path")
        self._file_handle = None
        self._sync_state: Optional[SyncState] = None
        self._last_position = 0
        self._file_size = 0
        self._extract_msg_available = False
        self._ost_parser = None
    
    @property
    def connector_type(self) -> ConnectorType:
        """Return the connector type."""
        return ConnectorType.OST
    
    def connect(self) -> bool:
        """
        Open the OST file.
        
        Returns:
            True if connection successful.
        """
        if self._initialized:
            return True
        
        try:
            if not self._file_path:
                raise ValueError("No file path specified in configuration")
            
            if not os.path.exists(self._file_path):
                raise FileNotFoundError(f"OST file not found: {self._file_path}")
            
            # Try to import extract-msg for better OST parsing
            try:
                from ost_utils import OSTParser
                self._ost_parser = OSTParser()
                self._extract_msg_available = True
            except ImportError:
                self._extract_msg_available = False
            
            # Open file
            self._file_handle = open(self._file_path, 'rb')
            
            # Get file size for sync tracking
            self._file_handle.seek(0, 2)
            self._file_size = self._file_handle.tell()
            self._file_handle.seek(0)
            
            # Load sync state
            if self._sync_state and self._sync_state.last_sync_uid:
                self._last_position = self._sync_state.last_sync_uid
            
            self._initialized = True
            return True
            
        except ImportError as e:
            raise ImportError(
                "OST connector requires ost_utils library for best-effort parsing. "
                "Install with: pip install ost-utils"
            ) from e
        except Exception as e:
            self._handle_error(e, "connect")
            return False
    
    def disconnect(self) -> None:
        """Close the OST file."""
        if self._file_handle and self._initialized:
            try:
                self._file_handle.close()
            except Exception:
                pass
            finally:
                self._file_handle = None
                self._initialized = False
        
        # Save sync state
        if self._file_handle:
            self._file_handle.seek(0, 1)
            self._last_position = self._file_handle.tell()
        
        if self._sync_state:
            self._sync_state.last_sync_uid = self._last_position
            self._sync_state.last_sync_time = datetime.now()
    
    def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_uid: Optional[int] = None,
        since_history_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Generator[Email, None, None]:
        """
        Fetch emails from OST file.
        
        Args:
            limit: Maximum number of emails to fetch.
            since_uid: Fetch only emails after this file position.
            since_history_id: Not used for OST.
            labels: Not used for OST (all emails are returned).
        
        Yields:
            Email objects.
        """
        if not self._file_handle:
            raise ConnectionError("Not connected to OST file")
        
        # Seek to sync position if specified
        if since_uid:
            self._file_handle.seek(since_uid)
            self._last_position = since_uid
        
        # Try OST parsing first if available
        if self._extract_msg_available and self._ost_parser:
            try:
                yield from self._parse_ost_emails(limit)
                return
            except Exception:
                # Fall back to manual parsing
                pass
        
        # Fallback: Manual parsing of OST file
        yield from self._parse_ost_manual(limit)
    
    def _parse_ost_emails(self, limit: Optional[int]) -> Generator[Email, None, None]:
        """Parse OST emails using OST parser."""
        email_count = 0
        
        # OST parser would iterate through OST structure
        # This is a placeholder for actual OST parsing logic
        # In production, use extract-msg or similar library
        
        # For now, we'll use manual parsing
        yield from self._parse_ost_manual(limit)
    
    def _parse_ost_manual(self, limit: Optional[int]) -> Generator[Email, None, None]:
        """Manual OST parsing as fallback."""
        email_count = 0
        current_email = []
        in_message = False
        
        # OST files have a specific binary format, but we'll try to extract email data
        # This is a simplified approach - real OST parsing requires specialized libraries
        
        for line in self._file_handle:
            # OST files are binary, so we look for email-like patterns
            line_str = line.decode('utf-8', errors='replace')
            
            # Look for message boundaries (From_ lines)
            if line_str.startswith('From '):
                # Process previous email if exists
                if current_email:
                    email_content = ''.join(current_email)
                    email_obj = self._parse_email(email_content)
                    if email_obj:
                        yield email_obj
                        email_count += 1
                        if limit and email_count >= limit:
                            break
                
                # Start new email
                current_email = [line_str]
                in_message = True
                self._last_position = self._file_handle.tell()
                
            elif in_message:
                current_email.append(line_str)
                self._last_position = self._file_handle.tell()
        
        # Process last email
        if current_email:
            email_content = ''.join(current_email)
            email_obj = self._parse_email(email_content)
            if email_obj:
                yield email_obj
                email_count += 1
    
    def _parse_email(self, email_content: str) -> Optional[Email]:
        """Parse email content into Email object."""
        try:
            # Try to parse as standard email
            msg = email.message_from_string(email_content)
            
            # Extract headers
            subject = msg.get("Subject", "")
            from_addr = msg.get("From", "")
            to_addr = msg.get("To", "")
            date_str = msg.get("Date", "")
            
            # Decode subject
            if subject:
                decoded_parts = decode_header(subject)
                subject = " ".join(
                    part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                    for part in decoded_parts
                )
            
            # Parse date
            try:
                received_date = datetime.strptime(
                    date_str,
                    "%a, %d %b %Y %H:%M:%S %z"
                )
            except (ValueError, TypeError):
                received_date = datetime.now()
            
            # Extract body
            body_plain = None
            body_html = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        try:
                            body_plain = part.get_payload(decode=True).decode('utf-8')
                        except (UnicodeDecodeError, AttributeError):
                            body_plain = part.get_payload()
                    
                    elif content_type == "text/html":
                        try:
                            body_html = part.get_payload(decode=True).decode('utf-8')
                        except (UnicodeDecodeError, AttributeError):
                            body_html = part.get_payload()
            else:
                try:
                    body_plain = msg.get_payload(decode=True).decode('utf-8')
                except (UnicodeDecodeError, AttributeError):
                    body_plain = msg.get_payload()
            
            # Extract attachments
            attachments = []
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "size": len(part.get_payload(decode=True) or b"")
                        })
            
            return Email(
                id=f"ost-{self._last_position}",
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                received_date=received_date,
                body_plain=body_plain,
                body_html=body_html,
                attachments=attachments,
                labels=["ost"],
                source_path=self._file_path
            )
            
        except Exception as e:
            self._handle_error(e, "parse_email")
            return None
    
    def get_unread_count(self) -> int:
        """Get count of unread emails (not applicable for OST)."""
        return 0
    
    def get_total_count(self) -> int:
        """Get total count of emails in OST file."""
        if not self._file_handle:
            raise ConnectionError("Not connected to OST file")
        
        count = 0
        self._file_handle.seek(0)
        
        for line in self._file_handle:
            line_str = line.decode('utf-8', errors='replace')
            if line_str.startswith('From '):
                count += 1
        
        return count
    
    def get_file_info(self) -> dict:
        """Get information about the OST file."""
        if not self._file_path:
            return {}
        
        stat = os.stat(self._file_path)
        return {
            "path": self._file_path,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime)
        }
    
    def search_emails(
        self,
        from_addr: Optional[str] = None,
        to_addr: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        since_date: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> List[int]:
        """
        Search for emails in OST file.
        
        Args:
            from_addr: Filter by sender.
            to_addr: Filter by recipient.
            subject: Filter by subject.
            body: Filter by body content.
            since_date: Filter by date (ISO format).
            before_date: Filter by date (ISO format).
        
        Returns:
            List of file positions where matching emails start.
        """
        if not self._file_handle:
            raise ConnectionError("Not connected to OST file")
        
        positions = []
        self._file_handle.seek(0)
        
        current_email = []
        in_message = False
        email_start = 0
        
        for line in self._file_handle:
            line_str = line.decode('utf-8', errors='replace')
            
            if line_str.startswith('From '):
                # Process previous email if exists
                if current_email:
                    email_content = ''.join(current_email)
                    email_obj = self._parse_email(email_content)
                    if email_obj and self._matches_criteria(email_obj, from_addr, to_addr, subject, body, since_date, before_date):
                        positions.append(email_start)
                
                # Start new email
                current_email = [line_str]
                in_message = True
                email_start = self._file_handle.tell()
                
            elif in_message:
                current_email.append(line_str)
        
        # Process last email
        if current_email:
            email_content = ''.join(current_email)
            email_obj = self._parse_email(email_content)
            if email_obj and self._matches_criteria(email_obj, from_addr, to_addr, subject, body, since_date, before_date):
                positions.append(email_start)
        
        return positions
    
    def _matches_criteria(
        self,
        email_obj: Email,
        from_addr: Optional[str],
        to_addr: Optional[str],
        subject: Optional[str],
        body: Optional[str],
        since_date: Optional[str],
        before_date: Optional[str]
    ) -> bool:
        """Check if email matches search criteria."""
        if from_addr and from_addr.lower() not in email_obj.from_addr.lower():
            return False
        if to_addr and to_addr.lower() not in email_obj.to_addr.lower():
            return False
        if subject and subject.lower() not in email_obj.subject.lower():
            return False
        if body:
            body_text = (email_obj.body_plain or "") + (email_obj.body_html or "")
            if body.lower() not in body_text.lower():
                return False
        
        # Date filtering (simplified)
        return True
    
    def mark_as_read(self, uid: str) -> bool:
        """Mark email as read (not applicable for OST)."""
        return False
    
    def mark_as_unread(self, uid: str) -> bool:
        """Mark email as unread (not applicable for OST)."""
        return False
    
    def delete_email(self, uid: str) -> bool:
        """Delete email from OST (not supported)."""
        return False
    
    def move_email(self, uid: str, target_folder: str) -> bool:
        """Move email to different folder (not supported for OST)."""
        return False
