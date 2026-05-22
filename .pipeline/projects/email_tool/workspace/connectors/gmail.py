"""Gmail API connector for fetching emails from Gmail."""

import base64
from email import message_from_bytes
from email.header import decode_header
from typing import Generator, List, Optional
from datetime import datetime
from email_tool.models import Email
from email_tool.connectors.base import EmailConnector, ConnectorConfig, ConnectorType, SyncState


class GmailConnector(EmailConnector):
    """
    Gmail API connector for fetching emails.
    
    Features:
    - OAuth2 authentication
    - Incremental sync via history ID
    - Label filtering
    - Full email parsing
    """
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize the Gmail connector.
        
        Args:
            config: Connector configuration with credentials.
        """
        super().__init__(config)
        self._service = None
        self._credentials = None
        self._sync_state: Optional[SyncState] = None
        self._label_filter = config.metadata.get("labels", [])
        self._max_results = config.metadata.get("max_results", 100)
    
    @property
    def connector_type(self) -> ConnectorType:
        """Return the connector type."""
        return ConnectorType.GMAIL
    
    def connect(self) -> bool:
        """
        Establish connection to Gmail API.
        
        Returns:
            True if connection successful.
        """
        if self._initialized:
            return True
        
        try:
            from google.oauth2.credentials import Credentials
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Load credentials
            credentials_data = self.config.metadata.get("credentials", {})
            
            if credentials_data.get("type") == "service_account":
                # Service account authentication
                self._credentials = service_account.Credentials.from_service_account_info(
                    credentials_data,
                    scopes=["https://www.googleapis.com/auth/gmail.readonly"]
                )
            else:
                # User credentials
                self._credentials = Credentials(
                    token=credentials_data.get("token"),
                    refresh_token=credentials_data.get("refresh_token"),
                    client_id=credentials_data.get("client_id"),
                    client_secret=credentials_data.get("client_secret"),
                    token_uri=credentials_data.get("token_uri", "https://oauth2.googleapis.com/token")
                )
            
            # Build service
            self._service = build('gmail', 'v1', credentials=self._credentials)
            
            # Test connection
            self._service.users().profile().get(userId='me').execute()
            
            self._initialized = True
            return True
            
        except ImportError as e:
            raise ImportError(
                "Gmail connector requires google-api-python-client and google-auth. "
                "Install with: pip install google-api-python-client google-auth"
            ) from e
        except Exception as e:
            self._handle_error(e, "connect")
            return False
    
    def disconnect(self) -> None:
        """Close the connection."""
        # Gmail service doesn't need explicit cleanup
        self._initialized = False
    
    def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_uid: Optional[int] = None,
        since_history_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Generator[Email, None, None]:
        """
        Fetch emails from Gmail.
        
        Args:
            limit: Maximum number of emails to fetch.
            since_uid: Not used for Gmail (use since_history_id).
            since_history_id: Fetch only emails changed after this history ID.
            labels: Filter by Gmail labels.
        
        Yields:
            Email objects.
        """
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        # Build query
        query = "in:inbox"  # Default to inbox
        
        # Apply label filter
        if labels:
            label_filter = " OR ".join([f"label:{label}" for label in labels])
            query = f"({query}) ({label_filter})"
        elif self._label_filter:
            label_filter = " OR ".join([f"label:{label}" for label in self._label_filter])
            query = f"({query}) ({label_filter})"
        
        # Apply history ID for incremental sync
        if since_history_id:
            history = self._service.users().history().list(
                userId='me',
                startHistoryId=int(since_history_id)
            ).execute()
            
            for entry in history.get("history", []):
                for message_id in entry.get("messages", []):
                    if limit and limit <= 0:
                        break
                    
                    try:
                        msg = self._get_message(message_id["id"])
                        if msg:
                            yield msg
                            limit = limit - 1 if limit else None
                    except Exception as e:
                        self._handle_error(e, "fetch_message")
                    
                    self._apply_rate_limit()
            
            # Update sync state
            if history.get("nextPageToken"):
                page_token = history["nextPageToken"]
                while page_token:
                    history = self._service.users().history().list(
                        userId='me',
                        startHistoryId=int(since_history_id),
                        pageToken=page_token
                    ).execute()
                    
                    for entry in history.get("history", []):
                        if limit and limit <= 0:
                            break
                        
                        for message_id in entry.get("messages", []):
                            try:
                                msg = self._get_message(message_id["id"])
                                if msg:
                                    yield msg
                                    limit = limit - 1 if limit else None
                            except Exception as e:
                                self._handle_error(e, "fetch_message")
                        
                        self._apply_rate_limit()
                    
                    page_token = history.get("nextPageToken")
            
            return
        
        # Standard fetch
        results = self._service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(limit or self._max_results, 100)
        ).execute()
        
        messages = results.get("messages", [])
        
        for message in messages:
            if limit and limit <= 0:
                break
            
            try:
                msg = self._get_message(message["id"])
                if msg:
                    yield msg
                    limit = limit - 1 if limit else None
            except Exception as e:
                self._handle_error(e, "fetch_message")
            
            self._apply_rate_limit()
        
        # Handle pagination
        page_token = results.get("nextPageToken")
        while page_token and (limit is None or limit > 0):
            results = self._service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(limit or self._max_results, 100),
                pageToken=page_token
            ).execute()
            
            messages = results.get("messages", [])
            
            for message in messages:
                if limit and limit <= 0:
                    break
                
                try:
                    msg = self._get_message(message["id"])
                    if msg:
                        yield msg
                        limit = limit - 1 if limit else None
                except Exception as e:
                    self._handle_error(e, "fetch_message")
                
                self._apply_rate_limit()
            
            page_token = results.get("nextPageToken")
    
    def _get_message(self, message_id: str) -> Optional[Email]:
        """Fetch and parse a single message."""
        try:
            raw_message = self._service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(raw_message)
            
        except Exception as e:
            self._handle_error(e, "get_message")
            return None
    
    def _parse_message(self, raw_message: dict) -> Optional[Email]:
        """Parse Gmail message into Email object."""
        try:
            payload = raw_message.get("payload", {})
            headers = payload.get("headers", [])
            
            # Extract headers
            subject = ""
            from_addr = ""
            to_addr = ""
            date_str = ""
            
            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                
                if name == "subject":
                    subject = value
                elif name == "from":
                    from_addr = value
                elif name == "to":
                    to_addr = value
                elif name == "date":
                    date_str = value
            
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
            
            def extract_body(part):
                nonlocal body_plain, body_html
                content_type = part.get("mimeType", "")
                
                if content_type == "text/plain":
                    body_plain = part.get("body", {}).get("data", "")
                elif content_type == "text/html":
                    body_html = part.get("body", {}).get("data", "")
                
                # Recursively process parts
                for child in part.get("parts", []):
                    extract_body(child)
            
            extract_body(payload)
            
            # Decode base64 content
            if body_plain:
                try:
                    body_plain = base64.urlsafe_b64decode(body_plain).decode('utf-8')
                except Exception:
                    pass
            
            if body_html:
                try:
                    body_html = base64.urlsafe_b64decode(body_html).decode('utf-8')
                except Exception:
                    pass
            
            # Extract attachments
            attachments = []
            for part in payload.get("parts", []):
                if part.get("filename"):
                    attachment_id = part.get("body", {}).get("attachmentId")
                    size = int(part.get("body", {}).get("size", 0))
                    attachments.append({
                        "filename": part["filename"],
                        "size": size,
                        "attachment_id": attachment_id
                    })
            
            # Extract labels
            label_ids = raw_message.get("labelIds", [])
            labels = [label_id.replace("LABEL_", "").lower() for label_id in label_ids]
            
            # Get history ID for incremental sync
            history_id = raw_message.get("historyId")
            
            return Email(
                id=raw_message["id"],
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                received_date=received_date,
                body_plain=body_plain,
                body_html=body_html,
                attachments=attachments,
                labels=labels,
                source_path=None,
                history_id=history_id
            )
            
        except Exception as e:
            self._handle_error(e, "parse_message")
            return None
    
    def get_unread_count(self) -> int:
        """Get count of unread emails."""
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        results = self._service.users().messages().list(
            userId='me',
            q="-in:inbox -category:promotions -category:social -category:updates -category:forums -in:trash -label:UNREAD"
        ).execute()
        
        return len(results.get("messages", []))
    
    def get_total_count(self) -> int:
        """Get total count of emails."""
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        results = self._service.users().messages().list(
            userId='me',
            q="-in:trash"
        ).execute()
        
        return len(results.get("messages", []))
    
    def get_labels(self) -> List[str]:
        """Get list of Gmail labels."""
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        results = self._service.users().labels().list(userId='me').execute()
        
        return [label["name"] for label in results.get("labels", [])]
    
    def apply_label(self, message_id: str, label: str) -> bool:
        """
        Apply label to message.
        
        Args:
            message_id: Gmail message ID.
            label: Label name to apply.
        
        Returns:
            True if successful.
        """
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        try:
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={"addLabelIds": [label]}
            ).execute()
            return True
        except Exception as e:
            self._handle_error(e, "apply_label")
            return False
    
    def remove_label(self, message_id: str, label: str) -> bool:
        """
        Remove label from message.
        
        Args:
            message_id: Gmail message ID.
            label: Label name to remove.
        
        Returns:
            True if successful.
        """
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        try:
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={"removeLabelIds": [label]}
            ).execute()
            return True
        except Exception as e:
            self._handle_error(e, "remove_label")
            return False
    
    def get_history_id(self) -> Optional[str]:
        """Get current history ID for incremental sync."""
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        profile = self._service.users().profile().get(userId='me').execute()
        return profile.get("historyId")
    
    def search_emails(
        self,
        query: str,
        max_results: int = 100
    ) -> List[str]:
        """
        Search for emails.
        
        Args:
            query: Gmail search query.
            max_results: Maximum results to return.
        
        Returns:
            List of message IDs.
        """
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        results = self._service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(max_results, 100)
        ).execute()
        
        return [msg["id"] for msg in results.get("messages", [])]
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read."""
        return self.remove_label(message_id, "UNREAD")
    
    def mark_as_unread(self, message_id: str) -> bool:
        """Mark email as unread."""
        return self.apply_label(message_id, "UNREAD")
    
    def delete_email(self, message_id: str) -> bool:
        """Delete email (move to trash)."""
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        try:
            self._service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            return True
        except Exception as e:
            self._handle_error(e, "delete_email")
            return False
    
    def move_email(self, message_id: str, label: str) -> bool:
        """
        Move email to different label.
        
        Args:
            message_id: Gmail message ID.
            label: Target label.
        
        Returns:
            True if successful.
        """
        if not self._service:
            raise ConnectionError("Not connected to Gmail API")
        
        try:
            # Remove all labels except INBOX
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={"removeLabelIds": ["INBOX"]}
            ).execute()
            
            # Add target label
            return self.apply_label(message_id, label)
            
        except Exception as e:
            self._handle_error(e, "move_email")
            return False
