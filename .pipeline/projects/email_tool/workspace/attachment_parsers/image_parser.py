"""Image attachment parser for extracting metadata from image files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from email_tool.attachment_parsers.base import ParsedAttachment, AbstractAttachmentParser, AttachmentMetadata
from email_tool.attachment_types import AttachmentType, is_image_attachment


class ImageAttachmentParser(AbstractAttachmentParser):
    """
    Parser for image attachments.
    
    Extracts metadata about image dimensions, format, color mode,
    and other properties.
    """
    
    # All image attachment types
    SUPPORTED_TYPES: Set[AttachmentType] = {
        AttachmentType.PNG,
        AttachmentType.JPG,
        AttachmentType.JPEG,
        AttachmentType.GIF,
        AttachmentType.BMP,
        AttachmentType.TIFF,
    }
    
    FORMAT_MAP = {
        '.PNG': 'PNG',
        '.JPG': 'JPEG',
        '.JPEG': 'JPEG',
        '.GIF': 'GIF',
        '.BMP': 'BMP',
        '.TIFF': 'TIFF',
        '.TIF': 'TIFF',
        '.WEBP': 'WEBP',
    }
    
    def __init__(self, staging_dir: str = "./staging"):
        """
        Initialize the image attachment parser.
        
        Args:
            staging_dir: Directory where attachments are stored.
        """
        super().__init__(staging_dir)
    
    def get_parser_name(self) -> str:
        """Return the parser name."""
        return "ImageAttachmentParser"
    
    def can_parse(self, attachment_type: AttachmentType) -> bool:
        """Check if this parser can handle the attachment type."""
        return attachment_type in self.SUPPORTED_TYPES
    
    def extract_text(self, file_path: Path, attachment_id: str, email_id: str) -> ParsedAttachment:
        """
        Extract text content from an image file.
        
        Args:
            file_path: Path to the image file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
        
        Returns:
            ParsedAttachment with extracted text content.
        """
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                
                # Check for transparency
                has_transparency = 'A' in mode or 'RGBA' in mode or 'LA' in mode
                
                # Calculate aspect ratio
                aspect_ratio = round(width / height, 2) if height > 0 else None
                
                metadata = {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'color_mode': mode,
                    'has_transparency': has_transparency,
                    'aspect_ratio': aspect_ratio,
                }
                
                text_content = self._generate_text_content(file_path.name, metadata, file_path.stat().st_size)
                
                return ParsedAttachment(
                    attachment_id=attachment_id,
                    email_id=email_id,
                    original_filename=file_path.name,
                    content_type="image",
                    size_bytes=file_path.stat().st_size,
                    attachment_type=self._get_attachment_type_from_format(format_name),
                    text_content=text_content,
                    metadata=metadata,
                    success=True
                )
                
        except ImportError:
            # PIL not available, return basic info
            metadata = {
                'width': None,
                'height': None,
                'format': self._guess_format_from_filename(file_path.name),
                'color_mode': None,
                'has_transparency': None,
                'aspect_ratio': None,
            }
            
            text_content = self._generate_text_content(file_path.name, metadata, file_path.stat().st_size)
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="image",
                size_bytes=file_path.stat().st_size,
                attachment_type=self._get_attachment_type_from_filename(file_path.name),
                text_content=text_content,
                metadata=metadata,
                success=False,
                error_message="PIL library not available"
            )
        except Exception as e:
            # Failed to open image, return minimal info
            metadata = {
                'width': None,
                'height': None,
                'format': self._guess_format_from_filename(file_path.name),
                'color_mode': None,
                'has_transparency': None,
                'aspect_ratio': None,
            }
            
            text_content = self._generate_text_content(file_path.name, metadata, file_path.stat().st_size)
            
            return ParsedAttachment(
                attachment_id=attachment_id,
                email_id=email_id,
                original_filename=file_path.name,
                content_type="image",
                size_bytes=file_path.stat().st_size,
                attachment_type=self._get_attachment_type_from_filename(file_path.name),
                text_content=text_content,
                metadata=metadata,
                success=False,
                error_message=f"Failed to parse image: {str(e)}"
            )
    
    def extract_metadata(self, file_path: Path) -> AttachmentMetadata:
        """
        Extract metadata from an image file.
        
        Args:
            file_path: Path to the image file.
        
        Returns:
            AttachmentMetadata object with extracted metadata.
        """
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                
                # Check for transparency
                has_transparency = 'A' in mode or 'RGBA' in mode or 'LA' in mode
                
                # Calculate aspect ratio
                aspect_ratio = round(width / height, 2) if height > 0 else None
                
                additional_metadata = {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'color_mode': mode,
                    'has_transparency': has_transparency,
                    'aspect_ratio': aspect_ratio,
                }
                
                return AttachmentMetadata(
                    original_filename=file_path.name,
                    content_type="image",
                    size_bytes=file_path.stat().st_size,
                    attachment_type=self._get_attachment_type_from_format(format_name),
                    extracted_at=datetime.now().isoformat(),
                    parser_name=self.get_parser_name(),
                    additional_metadata=additional_metadata
                )
                
        except ImportError:
            # PIL not available, return basic info
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="image",
                size_bytes=file_path.stat().st_size,
                attachment_type=self._get_attachment_type_from_filename(file_path.name),
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata={
                    'format': self._guess_format_from_filename(file_path.name),
                }
            )
        except Exception:
            # Failed to open image, return minimal info
            return AttachmentMetadata(
                original_filename=file_path.name,
                content_type="image",
                size_bytes=file_path.stat().st_size,
                attachment_type=self._get_attachment_type_from_filename(file_path.name),
                extracted_at=datetime.now().isoformat(),
                parser_name=self.get_parser_name(),
                additional_metadata={
                    'format': self._guess_format_from_filename(file_path.name),
                }
            )
    
    def _guess_format_from_filename(self, filename: str) -> str:
        """Guess image format from filename extension."""
        ext = Path(filename).suffix.upper()
        return self.FORMAT_MAP.get(ext, ext[1:] if ext.startswith('.') else 'unknown')
    
    def _get_attachment_type_from_filename(self, filename: str) -> AttachmentType:
        """Get attachment type from filename."""
        return self._get_attachment_type_from_format(self._guess_format_from_filename(filename))
    
    def _get_attachment_type_from_format(self, format_name: str) -> AttachmentType:
        """Get attachment type from image format name."""
        if not format_name:
            return AttachmentType.UNKNOWN
        
        format_upper = format_name.upper()
        format_map = {
            'PNG': AttachmentType.PNG,
            'JPEG': AttachmentType.JPEG,
            'JPG': AttachmentType.JPG,
            'GIF': AttachmentType.GIF,
            'BMP': AttachmentType.BMP,
            'TIFF': AttachmentType.TIFF,
            'WEBP': AttachmentType.UNKNOWN,
        }
        return format_map.get(format_upper, AttachmentType.UNKNOWN)
    
    def _generate_text_content(self, filename: str, image_metadata: Dict[str, Any], size_bytes: int) -> str:
        """
        Generate searchable text content from image metadata.
        
        Args:
            filename: Original filename.
            image_metadata: Extracted image metadata.
            size_bytes: File size in bytes.
        
        Returns:
            Text content for search indexing.
        """
        parts = [
            f"Image file: {filename}",
            f"Size: {size_bytes} bytes",
        ]
        
        if image_metadata.get('width'):
            parts.append(f"Width: {image_metadata['width']} pixels")
        if image_metadata.get('height'):
            parts.append(f"Height: {image_metadata['height']} pixels")
        if image_metadata.get('format'):
            parts.append(f"Format: {image_metadata['format']}")
        if image_metadata.get('color_mode'):
            parts.append(f"Color mode: {image_metadata['color_mode']}")
        if image_metadata.get('has_transparency') is not None:
            parts.append(f"Transparency: {'Yes' if image_metadata['has_transparency'] else 'No'}")
        if image_metadata.get('aspect_ratio'):
            parts.append(f"Aspect ratio: {image_metadata['aspect_ratio']}")
        
        return " ".join(parts)
    
    def get_supported_formats(self) -> list:
        """Return list of supported image formats."""
        return [t.name for t in self.SUPPORTED_TYPES]
    
    def validate_image(self, file_path: Path) -> bool:
        """
        Validate that a file is a valid image.
        
        Args:
            file_path: Path to the file to validate.
        
        Returns:
            True if valid image, False otherwise.
        """
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False


class ImageAttachmentValidator:
    """
    Validator for image attachments.
    
    Checks file integrity and format validity before processing.
    """
    
    def __init__(self):
        """Initialize the image validator."""
        self._image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}
    
    def validate_extension(self, filename: str) -> bool:
        """
        Check if filename has a valid image extension.
        
        Args:
            filename: Filename to check.
        
        Returns:
            True if valid image extension.
        """
        ext = Path(filename).suffix.lower()
        return ext in self._image_extensions
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that a file is a valid image.
        
        Args:
            file_path: Path to the file to validate.
        
        Returns:
            True if valid image file.
        """
        if not file_path.exists():
            return False
        
        # Check extension first
        if not self.validate_extension(file_path.name):
            return False
        
        # Try to open with PIL
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def get_valid_extensions(self) -> list:
        """Return list of valid image extensions."""
        return list(self._image_extensions)
