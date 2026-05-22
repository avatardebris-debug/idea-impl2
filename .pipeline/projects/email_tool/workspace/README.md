# Email Attachment Processing System

A comprehensive system for extracting, parsing, and indexing email attachments.

## Overview

This system provides:

- **Attachment Type Detection**: Automatically identify attachment types from MIME types and filenames
- **Multi-format Parsing**: Support for PDF, Office documents (DOCX, XLSX, PPTX), and text files (TXT, CSV)
- **Content Extraction**: Extract text content from various file formats
- **Metadata Extraction**: Extract file metadata and content statistics
- **Indexing**: Searchable index of all processed attachments
- **Staging Management**: Temporary storage and cleanup of attachments

## Architecture

```
email_tool/
├── attachment_types.py          # Attachment type definitions and detection
├── attachment_parsers/
│   ├── __init__.py
│   ├── base.py                  # Abstract base parser
│   ├── pdf.py                   # PDF parser
│   ├── office.py                # Office document parser
│   └── text.py                  # Text file parser
├── attachment_processor.py      # Main processing logic
├── attachment_index.py          # Searchable index
└── tests/
    └── test_attachment_processing.py
```

## Quick Start

### Basic Usage

```python
from email_tool import AttachmentProcessor, AttachmentType

# Create processor
processor = AttachmentProcessor(
    staging_dir="/tmp/attachments",
    index_dir="/tmp/attachment_index"
)

# Process an attachment
attachment = {
    'filename': 'report.pdf',
    'content_type': 'application/pdf',
    'content': b'PDF content here',
    'size': 1024
}

result = processor.process_attachment(
    attachment=attachment,
    email_id="email-123"
)

if result.success:
    print(f"Extracted {len(result.text_content)} characters")
    print(f"Attachment ID: {result.attachment_id}")
```

### Searching Processed Attachments

```python
# Find all attachments from an email
email_attachments = processor.index.find_by_email("email-123")

# Find all PDF attachments
pdf_attachments = processor.index.find_by_type(AttachmentType.PDF)

# Search for text content
important_docs = processor.index.search_text("important", case_sensitive=False)
```

## Attachment Type Detection

The system automatically detects attachment types from:

1. **MIME Type** (highest priority)
2. **Filename extension** (fallback)

```python
from email_tool import get_attachment_type, AttachmentType

# From MIME type
attachment_type = get_attachment_type(mime_type="application/pdf")
# Returns: AttachmentType.PDF

# From filename
attachment_type = get_attachment_type(filename="document.docx")
# Returns: AttachmentType.DOCX

# Priority: MIME > filename
attachment_type = get_attachment_type(
    mime_type="application/pdf",
    filename="document.docx"
)
# Returns: AttachmentType.PDF
```

## Supported File Types

### Documents
- **PDF** (.pdf) - Full text extraction
- **Word** (.docx) - Text and metadata extraction
- **Excel** (.xlsx) - Cell content extraction
- **PowerPoint** (.pptx) - Slide text extraction

### Text Files
- **Plain Text** (.txt)
- **CSV** (.csv)
- **JSON** (.json)
- **XML** (.xml)

### Images
- **PNG**, **JPG**, **JPEG**, **GIF**, **BMP**, **TIFF**
- (Image parsing can be added as needed)

## Extending the System

### Adding a New Parser

1. Create a new parser class inheriting from `AbstractAttachmentParser`:

```python
from email_tool.attachment_parsers.base import AbstractAttachmentParser, ParsedAttachment
from email_tool.attachment_types import AttachmentType

class MyCustomParser(AbstractAttachmentParser):
    """Parser for custom file format."""
    
    SUPPORTED_TYPES = [AttachmentType.CUSTOM]
    
    def _parse_content(self, content: bytes) -> ParsedAttachment:
        """Parse the actual content."""
        # Your parsing logic here
        return ParsedAttachment(
            attachment_id=self.attachment_id,
            email_id=self.email_id,
            original_filename=self.original_filename,
            content_type=self.content_type,
            size_bytes=self.size_bytes,
            attachment_type=self.attachment_type,
            text_content="Extracted text",
            metadata={"custom_field": "value"},
            success=True
        )
```

2. Register the parser with the processor:

```python
processor = AttachmentProcessor(staging_dir="/tmp/attachments")
processor.parsers.append(MyCustomParser())
```

### Customizing Attachment Type Detection

Extend the MIME type and file extension mappings:

```python
from email_tool.attachment_types import (
    MIME_TYPE_TO_ATTACHMENT_TYPE,
    EXTENSION_TO_ATTACHMENT_TYPE,
    AttachmentType
)

# Add new MIME type
MIME_TYPE_TO_ATTACHMENT_TYPE["application/my-custom-type"] = AttachmentType.CUSTOM

# Add new file extension
EXTENSION_TO_ATTACHMENT_TYPE[".custom"] = AttachmentType.CUSTOM
```

## Error Handling

The system handles errors gracefully:

```python
result = processor.process_attachment(
    attachment=attachment,
    email_id="email-123"
)

if not result.success:
    print(f"Error: {result.error_message}")
    print(f"Attachment ID: {result.attachment_id}")
```

Common error scenarios:
- No parser available for attachment type
- File format corruption
- Unsupported file format
- Processing exceptions

## Performance Considerations

- **Staging Directory**: Automatically cleaned up after 1 hour
- **Index Persistence**: Saved to disk for fast retrieval
- **Parallel Processing**: Process multiple attachments concurrently
- **Memory Efficient**: Streams large files instead of loading entirely

## Testing

Run the test suite:

```bash
pytest email_tool/tests/test_attachment_processing.py -v
```

## License

MIT License - See LICENSE file for details.
