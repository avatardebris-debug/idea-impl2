"""Base class for attachment parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path

from email_tool.attachment_types import AttachmentType


@dataclass
class AttachmentMetadata:
    """Metadata extracted from an attachment."""
    original_filename: str
    content_type: str
    size_bytes: int
    attachment_type: AttachmentType
    extracted_at: str = ""
    parser_name: str = ""
    additional_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedAttachment:
    """Result of parsing an attachment."""
    attachment_id: str
    email_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    attachment_type: AttachmentType
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class AbstractAttachmentParser(ABC):
    """
    Abstract base class for attachment parsers.
    
    Each concrete parser handles a specific attachment type and provides
    methods to extract text content and metadata.
    """
    
    SUPPORTED_TYPES: set[AttachmentType] = set()
    """Set of attachment types this parser supports."""
    
    def __init__(self, staging_dir: str):
        """
        Initialize the attachment parser.
        
        Args:
            staging_dir: Directory where attachments are stored.
        """
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    @abstractmethod
    def get_parser_name(cls) -> str:
        """
        Get the name of this parser.
        
        Returns:
            Parser name string.
        """
        pass
    
    @abstractmethod
    def can_parse(self, attachment_type: AttachmentType) -> bool:
        """
        Check if this parser can handle the given attachment type.
        
        Args:
            attachment_type: The attachment type to check.
        
        Returns:
            True if this parser can handle the attachment type.
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path, attachment_id: str, email_id: str) -> ParsedAttachment:
        """
        Extract text content from an attachment.
        
        Args:
            file_path: Path to the attachment file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
        
        Returns:
            ParsedAttachment object with extracted content and metadata.
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> AttachmentMetadata:
        """
        Extract metadata from an attachment.
        
        Args:
            file_path: Path to the attachment file.
        
        Returns:
            AttachmentMetadata object with extracted metadata.
        """
        pass
    
    def parse(self, file_path: Path, attachment_id: str, email_id: str,
              original_filename: str, content_type: str, size_bytes: int,
              attachment_type: AttachmentType) -> ParsedAttachment:
        """
        Parse an attachment and return structured data.
        
        This is a convenience method that calls extract_text and extract_metadata.
        
        Args:
            file_path: Path to the attachment file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
            original_filename: Original filename of the attachment.
            content_type: MIME content type of the attachment.
            size_bytes: Size of the attachment in bytes.
            attachment_type: Type of the attachment.
        
        Returns:
            ParsedAttachment object with extracted content and metadata.
        """
        try:
            # Convert to Path if it's a string
            file_path_obj = Path(file_path) if not isinstance(file_path, Path) else file_path
            
            metadata = self.extract_metadata(file_path_obj)
            parsed = self.extract_text(file_path_obj, attachment_id, email_id)
            
            # Update parsed attachment with additional info
            parsed.original_filename = original_filename
            parsed.content_type = content_type
            parsed.size_bytes = size_bytes
            parsed.attachment_type = attachment_type
            parsed.metadata = {
                "parser_name": self.get_parser_name(),
                "extracted_at": metadata.extracted_at,
                "file_size": size_bytes,
                "additional": metadata.additional_metadata
            }
            
            return parsed
        except Exception as e:
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=original_filename,
                content_type=content_type,
                size_bytes=size_bytes,
                attachment_type=attachment_type,
                success=False,
                error_message=str(e)
            )
