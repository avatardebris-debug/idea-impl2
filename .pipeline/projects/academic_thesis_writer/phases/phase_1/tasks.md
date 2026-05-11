# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and core data models
  - What: Create the Python project structure, install dependencies, and define the Thesis Project data model (Topic, Source, Section, Citation, BibliographyEntry) as Pydantic models. Set up SQLite storage layer for project metadata.
  - Files: `backend/pyproject.toml`, `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/models.py`, `backend/app/database.py`, `backend/app/config.py`
  - Done when: Project installs cleanly with `pip install -e backend/`; all Pydantic models validate correctly; SQLite database initializes and can store/retrieve a project with a topic and ≥3 sources.

- [ ] Task 2: Source ingestion module
  - What: Build the source ingestion pipeline that accepts sources via three methods: (1) manual entry (title, authors, year, abstract, URL), (2) URL fetch (extracts metadata from HTML/arXiv/PDF), and (3) PDF upload (extracts title, authors, year, abstract using pdfplumber/textract). Stores extracted text and metadata in the database.
  - Files: `backend/app/sources.py`, `backend/app/ingestion/url_fetcher.py`, `backend/app/ingestion/pdf_extractor.py`, `backend/app/ingestion/manual_entry.py`, `backend/app/ingestion/__init__.py`
  - Done when: Can add a source via manual entry and it persists; can add a source via URL (e.g., arXiv link) and metadata is extracted correctly; can upload a PDF and extract title/authors/year/abstract; all three methods produce a valid Source model with ≥80% metadata completeness.

- [ ] Task 3: Citation engine with CSL style support
  - What: Implement the citation engine that manages bibliography entries and formats inline citations and bibliography lists in four styles: APA 7th, MLA 9th, Chicago 17th, and IEEE. Uses the `citeproc-py` or a custom CSL formatter. Generates unique citation keys (e.g., AuthorYear) and resolves them for inline use.
  - Files: `backend/app/citation/engine.py`, `backend/app/citation/formatters/apa.py`, `backend/app/citation/formatters/mla.py`, `backend/app/citation/formatters/chicago.py`, `backend/app/citation/formatters/ieee.py`, `backend/app/citation/formatters/__init__.py`, `backend/app/citation/key_generator.py`
  - Done when: All four citation styles produce correctly formatted bibliography entries matching the official style guide (verified against known examples); inline citation keys map 1:1 to bibliography entries; bidirectional lookup (inline→bib entry and bib entry→inline) works; citation key generation is deterministic and collision-free.

- [ ] Task 4: Draft generation pipeline with LLM orchestration
  - What: Build the section-by-section thesis generation pipeline. Creates prompts that inject the topic, source texts, citation style, and section outline. Calls the LLM (configurable via OpenAI or local model) to generate each section (Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion) with inline citation markers (e.g., [AuthorYear]). Includes a post-generation citation verification pass that ensures every inline citation has a corresponding bibliography entry.
  - Files: `backend/app/generation/pipeline.py`, `backend/app/generation/prompts.py`, `backend/app/generation/llm_client.py`, `backend/app/generation/verification.py`, `backend/app/generation/__init__.py`
  - Done when: Given a topic and ≥3 sources, the pipeline generates a complete 7-section draft with ≥10 inline citations; every inline citation has a matching bibliography entry; the draft is ≥5 pages when rendered; LLM provider can be swapped via config (OpenAI default, local fallback); citation verification pass catches missing entries.

- [ ] Task 5: FastAPI backend API with export endpoints
  - What: Build the FastAPI REST API that exposes endpoints for the full workflow: create project, add sources, generate thesis, preview draft, select citation style, and export. Add Markdown and DOCX export endpoints using python-docx for DOCX generation (preserving citation formatting and section structure) and a simple Markdown renderer.
  - Files: `backend/app/api/routes.py`, `backend/app/api/export/markdown.py`, `backend/app/api/export/docx.py`, `backend/app/api/export/__init__.py`, `backend/app/main.py`
  - Done when: `POST /projects` creates a project; `POST /projects/{id}/sources` adds sources; `POST /projects/{id}/generate` triggers generation; `GET /projects/{id}/draft` returns the draft; `GET /projects/{id}/export/markdown` returns formatted Markdown; `GET /projects/{id}/export/docx` returns a DOCX file with correct section headings, inline citations, and bibliography; DOCX preserves citation formatting and section structure.

- [ ] Task 6: Minimal web editor (single-page app)
  - What: Build a single-page React/Next.js web editor with: (1) topic input form, (2) source list panel (add/remove sources, view metadata), (3) citation style selector dropdown, (4) generated draft preview panel with rendered inline citations and bibliography, (5) export buttons (Markdown, DOCX). Uses the FastAPI backend via fetch/axios.
  - Files: `frontend/package.json`, `frontend/next.config.js`, `frontend/src/app/page.tsx`, `frontend/src/app/globals.css`, `frontend/src/components/TopicInput.tsx`, `frontend/src/components/SourceList.tsx`, `frontend/src/components/CitationStyleSelector.tsx`, `frontend/src/components/DraftPreview.tsx`, `frontend/src/components/ExportButtons.tsx`, `frontend/src/lib/api.ts`
  - Done when: User can create a project, add ≥3 sources, select a citation style, trigger generation, and see the draft with inline citations and bibliography rendered; export buttons download correctly formatted Markdown and DOCX files; end-to-end flow (topic input → source addition → generation → preview) completes in < 5 minutes for a 10-source project.