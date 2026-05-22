# Email Attachment Processing Module

A comprehensive module for processing email attachments with support for multiple file types, flexible action execution, and detailed monitoring capabilities.

## Overview

This module provides a complete solution for:
- **Attachment Type Detection**: Automatically identify file types from MIME types and filenames
- **Multi-Format Parsing**: Parse PDF, Office documents (Word, Excel, PowerPoint), and text files
- **Flexible Actions**: Save, move, or delete attachments with collision handling
- **Pipeline Processing**: Build and execute processing pipelines with retry logic
- **Monitoring**: Track processing progress, success rates, and performance metrics

## Features

### 1. Attachment Type Detection
- Detect file types from MIME types and file extensions
- Support for PDF, Office documents (DOCX, XLSX, PPTX), text files (TXT, CSV), and images
- Automatic fallback to filename-based detection when MIME type is unavailable

### 2. Multi-Format Parsing
- **PDF Attachment Parser**: Extract text content from PDF files
- **Office Attachment Parser**: Extract text from Word, Excel, and PowerPoint documents
- **Text Attachment Parser**: Read plain text and CSV files

### 3. Action Execution
- **Save**: Copy attachments to a target location
- **Move**: Move attachments to a target location
- **Delete**: Remove attachments
- **Collision Handling**: Rename, overwrite, or skip on file conflicts

### 4. Pipeline Processing
- **Builder Pattern**: Construct custom processing pipelines
- **Retry Logic**: Automatic retry on failures with configurable delays
- **Dry Run Mode**: Test configurations without making changes

### 5. Monitoring and Statistics
- **Processing Statistics**: Track total, successful, and failed operations
- **Parser Performance**: Monitor performance of individual parsers
- **Type Performance**: Track processing by attachment type
- **Success Rate**: Calculate and display success rates

## Installation

No additional installation required. The module is part of the email_tool package.

## Quick Start

### Basic Processing

```python
from email_tool.attachment_processor import AttachmentProcessor
from email_tool.attachment_types import AttachmentType

# Initialize processor
processor = AttachmentProcessor(
    base_path="/path/to/base",
    dry_run=True
)

# Process an attachment
result = processor.process_attachment(
    file_path="/path/to/file.pdf",
    attachment_id="attachment_001",
    email_id="email_001",
    original_filename="document.pdf",
    content_type="application/pdf",
    size_bytes=1024,
    attachment_type=AttachmentType.PDF
)

if result.success:
    print(f"Processed: {result.text_content}")
else:
    print(f"Error: {result.error_message}")
```

### Using the Pipeline Builder

```python
from email_tool.attachment_processor import AttachmentPipelineBuilder

# Build a custom pipeline
builder = AttachmentPipelineBuilder()
builder.set_base_path("/path/to/base")
builder.set_dry_run(False)
builder.set_collision_strategy("rename")
builder.set_save_path("/path/to/save")
builder.set_retry_config(max_retries=5, retry_delay=2.0)

# Build the executor
executor = builder.build()

# Execute the pipeline
results = executor.execute(
    email=email,
    attachments=["file1.pdf", "file2.docx"],
    action_type="save"
)
```

### Monitoring Progress

```python
from email_tool.attachment_processor import AttachmentPipelineMonitor

# Initialize monitor
monitor = AttachmentPipelineMonitor(processor)

# Get status
status = monitor.get_status()
print(f"Success rate: {status['success_rate']}%")

# Get parser performance
parser_perf = monitor.get_parser_performance()
for parser, perf in parser_perf.items():
    print(f"{parser}: {perf['processed']} processed")
```

## API Reference

### Attachment Types

```python
from email_tool.attachment_types import (
    AttachmentType,
    get_attachment_type,
    is_text_attachment,
    is_image_attachment,
    is_office_attachment,
    is_pdf_attachment,
    get_supported_types
)

# Detect attachment type
attachment_type = get_attachment_type(
    mime_type="application/pdf",
    filename="document.pdf"
)

# Check attachment type
if is_pdf_attachment(attachment_type):
    print("This is a PDF file")
```

### Attachment Parsers

```python
from email_tool.attachment_parsers.pdf import PDFAttachmentParser
from email_tool.attachment_parsers.office import OfficeAttachmentParser
from email_tool.attachment_parsers.text import TextAttachmentParser

# Initialize parsers
pdf_parser = PDFAttachmentParser(base_path="/path/to/parsers")
office_parser = OfficeAttachmentParser(base_path="/path/to/parsers")
text_parser = TextAttachmentParser(base_path="/path/to/parsers")

# Parse attachments
result = pdf_parser.parse(
    file_path="/path/to/file.pdf",
    attachment_id="attachment_001",
    email_id="email_001",
    original_filename="document.pdf",
    content_type="application/pdf",
    size_bytes=1024,
    attachment_type=AttachmentType.PDF
)
```

### Attachment Processor

```python
from email_tool.attachment_processor import AttachmentProcessor

# Initialize processor
processor = AttachmentProcessor(
    base_path="/path/to/base",
    dry_run=True
)

# Process attachment
result = processor.process_attachment(
    file_path="/path/to/file.pdf",
    attachment_id="attachment_001",
    email_id="email_001",
    original_filename="document.pdf",
    content_type="application/pdf",
    size_bytes=1024,
    attachment_type=AttachmentType.PDF
)

# Get statistics
stats = processor.get_stats()
print(f"Total processed: {stats['total_processed']}")
```

### Attachment Dispatcher

```python
from email_tool.attachment_processor import AttachmentDispatcher

# Initialize dispatcher
dispatcher = AttachmentDispatcher(
    base_path="/path/to/base",
    dry_run=True
)

# Save attachment
result = dispatcher.save_attachment(
    file_path="/path/to/source.txt",
    target_path="/path/to/target.txt",
    attachment_id="attachment_001"
)

# Move attachment
result = dispatcher.move_attachment(
    file_path="/path/to/source.txt",
    target_path="/path/to/target.txt",
    attachment_id="attachment_001"
)

# Delete attachment
result = dispatcher.delete_attachment(
    file_path="/path/to/file.txt",
    attachment_id="attachment_001"
)
```

### Attachment Pipeline Executor

```python
from email_tool.attachment_processor import AttachmentPipelineBuilder

# Build executor
builder = AttachmentPipelineBuilder()
builder.set_base_path("/path/to/base")
builder.set_dry_run(False)
executor = builder.build()

# Execute pipeline
results = executor.execute(
    email=email,
    attachments=["file1.pdf", "file2.docx"],
    action_type="save"
)

# Process results
for result in results:
    if result['success']:
        print(f"Processed: {result['original_filename']}")
    else:
        print(f"Failed: {result['original_filename']} - {result['error_message']}")
```

### Configuration

```python
from email_tool.attachment_processor import AttachmentPipelineConfig

# Create configuration
config = AttachmentPipelineConfig(
    base_path="/path/to/base",
    dry_run=True,
    collision_strategy="overwrite",
    max_retries=5,
    retry_delay=2.0,
    save_path="/path/to/save"
)

# Convert to dictionary
config_dict = config.to_dict()

# Create from dictionary
config = AttachmentPipelineConfig.from_dict(config_dict)

# Convert to executor
executor = config.to_executor()
```

## Supported File Types

### Text Files
- `.txt` - Plain text files
- `.csv` - Comma-separated values files

### Office Documents
- `.docx` - Microsoft Word documents
- `.xlsx` - Microsoft Excel spreadsheets
- `.pptx` - Microsoft PowerPoint presentations

### PDF Files
- `.pdf` - Adobe PDF documents

### Image Files
- `.jpg`, `.jpeg` - JPEG images
- `.png` - PNG images
- `.gif` - GIF images
- `.bmp` - Bitmap images

## Error Handling

The module provides comprehensive error handling:

```python
result = processor.process_attachment(...)

if not result.success:
    print(f"Error: {result.error_message}")
    print(f"Attachment ID: {result.attachment_id}")
    print(f"Email ID: {result.email_id}")
```

Common error scenarios:
- File not found
- Invalid file format
- Permission denied
- Disk full
- Network errors (for remote storage)

## Best Practices

1. **Use Dry Run Mode**: Test your configurations with `dry_run=True` before running in production.

2. **Handle Collisions**: Choose an appropriate collision strategy for your use case:
   - `"rename"`: Automatically rename conflicting files (default)
   - `"overwrite"`: Overwrite existing files
   - `"skip"`: Skip processing if file exists

3. **Monitor Performance**: Use the monitoring features to track processing success rates and identify bottlenecks.

4. **Implement Retry Logic**: Use the built-in retry configuration to handle transient failures.

5. **Validate Attachments**: Always validate attachment types before processing to ensure compatibility.

## Examples

See the `examples/` directory for complete examples:

- `example_attachment_processing.py` - Comprehensive examples of all features
- `example_basic_usage.py` - Basic usage patterns
- `example_pipeline_builder.py` - Pipeline builder patterns
- `example_monitoring.py` - Monitoring and statistics

## Testing

Run the test suite:

```bash
cd workspace/email_tool
python -m pytest tests/ -v
```

## License

This module is part of the email_tool package.

## Contributing

Contributions are welcome! Please follow the existing code style and include tests for new features.
