# Multi-Format Export Engine

A Python library for exporting literary manuscripts to multiple formats (EPUB, PDF, MOBI) with a pluggable exporter architecture.

## Features

- **Pluggable Exporters**: Register custom exporters via a simple interface
- **Multiple Formats**: EPUB3, PDF (via WeasyPrint), and MOBI (via calibre)
- **Manuscript Model**: Rich data model with Paragraph, Heading, Chapter, and Manuscript types
- **Export Engine**: Central dispatch system for format routing
- **Validation**: Built-in manuscript and export option validation

## Installation

```bash
pip install multi-format-export-engine
```

### Optional dependencies

- **PDF export**: `pip install weasyprint`
- **MOBI export**: Requires [calibre](https://calibre-ebook.com/) installed on your system

## Quick Start

```python
from multi_format_export_engine.models import Manuscript
from multi_format_export_engine.export_engine import ExportEngine

# Create a manuscript
m = Manuscript(title="My Book", author="Author Name")
ch = m.add_chapter_title("Chapter 1")
ch.add_heading("Introduction", level=2)
ch.add_paragraph("This is the first paragraph.")
ch.add_paragraph("This is the second paragraph.")

# Create export engine and register exporters
engine = ExportEngine()
engine.register_exporter("epub", EPUBExporter())
engine.register_exporter("pdf", PDFExporter())
engine.register_exporter("mobi", MOBIExporter(calibre_path="/usr/bin/calibre"))

# Export!
engine.export("epub", m)  # → "My_Book.epub"
engine.export("pdf", m, margins={"top": "1in"})  # → "My_Book.pdf"
```

## Manuscript Model

```python
from multi_format_export_engine.models import Manuscript, Chapter, Heading, Paragraph

# Create a manuscript
m = Manuscript(title="Book Title", author="Author")
m.metadata["genre"] = "fiction"
m.metadata["year"] = 2024

# Add chapters
ch = m.add_chapter_title("Chapter 1")

# Add headings and paragraphs
ch.add_heading("Section 1", level=2)
ch.add_paragraph("Some text here.")
ch.add_paragraph("More text.", style="bold")

# Multiple chapters
ch2 = m.add_chapter_title("Chapter 2")
ch2.add_heading("Details", level=2)
ch2.add_paragraph("Details go here.")
```

## Export Options

### EPUB Exporter

```python
from multi_format_export_engine.exporters import EPUBExporter

engine.register_exporter("epub", EPUBExporter())
engine.export("epub", m, output_path="custom.epub")
```

### PDF Exporter

```python
from multi_format_export_engine.exporters import PDFExporter

engine.register_exporter("pdf", PDFExporter())
engine.export("pdf", m,
    margins={"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"},
    font_family="serif",
    font_size=12,
    line_height=1.6,
    page_size="A4"
)
```

### MOBI Exporter

```python
from multi_format_export_engine.exporters import MOBIExporter

engine.register_exporter("mobi", MOBIExporter(calibre_path="/usr/bin/calibre"))
engine.export("mobi", m, output_path="book.mobi")
```

## Validation

```python
from multi_format_export_engine.validation import validate_manuscript, validate_export_options

# Validate a manuscript before export
validate_manuscript(m)  # Raises ValueError if invalid

# Validate export options
validate_export_options({
    "font_size": 12,
    "margins": {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
})
```

## Architecture

```
multi_format_export_engine/
├── __init__.py
├── models.py           # Manuscript, Chapter, Heading, Paragraph
├── export_engine.py    # ExportEngine (dispatcher)
├── validation.py       # Validation utilities
├── exporters/
│   ├── __init__.py
│   ├── epub_exporter.py  # EPUB3 export
│   ├── pdf_exporter.py   # PDF export (WeasyPrint)
│   └── mobi_exporter.py  # MOBI export (calibre)
└── __main__.py         # CLI entry point
```

## Running Tests

```bash
pip install pytest
pytest
```

## License

MIT
