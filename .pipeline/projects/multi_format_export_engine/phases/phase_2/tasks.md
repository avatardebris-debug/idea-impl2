# Phase 2 Tasks

- [ ] Task 1: Add unit tests for core models
  - What: Write tests for Paragraph, Heading, Chapter, and Manuscript dataclasses — including add_heading, add_paragraph, add_chapter, and add_chapter_title methods.
  - Files: tests/test_models.py (new)
  - Done when: All model methods are tested; tests cover normal paths, empty manuscript, and multi-chapter scenarios; pytest runs cleanly.

- [ ] Task 2: Add unit tests for ExportEngine
  - What: Write tests for ExportEngine.register_exporter and ExportEngine.export — including registering multiple formats, exporting with default output path, exporting with custom output path, and raising ValueError for unsupported formats.
  - Files: tests/test_export_engine.py (new)
  - Done when: Tests cover registration, export with default/custom paths, and error on unknown format; all pass with pytest.

- [ ] Task 3: Add unit tests for EPUBExporter
  - What: Write tests for EPUBExporter.export — verify that the output file is a valid ZIP, contains required EPUB3 structure (mimetype, META-INF/container.xml, content.opf, nav.xhtml, style.css, chapter files), and that chapter content is correctly rendered as XHTML.
  - Files: tests/test_epub_exporter.py (new)
  - Done when: Tests verify ZIP structure, required files present, correct XHTML output, and multi-chapter EPUB generation; all pass with pytest.

- [ ] Task 4: Add unit tests for PDFExporter and MOBIExporter
  - What: Write tests for PDFExporter.export — mock WeasyPrint to verify HTML generation with correct margins, font_family, font_size, and page_size options. Write tests for MOBIExporter.export — mock calibre availability and verify EPUB fallback behavior.
  - Files: tests/test_pdf_exporter.py (new), tests/test_mobi_exporter.py (new)
  - Done when: PDF tests verify HTML output contains expected CSS margins/fonts/page-size; MOBI tests verify calibre-used path and EPUB fallback path; all pass with pytest.

- [ ] Task 5: Add error handling and input validation
  - What: Add validation to the ExportEngine and exporters — validate that Manuscript has at least one chapter before exporting, validate margin key names, validate font_family/font_size are non-empty strings, and add graceful error messages for missing dependencies (WeasyPrint, calibre).
  - Files: multi_format_export_engine/export_engine.py (modify), multi_format_export_engine/exporters/pdf_exporter.py (modify), multi_format_export_engine/exporters/mobi_exporter.py (modify), multi_format_export_engine/models.py (modify)
  - Done when: Exporting an empty manuscript raises a clear ValueError; invalid margin keys raise ValueError with helpful message; missing WeasyPrint raises ImportError with install instructions; missing calibre falls back to EPUB with a warning; new tests in tests/test_validation.py cover all error paths.

- [ ] Task 6: Write README and project documentation
  - What: Create a comprehensive README.md at the project root covering: project overview, installation instructions (pip install, WeasyPrint dependency, calibre optional), usage examples (CLI and Python API), export format details (EPUB3, PDF, MOBI), configuration options (margins, fonts, page size), and a quick-start guide.
  - Files: README.md (new), docs/usage.md (new)
  - Done when: README.md has clear installation, usage, and configuration sections; docs/usage.md has API reference examples; both are well-formatted markdown.