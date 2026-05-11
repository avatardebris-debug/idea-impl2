# Phase 1 Tasks

- [x] Task 1: Project scaffolding and core data model
  - What: Create the project structure and define the core manuscript data model (Chapter, Paragraph, Heading, etc.) that the export engine will operate on.
  - Files: multi_format_export_engine/__init__.py, multi_format_export_engine/models.py, multi_format_export_engine/export_engine.py
  - Done when: models.py defines a Manuscript class with chapters and content; export_engine.py defines an ExportEngine class with a base export() method that can be subclassed; project is importable via `from multi_format_export_engine import ExportEngine, Manuscript`.

- [x] Task 2: EPUB export implementation
  - What: Implement EPUB export — generate a valid EPUB3 package with proper structure (container.xml, content.opf, spine, chapter files as XHTML).
  - Files: multi_format_export_engine/exporters/epub_exporter.py
  - Done when: ExportEngine.export('epub', manuscript) produces a valid .epub file (zip with correct mimetype, META-INF/container.xml, and OPF manifest); exported EPUB opens in a standard reader without errors.

- [x] Task 3: PDF export implementation
  - What: Implement print-ready PDF export using a document generation library (e.g., weasyprint or reportlab) with configurable margins and typography.
  - Files: multi_format_export_engine/exporters/pdf_exporter.py
  - Done when: ExportEngine.export('pdf', manuscript) produces a .pdf file with proper page margins, chapter headings, and body text; margins and font settings are configurable via export options.

- [x] Task 4: MOBI export implementation
  - What: Implement MOBI export — convert manuscript to MOBI format (using calibre's ebook-convert or a direct EPUB-to-MOBI pipeline).
  - Files: multi_format_export_engine/exporters/mobi_exporter.py
  - Done when: ExportEngine.export('mobi', manuscript) produces a .mobi file; the file is a valid MOBI/KB8K container that can be read by Kindle devices or the Kindle Previewer.

- [x] Task 5: CLI entry point
  - What: Build a command-line interface so users can run the export engine from the terminal (e.g., `python -m multi_format_export_engine input.txt --format epub`).
  - Files: multi_format_export_engine/__main__.py
  - Done when: Running `python -m multi_format_export_engine --help` shows usage; passing a manuscript file and format flag produces the corresponding export file in the current directory.