"""Attachment index for storing and querying parsed attachments."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from email_tool.attachment_types import AttachmentType
from email_tool.models import AttachmentProcessingResult


@dataclass
class AttachmentIndexEntry:
    """Entry in the attachment index."""
    attachment_id: str
    email_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    attachment_type: AttachmentType
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    indexed_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            'attachment_id': self.attachment_id,
            'email_id': self.email_id,
            'original_filename': self.original_filename,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
            'attachment_type': self.attachment_type.name,
            'text_content': self.text_content,
            'metadata': self.metadata,
            'indexed_at': self.indexed_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttachmentIndexEntry':
        """Create entry from dictionary."""
        # Convert attachment_type string back to enum
        attachment_type_str = data.get('attachment_type', 'UNKNOWN')
        try:
            attachment_type = AttachmentType(attachment_type_str)
        except ValueError:
            attachment_type = AttachmentType.UNKNOWN
        
        # Handle indexed_at field consistently - use value from data if present, otherwise generate timestamp
        indexed_at = data.get('indexed_at')
        if not indexed_at:
            indexed_at = datetime.now().isoformat()
        
        return cls(
            attachment_id=data['attachment_id'],
            email_id=data['email_id'],
            original_filename=data['original_filename'],
            content_type=data['content_type'],
            size_bytes=data['size_bytes'],
            attachment_type=attachment_type,
            text_content=data.get('text_content'),
            metadata=data.get('metadata'),
            indexed_at=indexed_at
        )


class AttachmentIndex:
    """
    Index for storing and querying parsed attachments.
    
    Provides efficient lookup by email_id, attachment_type, and text content.
    Supports serialization to JSON for persistence.
    """
    
    def __init__(self, index_dir: str = None):
        """
        Initialize the attachment index.
        
        Args:
            index_dir: Directory to store index files. If None, uses in-memory only.
        """
        self.entries: List[AttachmentIndexEntry] = []
        self.index_dir = Path(index_dir) if index_dir else None
        if self.index_dir:
            self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Build indexes for fast lookup
        self._by_email: Dict[str, Set[str]] = defaultdict(set)  # email_id -> set of attachment_ids
        self._by_type: Dict[AttachmentType, Set[str]] = defaultdict(set)  # attachment_type -> set of attachment_ids
        self._by_id: Dict[str, AttachmentIndexEntry] = {}  # attachment_id -> entry
    
    def add_entry(self, entry: AttachmentIndexEntry) -> None:
        """
        Add an entry to the index.
        
        Args:
            entry: AttachmentIndexEntry to add.
        """
        # Remove existing entry with same ID if present
        if entry.attachment_id in self._by_id:
            old_entry = self._by_id[entry.attachment_id]
            self._by_email[old_entry.email_id].discard(entry.attachment_id)
            self._by_type[old_entry.attachment_type].discard(entry.attachment_id)
        
        # Add new entry
        self.entries.append(entry)
        self._by_id[entry.attachment_id] = entry
        self._by_email[entry.email_id].add(entry.attachment_id)
        self._by_type[entry.attachment_type].add(entry.attachment_id)
    
    def add_entries(self, entries: List[AttachmentIndexEntry]) -> None:
        """
        Add multiple entries to the index.
        
        Args:
            entries: List of AttachmentIndexEntry to add.
        """
        for entry in entries:
            self.add_entry(entry)
    
    def add_from_processing_result(self, result: AttachmentProcessingResult) -> None:
        """
        Add entries from an attachment processing result.
        
        Args:
            result: AttachmentProcessingResult to add.
        """
        entry = AttachmentIndexEntry(
            attachment_id=result.attachment_id,
            email_id=result.email_id,
            original_filename=result.original_filename,
            content_type=result.content_type,
            size_bytes=result.size_bytes,
            attachment_type=result.attachment_type,
            text_content=result.text_content,
            metadata=result.metadata,
            indexed_at=result.processed_at
        )
        self.add_entry(entry)
    
    def find_by_email(self, email_id: str) -> List[AttachmentIndexEntry]:
        """
        Find all attachments for a specific email.
        
        Args:
            email_id: Email ID to search for.
        
        Returns:
            List of AttachmentIndexEntry objects.
        """
        attachment_ids = self._by_email.get(email_id, set())
        return [self._by_id[aid] for aid in attachment_ids if aid in self._by_id]
    
    def find_by_type(self, attachment_type: AttachmentType) -> List[AttachmentIndexEntry]:
        """
        Find all attachments of a specific type.
        
        Args:
            attachment_type: Attachment type to search for.
        
        Returns:
            List of AttachmentIndexEntry objects.
        """
        attachment_ids = self._by_type.get(attachment_type, set())
        return [self._by_id[aid] for aid in attachment_ids if aid in self._by_id]
    
    def search_text(self, query: str, case_sensitive: bool = False) -> List[AttachmentIndexEntry]:
        """
        Search for attachments containing query text.
        
        Args:
            query: Text to search for.
            case_sensitive: Whether search is case-sensitive.
        
        Returns:
            List of AttachmentIndexEntry objects matching the query.
        """
        results = []
        search_query = query if case_sensitive else query.lower()
        
        for entry in self.entries:
            if entry.text_content:
                text = entry.text_content if case_sensitive else entry.text_content.lower()
                if search_query in text:
                    results.append(entry)
        
        return results
    
    def search_text_in_email(self, email_id: str, query: str, case_sensitive: bool = False) -> List[AttachmentIndexEntry]:
        """
        Search for attachments containing query text within a specific email.
        
        Args:
            email_id: Email ID to search within.
            query: Text to search for.
            case_sensitive: Whether search is case-sensitive.
        
        Returns:
            List of AttachmentIndexEntry objects matching the query.
        """
        email_attachments = self.find_by_email(email_id)
        return [entry for entry in email_attachments 
                if entry.text_content and 
                (query in entry.text_content if case_sensitive else query.lower() in entry.text_content.lower())]
    
    def get_all(self) -> List[AttachmentIndexEntry]:
        """
        Get all entries in the index.
        
        Returns:
            List of all AttachmentIndexEntry objects.
        """
        return self.entries.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the index contents.
        
        Returns:
            Dictionary with index statistics.
        """
        type_counts: Dict[str, int] = {}
        for entry in self.entries:
            type_name = entry.attachment_type.name
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        total_size = sum(entry.size_bytes for entry in self.entries)
        emails_with_attachments = len(self._by_email)
        
        return {
            'total_attachments': len(self.entries),
            'total_size_bytes': total_size,
            'emails_with_attachments': emails_with_attachments,
            'attachment_types': type_counts,
        }
    
    def serialize(self) -> str:
        """
        Serialize the index to JSON string.
        
        Returns:
            JSON string representation of the index.
        """
        data = {
            'indexed_at': datetime.now().isoformat(),
            'entries': [entry.to_dict() for entry in self.entries],
        }
        return json.dumps(data, indent=2)
    
    def deserialize(self, json_str: str) -> None:
        """
        Deserialize the index from JSON string.
        
        Args:
            json_str: JSON string to deserialize.
        """
        data = json.loads(json_str)
        self.entries = []
        self._by_email.clear()
        self._by_type.clear()
        self._by_id.clear()
        
        for entry_data in data.get('entries', []):
            entry = AttachmentIndexEntry.from_dict(entry_data)
            self.add_entry(entry)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the index to a JSON file.
        
        Args:
            filepath: Path to save the index file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(self.serialize())
    
    def load_from_file(self, filepath: str) -> None:
        """
        Load the index from a JSON file.
        
        Args:
            filepath: Path to load the index file from.
        """
        filepath = Path(filepath)
        if filepath.exists():
            with open(filepath, 'r') as f:
                self.deserialize(f.read())
    
    def clear(self) -> None:
        """Clear all entries from the index."""
        self.entries.clear()
        self._by_email.clear()
        self._by_type.clear()
        self._by_id.clear()
    
    def __len__(self) -> int:
        """Return the number of entries in the index."""
        return len(self.entries)
    
    def __bool__(self) -> bool:
        """Return True if the index has entries."""
        return len(self.entries) > 0
