"""IMAP connector for fetching emails from IMAP servers."""

import imaplib
import email
from email.header import decode_header
from typing import Generator, List, Optional
from email_tool.models import Email
from email_tool.connectors.base import EmailConnector, ConnectorConfig, ConnectorType, SyncState


class IMAPConnector(EmailConnector):
    """
    IMAP connector for fetching emails from IMAP servers.
    
    Supports:
    - SSL/TLS connections
    - Incremental sync by UID
    - Folder/mailbox selection
    - Search by various criteria
    """
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize the IMAP connector.
        
        Args:
            config: Connector configuration with host, port, username, password.
        """
        super().__init__(config)
        self._client: Optional[imaplib.IMAP4_SSL] = None
        self._mailbox = config.metadata.get("mailbox", "INBOX")
        self._search_criteria = config.metadata.get("search_criteria", "ALL")
        self._fetch_body = config.metadata.get("fetch_body", True)
        self._sync_state: Optional[SyncState] = None
    
    @property
    def connector_type(self) -> ConnectorType:
        """Return the connector type."""
        return ConnectorType.IMAP
    
    def connect(self) -> bool:
        """
        Establish connection to IMAP server.
        
        Returns:
            True if connection successful.
        """
        if self._initialized:
            return True
        
        try:
            host = self.config.metadata.get("host")
            port = self.config.metadata.get("port", 993)
            username = self.config.metadata.get("username")
            password = self.config.metadata.get("password")
            
            if not all([host, username, password]):
                raise ValueError("Missing required IMAP credentials")
            
            # Connect with SSL
            self._client = imaplib.IMAP4_SSL(host, port, timeout=self.config.timeout)
            self._client.login(username, password)
            
            # Select mailbox
            status, _ = self._client.select(self._mailbox)
            if status != "OK":
                raise ConnectionError(f"Failed to select mailbox: {self._mailbox}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            self._handle_error(e, "connect")
            return False
    
    def disconnect(self) -> None:
        """Close the IMAP connection."""
        if self._client and self._initialized:
            try:
                self._client.close()
                self._client.logout()
            except Exception:
                pass
            finally:
                self._client = None
                self._initialized = False
    
    def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_uid: Optional[int] = None,
        since_history_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Generator[Email, None, None]:
        """
        Fetch emails from IMAP server.
        
        Args:
            limit: Maximum number of emails to fetch.
            since_uid: Fetch only emails with UID greater than this.
            since_history_id: Not used for IMAP.
            labels: Not used for IMAP (use search_criteria instead).
        
        Yields:
            Email objects.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        # Build search criteria
        search_parts = [self._search_criteria]
        
        # Add UID range if specified
        if since_uid:
            search_parts.append(f"UID>{since_uid}")
        
        # Apply limit
        if limit:
            search_parts.append(f"UID<=+{limit}")  # Fetch recent emails
        
        search_query = " ".join(search_parts)
        
        # Search for emails
        status, data = self._client.search(None, search_query)
        
        if status != "OK":
            raise ConnectionError(f"IMAP search failed: {data}")
        
        # Get UID validity
        status, uid_validity_data = self._client.uid('VALIDITY')
        uid_validity = int(uid_validity_data[0].decode()) if uid_validity_data else None
        
        # Fetch email UIDs
        uid_list = data[0].split()
        
        # Fetch email headers and bodies
        for uid in uid_list:
            if limit and len(list(self._fetch_emails_with_uid(uid, uid_validity))) >= limit:
                break
            
            yield from self._fetch_emails_with_uid(uid, uid_validity)
            
            # Apply rate limiting
            self._apply_rate_limit()
    
    def _fetch_emails_with_uid(
        self,
        uid: bytes,
        uid_validity: Optional[int]
    ) -> Generator[Email, None, None]:
        """Fetch a single email by UID."""
        uid_str = uid.decode()
        
        # Fetch email
        status, data = self._client.uid('FETCH', uid_str, '(BODY.PEEK[] FLAGS)')
        
        if status != "OK":
            return
        
        # Parse email data
        email_data = data[0]
        if isinstance(email_data, tuple):
            raw_email = email_data[1]
        else:
            raw_email = email_data
        
        # Parse email
        msg = email.message_from_bytes(raw_email)
        
        # Extract email information
        email_obj = self._parse_email(msg, uid_str, uid_validity)
        
        if email_obj:
            yield email_obj
    
    def _parse_email(
        self,
        msg: email.message.Message,
        uid: str,
        uid_validity: Optional[int]
    ) -> Optional[Email]:
        """Parse email message into Email object."""
        try:
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
            from datetime import datetime
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
            
            # Extract labels (IMAP flags)
            flags = msg.get("X-IMAP-FLAGS", "")
            labels = []
            if flags:
                if "\\Seen" not in flags:
                    labels.append("unread")
                if "\\Flagged" in flags:
                    labels.append("flagged")
                if "\\Answered" in flags:
                    labels.append("answered")
                if "\\Draft" in flags:
                    labels.append("draft")
            
            return Email(
                id=f"imap-{uid}",
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                received_date=received_date,
                body_plain=body_plain,
                body_html=body_html,
                attachments=attachments,
                labels=labels,
                source_path=None,
                uid=uid,
                uid_validity=uid_validity
            )
            
        except Exception as e:
            self._handle_error(e, "parse_email")
            return None
    
    def get_unread_count(self) -> int:
        """Get count of unread emails."""
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, data = self._client.uid('SEARCH', None, '(UNSEEN)')
        
        if status != "OK":
            return 0
        
        return len(data[0].split()) if data[0] else 0
    
    def get_total_count(self) -> int:
        """Get total count of emails."""
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, data = self._client.uid('SEARCH', None, "ALL")
        
        if status != "OK":
            return 0
        
        return len(data[0].split()) if data[0] else 0
    
    def get_folder_list(self) -> List[str]:
        """Get list of available folders/mailboxes."""
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, data = self._client.list()
        
        if status != "OK":
            return []
        
        folders = []
        for item in data:
            if isinstance(item, bytes):
                item = item.decode()
            # Parse LIST response: ("" "/" "INBOX")
            parts = item.split()
            if len(parts) >= 3:
                folders.append(parts[-1])
        
        return folders
    
    def search_emails(
        self,
        from_addr: Optional[str] = None,
        to_addr: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        since_date: Optional[str] = None,
        before_date: Optional[str] = None,
        uid_range: Optional[tuple] = None
    ) -> List[str]:
        """
        Search for emails with various criteria.
        
        Args:
            from_addr: Filter by sender.
            to_addr: Filter by recipient.
            subject: Filter by subject.
            body: Filter by body content.
            since_date: Filter by date (IMAP date format).
            before_date: Filter by date (IMAP date format).
            uid_range: Filter by UID range (start, end).
        
        Returns:
            List of UID strings matching criteria.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        search_parts = []
        
        if from_addr:
            search_parts.append(f'FROM "{from_addr}"')
        if to_addr:
            search_parts.append(f'TO "{to_addr}"')
        if subject:
            search_parts.append(f'SUBJECT "{subject}"')
        if body:
            search_parts.append(f'BODY "{body}"')
        if since_date:
            search_parts.append(f'SINCE "{since_date}"')
        if before_date:
            search_parts.append(f'BEFORE "{before_date}"')
        if uid_range:
            search_parts.append(f'UID {uid_range[0]}:*')
        
        if not search_parts:
            search_parts = ["ALL"]
        
        search_query = " ".join(search_parts)
        status, data = self._client.search(None, search_query)
        
        if status != "OK":
            return []
        
        return data[0].split() if data[0] else []
    
    def mark_as_read(self, uid: str) -> bool:
        """
        Mark email as read.
        
        Args:
            uid: Email UID.
        
        Returns:
            True if successful.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, _ = self._client.uid('STORE', uid, '+FLAGS', '(\\Seen)')
        return status == "OK"
    
    def mark_as_unread(self, uid: str) -> bool:
        """
        Mark email as unread.
        
        Args:
            uid: Email UID.
        
        Returns:
            True if successful.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, _ = self._client.uid('STORE', uid, '-FLAGS', '(\\Seen)')
        return status == "OK"
    
    def delete_email(self, uid: str) -> bool:
        """
        Delete email.
        
        Args:
            uid: Email UID.
        
        Returns:
            True if successful.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        status, _ = self._client.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
        if status == "OK":
            self._client.expunge()
        return status == "OK"
    
    def move_email(self, uid: str, target_folder: str) -> bool:
        """
        Move email to different folder.
        
        Args:
            uid: Email UID.
            target_folder: Target folder name.
        
        Returns:
            True if successful.
        """
        if not self._client:
            raise ConnectionError("Not connected to IMAP server")
        
        # Create folder if it doesn't exist
        status, _ = self._client.create(target_folder)
        if status != "OK":
            return False
        
        # Move email
        status, _ = self._client.uid('COPY', uid, target_folder)
        if status == "OK":
            # Delete from original folder
            self._client.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
            self._client.expunge()
        
        return status == "OK"
