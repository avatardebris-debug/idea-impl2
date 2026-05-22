"""Attachment type definitions for email attachments."""

from enum import Enum
from typing import Dict, Set


class AttachmentType(Enum):
    """Types of attachments that can be processed."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    TXT = "txt"
    CSV = "csv"
    ZIP = "zip"
    UNKNOWN = "unknown"


# MIME type to AttachmentType mapping
MIME_TYPE_TO_ATTACHMENT_TYPE: Dict[str, AttachmentType] = {
    # Documents
    "application/pdf": AttachmentType.PDF,
    "application/msword": AttachmentType.DOCX,  # Legacy Word
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": AttachmentType.DOCX,
    "application/vnd.ms-excel": AttachmentType.XLSX,  # Legacy Excel
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": AttachmentType.XLSX,
    "application/vnd.ms-powerpoint": AttachmentType.PPTX,  # Legacy PowerPoint
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": AttachmentType.PPTX,
    
    # Images
    "image/png": AttachmentType.PNG,
    "image/jpeg": AttachmentType.JPG,
    "image/jpg": AttachmentType.JPG,
    "image/gif": AttachmentType.GIF,
    "image/bmp": AttachmentType.BMP,
    "image/tiff": AttachmentType.TIFF,
    "image/x-tiff": AttachmentType.TIFF,
    
    # Text files
    "text/plain": AttachmentType.TXT,
    "text/csv": AttachmentType.CSV,
    
    # Archives
    "application/zip": AttachmentType.ZIP,
    "application/x-zip-compressed": AttachmentType.ZIP,
}

# File extension to AttachmentType mapping
EXTENSION_TO_ATTACHMENT_TYPE: Dict[str, AttachmentType] = {
    # Documents
    ".pdf": AttachmentType.PDF,
    ".doc": AttachmentType.DOCX,
    ".docx": AttachmentType.DOCX,
    ".xls": AttachmentType.XLSX,
    ".xlsx": AttachmentType.XLSX,
    ".ppt": AttachmentType.PPTX,
    ".pptx": AttachmentType.PPTX,
    
    # Images
    ".png": AttachmentType.PNG,
    ".jpg": AttachmentType.JPG,
    ".jpeg": AttachmentType.JPG,
    ".gif": AttachmentType.GIF,
    ".bmp": AttachmentType.BMP,
    ".tiff": AttachmentType.TIFF,
    ".tif": AttachmentType.TIFF,
    
    # Text files
    ".txt": AttachmentType.TXT,
    ".csv": AttachmentType.CSV,
    
    # Archives
    ".zip": AttachmentType.ZIP,
}


def get_attachment_type_from_mime(mime_type: str) -> AttachmentType:
    """
    Determine attachment type from MIME type.
    
    Args:
        mime_type: The MIME type of the attachment.
    
    Returns:
        AttachmentType enum value.
    """
    if not mime_type:
        return AttachmentType.UNKNOWN
    
    # Normalize MIME type
    mime_type_lower = mime_type.lower().strip()
    
    # Direct lookup
    if mime_type_lower in MIME_TYPE_TO_ATTACHMENT_TYPE:
        return MIME_TYPE_TO_ATTACHMENT_TYPE[mime_type_lower]
    
    # Check for subtype patterns (e.g., "application/pdf; name=foo.pdf")
    base_mime = mime_type_lower.split(';')[0].strip()
    if base_mime in MIME_TYPE_TO_ATTACHMENT_TYPE:
        return MIME_TYPE_TO_ATTACHMENT_TYPE[base_mime]
    
    return AttachmentType.UNKNOWN


def get_attachment_type_from_filename(filename: str) -> AttachmentType:
    """
    Determine attachment type from filename extension.
    
    Args:
        filename: The filename of the attachment.
    
    Returns:
        AttachmentType enum value.
    """
    if not filename:
        return AttachmentType.UNKNOWN
    
    # Get file extension
    filename_lower = filename.lower()
    for ext, attachment_type in EXTENSION_TO_ATTACHMENT_TYPE.items():
        if filename_lower.endswith(ext):
            return attachment_type
    
    return AttachmentType.UNKNOWN


def get_attachment_type(mime_type: str = None, filename: str = None) -> AttachmentType:
    """
    Determine attachment type from MIME type or filename.
    
    Priority: MIME type > filename extension
    
    Args:
        mime_type: The MIME type of the attachment.
        filename: The filename of the attachment.
    
    Returns:
        AttachmentType enum value.
    """
    # Try MIME type first
    if mime_type:
        attachment_type = get_attachment_type_from_mime(mime_type)
        if attachment_type != AttachmentType.UNKNOWN:
            return attachment_type
    
    # Fall back to filename
    if filename:
        return get_attachment_type_from_filename(filename)
    
    return AttachmentType.UNKNOWN


def is_text_attachment(attachment_type: AttachmentType) -> bool:
    """
    Check if an attachment type is text-based and can be parsed for content.
    
    Args:
        attachment_type: The attachment type to check.
    
    Returns:
        True if the attachment type is text-based, False otherwise.
    """
    text_types = {
        AttachmentType.TXT,
        AttachmentType.CSV,
    }
    return attachment_type in text_types


def is_image_attachment(attachment_type: AttachmentType) -> bool:
    """
    Check if an attachment type is an image.
    
    Args:
        attachment_type: The attachment type to check.
    
    Returns:
        True if the attachment type is an image, False otherwise.
    """
    image_types = {
        AttachmentType.PNG,
        AttachmentType.JPG,
        AttachmentType.JPEG,
        AttachmentType.GIF,
        AttachmentType.BMP,
        AttachmentType.TIFF,
    }
    return attachment_type in image_types


def get_supported_types() -> Set[AttachmentType]:
    """
    Get all supported attachment types.
    
    Returns:
        Set of all AttachmentType enum values.
    """
    return {
        AttachmentType.PDF,
        AttachmentType.DOCX,
        AttachmentType.XLSX,
        AttachmentType.PPTX,
        AttachmentType.PNG,
        AttachmentType.JPG,
        AttachmentType.JPEG,
        AttachmentType.GIF,
        AttachmentType.BMP,
        AttachmentType.TIFF,
        AttachmentType.TXT,
        AttachmentType.CSV,
        AttachmentType.ZIP,
    }


def is_office_attachment(attachment_type: AttachmentType) -> bool:
    """
    Check if an attachment type is a Microsoft Office file.
    
    Args:
        attachment_type: The attachment type to check.
    
    Returns:
        True if the attachment type is an Office file, False otherwise.
    """
    office_types = {
        AttachmentType.DOCX,
        AttachmentType.XLSX,
        AttachmentType.PPTX,
    }
    return attachment_type in office_types


def is_pdf_attachment(attachment_type: AttachmentType) -> bool:
    """
    Check if an attachment type is a PDF file.
    
    Args:
        attachment_type: The attachment type to check.
    
    Returns:
        True if the attachment type is a PDF, False otherwise.
    """
    return attachment_type == AttachmentType.PDF
