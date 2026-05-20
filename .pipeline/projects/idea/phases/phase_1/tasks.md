# Phase 1 Tasks

- [ ] Task 1: Create project package structure and core library module
  - What: Create the `src/audiobook2pdf/` Python package with `__init__.py`, version info, and public API surface so the library is importable.
  - Done when: `import audiobook2pdf` succeeds and exposes a clean public API.

- [ ] Task 2: Implement audiobook metadata extractor
  - What: Build `src/audiobook2pdf/extractor.py` that reads Amazon audiobook files (m4b/mp4 containers), extracts metadata (title, author, narrator, cover art, chapter markers, duration).
  - Done when: Given a valid m4b/mp4 file path, the extractor returns a dict with title, author, cover_art_bytes, and chapters list.

- [ ] Task 3: Implement PDF generation module
  - What: Build `src/audiobook2pdf/pdf_generator.py` that takes extracted metadata and produces a PDF containing the cover art, metadata page, and chapter listing.
  - Done when: Given metadata dict, the generator writes a valid PDF file to disk.

- [ ] Task 4: Implement CLI entry point
  - What: Build `src/audiobook2pdf/cli.py` with a `main()` function that accepts input file path and output PDF path via command-line arguments, orchestrating extraction and PDF generation.
  - Done when: Running `python -m audiobook2pdf input.m4b output.pdf` produces a PDF from an audiobook file.

- [ ] Task 5: Add integration smoke test
  - What: Create `tests/test_integration.py` with a smoke test that verifies the full pipeline (extract → generate PDF) works end-to-end using a synthetic or sample audiobook file.
  - Done when: `pytest tests/` passes, confirming the importable library and CLI work together.