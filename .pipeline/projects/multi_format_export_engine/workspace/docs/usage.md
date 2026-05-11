# Usage Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Manuscript Model](#manuscript-model)
3. [Export Engine](#export-engine)
4. [Exporters](#exporters)
5. [Validation](#validation)
6. [Custom Exporters](#custom-exporters)
7. [CLI Usage](#cli-usage)

---

## Getting Started

### Installation

```bash
pip install multi-format-export-engine
```

### Basic Export

```python
from multi_format_export_engine.models import Manuscript
from multi_format_export_engine.export_engine import ExportEngine
from multi_format_export_engine.exporters import EPUBExporter, PDFExporter

# 1. Create a manuscript
m = Manuscript(title="My Novel", author="Jane Doe")
ch = m.add_chapter_title("Chapter 1")
ch.add_heading("The Beginning", level=2)
ch.add_paragraph("Once upon a time...")

# 2. Set up the export engine
engine = ExportEngine()
engine.register_exporter("epub", EPUBExporter())
engine.register_exporter("pdf", PDFExporter())

# 3. Export
engine.export("epub", m)  # Creates "My_Novel.epub"
engine.export("pdf", m)   # Creates "My_Novel.pdf"
```

---

## Manuscript Model

### Manuscript

The `Manuscript` class is the root of the document model.

```python
from multi_format_export_engine.models import Manuscript

m = Manuscript(
    title="Book Title",
    author="Author Name"
)
m.metadata["genre"] = "science fiction"
m.metadata["year"] = 2024
```

**Attributes:**
- `title` (str): The book title
- `author` (str): The author name
- `chapters` (list[Chapter]): List of chapters
- `metadata` (dict): Arbitrary metadata

### Chapter

```python
ch = m.add_chapter_title("Chapter 1")
ch.add_heading("Introduction", level=2)
ch.add_paragraph("Welcome to the book.")
```

**Methods:**
- `add_heading(text, level=1)`: Add a heading
- `add_paragraph(text, style="normal")`: Add a paragraph

### Heading

```python
from multi_format_export_engine.models import Heading

h = Heading(text="Section Title", level=2)
```

**Attributes:**
- `text` (str): The heading text
- `level` (int): Heading level (1-6)

### Paragraph

```python
from multi_format_export_engine.models import Paragraph

p = Paragraph(text="Some text", style="normal")
```

**Attributes:**
- `text` (str): The paragraph text
- `style` (str): Text style ("normal", "bold", "italic", etc.)

---

## Export Engine

The `ExportEngine` is a central dispatcher that routes export requests to registered exporters.

### Registration

```python
from multi_format_export_engine.export_engine import ExportEngine
from multi_format_export_engine.exporters import EPUBExporter, PDFExporter

engine = ExportEngine()
engine.register_exporter("epub", EPUBExporter())
engine.register_exporter("pdf", PDFExporter())
```

### Exporting

```python
# Default output path (based on manuscript title)
engine.export("epub", m)

# Custom output path
engine.export("epub", m, output_path="my_book.epub")

# With options
engine.export("pdf", m, margins={"top": "1in"}, font_size=14)
```

### Format Resolution

- Format names are case-insensitive (`"EPUB"` = `"epub"`)
- Unsupported formats raise `ValueError`
- The engine lists available formats in error messages

---

## Exporters

### EPUB Exporter

Generates valid EPUB3 packages with:
- Proper OPF manifest
- Navigation document (nav.xhtml)
- Chapter XHTML files
- Embedded CSS styles

```python
from multi_format_export_engine.exporters import EPUBExporter

engine.register_exporter("epub", EPUBExporter())
engine.export("epub", m)
```

### PDF Exporter

Generates print-ready PDFs using WeasyPrint.

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `margins` | dict | `{"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}` | Page margins |
| `font_family` | str | `"serif"` | CSS font family |
| `font_size` | str | `"12pt"` | CSS font size |
| `line_height` | float | `1.6` | Line height multiplier |
| `page_size` | str | `"A4"` | Page size (A4, Letter, Legal, A5, B5) |

```python
from multi_format_export_engine.exporters import PDFExporter

engine.register_exporter("pdf", PDFExporter())
engine.export("pdf", m,
    margins={"top": "1in", "right": "1.5in", "bottom": "1in", "left": "1.5in"},
    font_family="Georgia, serif",
    font_size="14pt",
    line_height=1.8,
    page_size="Letter"
)
```

### MOBI Exporter

Converts manuscripts to MOBI format using calibre's `ebook-convert`.

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `calibre_path` | str | `None` | Path to calibre's ebook-convert |
| `epub_path` | str | Auto-generated | Intermediate EPUB file path |

```python
from multi_format_export_engine.exporters import MOBIExporter

engine.register_exporter("mobi", MOBIExporter(calibre_path="/usr/bin/calibre"))
engine.export("mobi", m, output_path="book.mobi")
```

**Note:** If calibre is not available, the exporter falls back to returning the intermediate EPUB file.

---

## Validation

### Manuscript Validation

```python
from multi_format_export_engine.validation import validate_manuscript

validate_manuscript(m)  # Raises ValueError if invalid
```

Validates:
- Manuscript is not None
- Title is non-empty
- At least one chapter exists
- Each chapter has a title and content
- Content items have text attributes

### Export Options Validation

```python
from multi_format_export_engine.validation import validate_export_options

validate_export_options({
    "font_size": 12,
    "margins": {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
})
```

Validates:
- Options is not None
- `page_size` is one of: A4, Letter, Legal, A5, B5
- `font_family` is a string
- `line_height` is a positive number
- `font_size` is a positive number
- `margins` is a dict with valid keys (top/right/bottom/left) and string values ending in units (in, cm, px, pt)

---

## Custom Exporters

Implement the `export` method to create a custom exporter:

```python
from multi_format_export_engine.models import Manuscript

class MyExporter:
    def export(self, manuscript: Manuscript, output_path: str = "output.txt", **options) -> str:
        # Convert manuscript to your format
        with open(output_path, "w") as f:
            f.write(manuscript.title)
            for ch in manuscript.chapters:
                f.write(f"\n\n{ch.title}\n")
                for item in ch.content:
                    f.write(f"{item.text}\n")
        return output_path

# Register and use
engine.register_exporter("txt", MyExporter())
engine.export("txt", m, output_path="my_book.txt")
```

---

## CLI Usage

```bash
# Run the CLI
python -m multi_format_export_engine --help

# Export to EPUB
python -m multi_format_export_engine --format epub --input manuscript.json --output book.epub

# Export to PDF
python -m multi_format_export_engine --format pdf --input manuscript.json --output book.pdf
```
