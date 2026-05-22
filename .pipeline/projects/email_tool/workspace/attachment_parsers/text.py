"""Text file attachment parser for TXT and CSV files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from email_tool.attachment_types import AttachmentType
from email_tool.attachment_parsers.base import (
    AbstractAttachmentParser,
    AttachmentMetadata,
    ParsedAttachment
)


class TextAttachmentParser(AbstractAttachmentParser):
    """
    Parser for text-based attachments (TXT, CSV).
    
    Reads text content directly from files.
    """
    
    SUPPORTED_TYPES = {
        AttachmentType.TXT,
        AttachmentType.CSV,
    }
    
    def __init__(self, staging_dir: str):
        """
        Initialize the text file parser.
        
        Args:
            staging_dir: Directory where attachments are stored.
        """
        super().__init__(staging_dir)
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser."""
        return "TextAttachmentParser"
    
    def can_parse(self, attachment_type: AttachmentType) -> bool:
        """Check if this parser can handle the given attachment type."""
        return attachment_type in self.SUPPORTED_TYPES
    
    def extract_text(self, file_path: Path, attachment_id: str, email_id: str) -> ParsedAttachment:
        """
        Extract text content from a text file.
        
        Args:
            file_path: Path to the text file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
        
        Returns:
            ParsedAttachment object with extracted text content.
        
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        # Check if file exists first
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")
        
        try:
            # Try to read as UTF-8 first, then fall back to latin-1
            encoding = 'utf-8'
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text_content = f.read()
            except UnicodeDecodeError:
                encoding = 'latin-1'
                with open(file_path, 'r', encoding=encoding) as f:
                    text_content = f.read()
            
            # Get file size only if we successfully read the file
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="text/plain",
                size_bytes=size_bytes,
                attachment_type=self._detect_type(file_path),
                text_content=text_content,
                success=True
            )
            
        except Exception as e:
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="text/plain",
                size_bytes=size_bytes,
                attachment_type=self._detect_type(file_path),
                success=False,
                error_message=f"Text file parsing error: {str(e)}"
            )
    
    def extract_metadata(self, file_path: Path) -> AttachmentMetadata:
        """
        Extract metadata from a text file.
        
        Args:
            file_path: Path to the text file.
        
        Returns:
            AttachmentMetadata object with extracted metadata.
        
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        # Check if file exists first
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")
        
        try:
            # Read file to get line count
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            metadata_dict = {
                'line_count': len(lines),
                'char_count': sum(len(line) for line in lines),
            }
            
            # If CSV, try to detect columns
            if file_path.suffix.lower() == '.csv':
                try:
                    import csv
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        if header:
                            metadata_dict['column_count'] = len(header)
                            metadata_dict['columns'] = header
                        metadata_dict['row_count'] = sum(1 for _ in reader) + 1  # +1 for header
                except Exception as e:
                    metadata_dict['csv_error'] = str(e)
            
            # Get file size only if we successfully read the file
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="text/plain",
                size_bytes=size_bytes,
                attachment_type=self._detect_type(file_path),
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata=metadata_dict
            )
            
        except Exception as e:
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="text/plain",
                size_bytes=size_bytes,
                attachment_type=self._detect_type(file_path),
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata={'error': str(e)}
            )
    
    def _detect_type(self, file_path: Path) -> AttachmentType:
        """Detect the text file type from file extension."""
        if file_path.suffix.lower() == '.csv':
            return AttachmentType.CSV
        elif file_path.suffix.lower() == '.txt':
            return AttachmentType.TXT
        else:
            return AttachmentType.UNKNOWN
