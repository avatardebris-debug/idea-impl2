"""Base connector interface for email sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generator, List, Optional
from email_tool.models import Email


class ConnectorType(Enum):
    """Types of email connectors."""
    IMAP = "imap"
    GMAIL = "gmail"
    MBOX = "mbox"
    OST = "ost"


@dataclass
class ConnectorConfig:
    """Base configuration for email connectors."""
    name: str
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[float] = None  # Requests per second
    timeout: float = 30.0
    ssl: bool = True
    
    # Sync state tracking
    last_sync_time: Optional[datetime] = None
    last_sync_uid: Optional[int] = None
    last_sync_history_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncState:
    """Tracks synchronization state for incremental sync."""
    connector_type: ConnectorType
    last_sync_time: Optional[datetime] = None
    last_sync_uid: Optional[int] = None
    last_sync_history_id: Optional[str] = None
    total_emails_fetched: int = 0
    total_emails_processed: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "connector_type": self.connector_type.value,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "last_sync_uid": self.last_sync_uid,
            "last_sync_history_id": self.last_sync_history_id,
            "total_emails_fetched": self.total_emails_fetched,
            "total_emails_processed": self.total_emails_processed,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncState':
        """Create from dictionary."""
        return cls(
            connector_type=ConnectorType(data["connector_type"]),
            last_sync_time=datetime.fromisoformat(data["last_sync_time"]) if data.get("last_sync_time") else None,
            last_sync_uid=data.get("last_sync_uid"),
            last_sync_history_id=data.get("last_sync_history_id"),
            total_emails_fetched=data.get("total_emails_fetched", 0),
            total_emails_processed=data.get("total_emails_processed", 0),
            last_error=data.get("last_error"),
            last_error_time=datetime.fromisoformat(data["last_error_time"]) if data.get("last_error_time") else None,
            retry_count=data.get("retry_count", 0)
        )


class EmailConnector(ABC):
    """
    Abstract base class for email connectors.
    
    All connectors must implement this interface to fetch emails from various sources.
    """
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize the connector.
        
        Args:
            config: Connector configuration.
        """
        self.config = config
        self._sync_state: Optional[SyncState] = None
        self._rate_limiter: Optional[Any] = None
        self._initialized = False
    
    @property
    @abstractmethod
    def connector_type(self) -> ConnectorType:
        """Return the type of this connector."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the email source.
        
        Returns:
            True if connection successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_uid: Optional[int] = None,
        since_history_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Generator[Email, None, None]:
        """
        Fetch emails from the source.
        
        Args:
            limit: Maximum number of emails to fetch.
            since_uid: Fetch only emails with UID greater than this (IMAP).
            since_history_id: Fetch only emails changed after this ID (Gmail).
            labels: Filter by labels (Gmail).
        
        Yields:
            Email objects.
        """
        pass
    
    @abstractmethod
    def get_unread_count(self) -> int:
        """
        Get count of unread emails.
        
        Returns:
            Number of unread emails.
        """
        pass
    
    @abstractmethod
    def get_total_count(self) -> int:
        """
        Get total count of emails.
        
        Returns:
            Total number of emails.
        """
        pass
    
    def get_sync_state(self) -> SyncState:
        """
        Get current sync state.
        
        Returns:
            SyncState object.
        """
        if self._sync_state is None:
            self._sync_state = SyncState(connector_type=self.connector_type)
        return self._sync_state
    
    def set_sync_state(self, state: SyncState) -> None:
        """
        Set sync state for resume capability.
        
        Args:
            state: SyncState to set.
        """
        self._sync_state = state
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting if configured."""
        if self.config.rate_limit and self.config.rate_limit > 0:
            import time
            time.sleep(1.0 / self.config.rate_limit)
    
    def _handle_error(self, error: Exception, operation: str) -> bool:
        """
        Handle errors with retry logic.
        
        Args:
            error: The exception that occurred.
            operation: Name of the operation that failed.
        
        Returns:
            True if should retry, False otherwise.
        """
        self._sync_state = self._sync_state or SyncState(connector_type=self.connector_type)
        self._sync_state.retry_count += 1
        self._sync_state.last_error = str(error)
        self._sync_state.last_error_time = datetime.now()
        
        if self._sync_state.retry_count < self.config.max_retries:
            import time
            # Exponential backoff
            delay = self.config.retry_delay * (2 ** (self._sync_state.retry_count - 1))
            time.sleep(min(delay, 30))  # Cap at 30 seconds
            return True
        
        return False
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._initialized
    
    def __enter__(self) -> 'EmailConnector':
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()


class ConnectorFactory:
    """
    Factory for creating email connectors.
    
    Loads connectors from configuration.
    """
    
    _connectors: Dict[ConnectorType, type] = {}
    
    @classmethod
    def register_connector(cls, connector_type: ConnectorType, connector_class: type) -> None:
        """
        Register a connector class.
        
        Args:
            connector_type: Type of connector.
            connector_class: Connector class to register.
        """
        cls._connectors[connector_type] = connector_class
    
    @classmethod
    def create(cls, config: ConnectorConfig) -> EmailConnector:
        """
        Create a connector from configuration.
        
        Args:
            config: Connector configuration.
        
        Returns:
            EmailConnector instance.
        
        Raises:
            ValueError: If connector type is not registered.
        """
        if config.name not in cls._connectors:
            raise ValueError(f"Unknown connector type: {config.name}")
        
        connector_class = cls._connectors[config.name]
        return connector_class(config)
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> EmailConnector:
        """
        Create connector from dictionary configuration.
        
        Args:
            config_dict: Dictionary with connector configuration.
        
        Returns:
            EmailConnector instance.
        """
        config = ConnectorConfig(
            name=config_dict["type"],
            enabled=config_dict.get("enabled", True),
            max_retries=config_dict.get("max_retries", 3),
            retry_delay=config_dict.get("retry_delay", 1.0),
            rate_limit=config_dict.get("rate_limit"),
            timeout=config_dict.get("timeout", 30.0),
            ssl=config_dict.get("ssl", True),
            metadata=config_dict.get("metadata", {})
        )
        return cls.create(config)
