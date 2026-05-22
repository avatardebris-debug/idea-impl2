"""Attachment parsers package."""

from email_tool.attachment_parsers.base import AbstractAttachmentParser, ParsedAttachment
from email_tool.attachment_parsers.pdf import PDFAttachmentParser
from email_tool.attachment_parsers.office import OfficeAttachmentParser
from email_tool.attachment_parsers.text import TextAttachmentParser
from email_tool.attachment_parsers.image_parser import ImageAttachmentParser
from email_tool.attachment_parsers.zip_parser import ZipAttachmentParser

__all__ = [
    'AbstractAttachmentParser',
    'ParsedAttachment',
    'PDFAttachmentParser',
    'OfficeAttachmentParser',
    'TextAttachmentParser',
    'ImageAttachmentParser',
    'ZipAttachmentParser',
]
