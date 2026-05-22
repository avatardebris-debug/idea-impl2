"""PDF attachment parser using PyPDF2."""

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


class PDFAttachmentParser(AbstractAttachmentParser):
    """
    Parser for PDF attachments.
    
    Uses PyPDF2 to extract text content and metadata from PDF files.
    """
    
    SUPPORTED_TYPES = {AttachmentType.PDF}
    
    def __init__(self, staging_dir: str):
        """
        Initialize the PDF attachment parser.
        
        Args:
            staging_dir: Directory where attachments are stored.
        """
        super().__init__(staging_dir)
        try:
            import PyPDF2
            self.PyPDF2 = PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser."""
        return "PDFAttachmentParser"
    
    def can_parse(self, attachment_type: AttachmentType) -> bool:
        """Check if this parser can handle the given attachment type."""
        return attachment_type in self.SUPPORTED_TYPES
    
    def extract_text(self, file_path: Path, attachment_id: str, email_id: str) -> ParsedAttachment:
        """
        Extract text content from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
        
        Returns:
            ParsedAttachment object with extracted text content.
        
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        # Check if file exists first
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            text_parts = []
            
            with open(file_path, 'rb') as f:
                reader = self.PyPDF2.PdfReader(f)
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            # Combine all pages
            text_content = '\n\n'.join(text_parts) if text_parts else None
            
            # Get file size only if we successfully read the file
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="application/pdf",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.PDF,
                text_content=text_content,
                success=True
            )
            
        except self.PyPDF2.errors.PdfReadError as e:
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="application/pdf",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.PDF,
                success=False,
                error_message=f"PDF read error: {str(e)}"
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
                content_type="application/pdf",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.PDF,
                success=False,
                error_message=f"PDF parsing error: {str(e)}"
            )
    
    def extract_metadata(self, file_path: Path) -> AttachmentMetadata:
        """
        Extract metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
        
        Returns:
            AttachmentMetadata object with extracted metadata.
        
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        # Check if file exists first
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                reader = self.PyPDF2.PdfReader(f)
                
                # Extract document metadata
                metadata = reader.metadata
                metadata_dict = {}
                
                if metadata:
                    # Map PDF metadata fields to our format
                    if metadata.get('/Title'):
                        metadata_dict['title'] = metadata['/Title']
                    if metadata.get('/Author'):
                        metadata_dict['author'] = metadata['/Author']
                    if metadata.get('/Subject'):
                        metadata_dict['subject'] = metadata['/Subject']
                    if metadata.get('/Creator'):
                        metadata_dict['creator'] = metadata['/Creator']
                    if metadata.get('/Producer'):
                        metadata_dict['producer'] = metadata['/Producer']
                    if metadata.get('/Keywords'):
                        metadata_dict['keywords'] = metadata['/Keywords']
                
                # Get page count
                metadata_dict['page_count'] = len(reader.pages)
                
                # Get PDF version
                metadata_dict['pdf_version'] = reader.pdf_version
                
                # Get file size only if we successfully read the file
                try:
                    size_bytes = file_path.stat().st_size
                except OSError:
                    size_bytes = 0
                
                return AttachmentMetadata(
                    original_filename=file_path.name,
                    content_type="application/pdf",
                    size_bytes=size_bytes,
                    attachment_type=AttachmentType.PDF,
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
                content_type="application/pdf",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.PDF,
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata={'error': str(e)}
            )
