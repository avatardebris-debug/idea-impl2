"""ZIP attachment parser for extracting metadata from archive files."""

import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from email_tool.attachment_parsers.base import ParsedAttachment, AbstractAttachmentParser, AttachmentMetadata
from email_tool.attachment_types import AttachmentType


class ZipAttachmentParser(AbstractAttachmentParser):
    """
    Parser for ZIP attachments.
    
    Extracts metadata about the archive contents including file list,
    sizes, and compression information.
    """
    
    SUPPORTED_TYPES = {
        AttachmentType.ZIP,
    }
    
    def __init__(self, staging_dir: str = "./staging"):
        """
        Initialize the ZIP attachment parser.
        
        Args:
            staging_dir: Directory where attachments are stored.
        """
        super().__init__(staging_dir)
    
    def get_parser_name(self) -> str:
        """Return the parser name."""
        return "ZipAttachmentParser"
    
    def can_parse(self, attachment_type: AttachmentType) -> bool:
        """Check if this parser can handle the attachment type."""
        return attachment_type in self.SUPPORTED_TYPES
    
    def extract_text(self, file_path: Path, attachment_id: str, email_id: str) -> ParsedAttachment:
        """
        Extract text content from a ZIP file.
        
        Args:
            file_path: Path to the ZIP file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
        
        Returns:
            ParsedAttachment with extracted text content.
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Get file list
                file_list = []
                total_size = 0
                total_compressed = 0
                directories = 0
                files = 0
                
                for info in zf.infolist():
                    is_dir = info.is_dir()
                    file_entry = {
                        'name': info.filename,
                        'size': info.file_size,
                        'is_directory': is_dir,
                        'compressed_size': info.compress_size,
                        'date_time': datetime(*info.date_time).isoformat() if info.date_time else None,
                    }
                    file_list.append(file_entry)
                    
                    total_size += info.file_size
                    total_compressed += info.compress_size
                    
                    if is_dir:
                        directories += 1
                    else:
                        files += 1
                
                # Calculate compression ratio
                compression_ratio = 0.0
                if total_size > 0:
                    compression_ratio = round((1 - total_compressed / total_size) * 100, 2)
                
                metadata = {
                    'total_entries': len(file_list),
                    'total_files': files,
                    'total_directories': directories,
                    'total_uncompressed_size': total_size,
                    'total_compressed_size': total_compressed,
                    'compression_ratio_percent': compression_ratio,
                    'files': file_list,
                    'is_encrypted': zf.testzip() is not None,
                }
                
                # Get file size only if we successfully read the file
                try:
                    size_bytes = file_path.stat().st_size
                except OSError:
                    size_bytes = 0
                
                text_content = self._generate_text_content(file_path.name, metadata, size_bytes)
                
                return ParsedAttachment(
                    attachment_id=attachment_id,
                    email_id=email_id,
                    original_filename=file_path.name,
                    content_type="application/zip",
                    size_bytes=size_bytes,
                    attachment_type=AttachmentType.ZIP,
                    text_content=text_content,
                    metadata=metadata,
                    success=True
                )
                
        except zipfile.BadZipFile as e:
            metadata = {
                'error': str(e),
                'total_entries': 0,
                'total_files': 0,
                'total_directories': 0,
                'total_uncompressed_size': 0,
                'total_compressed_size': 0,
                'compression_ratio_percent': 0.0,
                'files': [],
                'is_encrypted': False,
            }
            
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            text_content = self._generate_text_content(file_path.name, metadata, size_bytes)
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="application/zip",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.ZIP,
                text_content=text_content,
                metadata=metadata,
                success=True
            )
        except Exception as e:
            metadata = {
                'error': str(e),
                'total_entries': 0,
                'total_files': 0,
                'total_directories': 0,
                'total_uncompressed_size': 0,
                'total_compressed_size': 0,
                'compression_ratio_percent': 0.0,
                'files': [],
                'is_encrypted': False,
            }
            
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            text_content = self._generate_text_content(file_path.name, metadata, size_bytes)
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="application/zip",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.ZIP,
                text_content=text_content,
                metadata=metadata,
                success=True
            )
    
    def extract_metadata(self, file_path: Path) -> AttachmentMetadata:
        """
        Extract metadata from a ZIP file.
        
        Args:
            file_path: Path to the ZIP file.
        
        Returns:
            AttachmentMetadata object with extracted metadata.
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Get file list
                file_list = []
                total_size = 0
                total_compressed = 0
                directories = 0
                files = 0
                
                for info in zf.infolist():
                    is_dir = info.is_dir()
                    file_entry = {
                        'name': info.filename,
                        'size': info.file_size,
                        'is_directory': is_dir,
                        'compressed_size': info.compress_size,
                        'date_time': datetime(*info.date_time).isoformat() if info.date_time else None,
                    }
                    file_list.append(file_entry)
                    
                    total_size += info.file_size
                    total_compressed += info.compress_size
                    
                    if is_dir:
                        directories += 1
                    else:
                        files += 1
                
                # Calculate compression ratio
                compression_ratio = 0.0
                if total_size > 0:
                    compression_ratio = round((1 - total_compressed / total_size) * 100, 2)
                
                additional_metadata = {
                    'total_entries': len(file_list),
                    'total_files': files,
                    'total_directories': directories,
                    'total_uncompressed_size': total_size,
                    'total_compressed_size': total_compressed,
                    'compression_ratio_percent': compression_ratio,
                    'files': file_list,
                    'is_encrypted': zf.testzip() is not None,
                }
                
                # Get file size only if we successfully read the file
                try:
                    size_bytes = file_path.stat().st_size
                except OSError:
                    size_bytes = 0
                
                return AttachmentMetadata(
                    original_filename=file_path.name,
                    content_type="application/zip",
                    size_bytes=size_bytes,
                    attachment_type=AttachmentType.ZIP,
                    extracted_at=datetime.now().isoformat(),
                    parser_name=self.get_parser_name(),
                    additional_metadata=additional_metadata
                )
                
        except zipfile.BadZipFile as e:
            additional_metadata = {
                'error': str(e),
                'total_entries': 0,
                'total_files': 0,
                'total_directories': 0,
                'total_uncompressed_size': 0,
                'total_compressed_size': 0,
                'compression_ratio_percent': 0.0,
                'files': [],
                'is_encrypted': False,
            }
            
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="application/zip",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.ZIP,
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata=additional_metadata
            )
        except Exception as e:
            additional_metadata = {
                'error': str(e),
                'total_entries': 0,
                'total_files': 0,
                'total_directories': 0,
                'total_uncompressed_size': 0,
                'total_compressed_size': 0,
                'compression_ratio_percent': 0.0,
                'files': [],
                'is_encrypted': False,
            }
            
            # Get file size for error case if possible
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="application/zip",
                size_bytes=size_bytes,
                attachment_type=AttachmentType.ZIP,
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata=additional_metadata
            )
    
    def _generate_text_content(self, filename: str, zip_metadata: Dict[str, Any], size_bytes: int) -> str:
        """
        Generate searchable text content from ZIP metadata.
        
        Args:
            filename: Original filename.
            zip_metadata: Extracted ZIP metadata.
            size_bytes: File size in bytes.
        
        Returns:
            Text content for search indexing.
        """
        parts = [
            f"ZIP archive: {filename}",
            f"Size: {size_bytes} bytes",
            f"Total entries: {zip_metadata.get('total_entries', 0)}",
            f"Files: {zip_metadata.get('total_files', 0)}",
            f"Directories: {zip_metadata.get('total_directories', 0)}",
            f"Compression ratio: {zip_metadata.get('compression_ratio_percent', 0.0)}%",
        ]
        
        # Add file list for search indexing
        if zip_metadata.get('files'):
            parts.append("File list:")
            for file_info in zip_metadata['files'][:20]:  # Limit to first 20 files
                parts.append(f"  - {file_info['name']} ({file_info['size']} bytes)")
            
            if len(zip_metadata['files']) > 20:
                parts.append(f"  ... and {len(zip_metadata['files']) - 20} more files")
        
        if zip_metadata.get('is_encrypted'):
            parts.append("Encrypted: Yes")
        
        return " ".join(parts)
    
    def get_supported_types(self) -> list:
        """Return list of supported attachment types."""
        return [t.name for t in self.SUPPORTED_TYPES]
    
    def validate_zip(self, file_path: Path) -> bool:
        """
        Validate that a file is a valid ZIP archive.
        
        Args:
            file_path: Path to the file to validate.
        
        Returns:
            True if valid ZIP file, False otherwise.
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Test the ZIP file
                bad_file = zf.testzip()
                return bad_file is None
        except zipfile.BadZipFile:
            return False
        except Exception:
            return False
    
    def list_contents(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        List contents of a ZIP file.
        
        Args:
            file_path: Path to the ZIP file.
        
        Returns:
            List of file information dictionaries.
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                file_list = []
                for info in zf.infolist():
                    file_list.append({
                        'name': info.filename,
                        'size': info.file_size,
                        'is_directory': info.is_dir(),
                        'compressed_size': info.compress_size,
                        'date_time': datetime(*info.date_time).isoformat() if info.date_time else None,
                    })
                return file_list
        except Exception:
            return []
    
    def extract_file(self, file_path: Path, target_file: str, output_dir: Path) -> bool:
        """
        Extract a specific file from a ZIP archive.
        
        Args:
            file_path: Path to the ZIP file.
            target_file: Name of the file to extract.
            output_dir: Directory to extract to.
        
        Returns:
            True if extraction successful, False otherwise.
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if target_file in zf.namelist():
                    output_dir.mkdir(parents=True, exist_ok=True)
                    zf.extract(target_file, output_dir)
                    return True
            return False
        except Exception:
            return False
