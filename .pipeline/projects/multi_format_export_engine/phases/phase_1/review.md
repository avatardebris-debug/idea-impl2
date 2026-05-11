# Phase 1 Review — Multi-Format Export Engine

## What's Good

- Clean, well-structured data model: `Manuscript`, `Chapter`, `Heading`, and `Paragraph` dataclasses are simple, type-hinted, and easy to extend.
- `ExportEngine` uses a clean registration pattern (`register_exporter`) that makes adding new formats trivial.
- EPUB exporter produces a structurally valid EPUB3: correct mimetype (stored uncompressed, first in archive), `META-INF/container.xml`, `content.opf` with manifest/spine, `nav.xhtml` with `epub:type="toc"`, and per-chapter XHTML files.
- PDF exporter uses WeasyPrint with configurable margins, font_family, font_size, line_height, and page_size — all properly defaulted.
- MOBI exporter has a sensible fallback strategy: tries calibre's `ebook-convert`, falls back to EPUB if unavailable, and even renames the extension honestly.
- CLI (`__main__.py`) is comprehensive: argparse with all documented flags, plain-text manuscript parser, margin parser, and proper error handling (missing file → stderr + exit).
- The `_escape_html` helper is used consistently across EPUB and PDF exporters to prevent HTML injection.
- `conftest.py` correctly injects the workspace into `sys.path` for pytest import resolution.
- `__init__.py` exposes the public API cleanly via `__all__`.

## Blocking Bugs

- **epub_exporter.py:108** — `chr(10).join(...)` is used inside an f-string that is already a triple-quoted string. The f-string `f"""...{chr(10).join(manifest_entries)}..."""` works but is fragile: the `chr(10)` call is evaluated at f-string interpolation time, which is correct, but the same pattern is repeated for `spine_entries` and `nav_content`. This is functionally correct but worth noting.

- **epub_exporter.py:108–110** — The `opf_content` f-string uses `chr(10).join(manifest_entries)` and `chr(10).join(spine_entries)` inside triple-quoted f-strings. While this works, the indentation of the joined entries will not match the surrounding XML indentation because `chr(10).join()` produces lines without leading whitespace. The manifest entries already include their own leading spaces (`    <item ...>`), so the output is actually correct. **No bug.**

- **pdf_exporter.py:38** — The `margins` dict is mutated in-place via `margins.setdefault(key, "1in")`. Since `margins` is a local variable from `options.get()`, this is safe. **No bug.**

- **mobi_exporter.py:62** — `shutil.copy2(epub_path, fallback_path)` copies the EPUB to the fallback path. If `output_path` was `output.mobi`, `fallback_path` becomes `output.epub`. This is correct behavior. **No bug.**

- **__main__.py:126** — `export_options` is only populated for `pdf` format. For `epub` and `mobi`, `**export_options` expands to `{}`, which is fine. **No bug.**

- **models.py:10** — `style: str = "normal"` accepts arbitrary style values. No validation, but this is by design for extensibility. **No bug.**

- **models.py:44** — `metadata: dict = field(default_factory=dict)` is a mutable default via `default_factory`, which is correct for dataclasses. **No bug.**

- **epub_exporter.py:115** — The nav.xhtml uses `zip` with a list comprehension to pair filenames and chapters. This works correctly because both lists are built in the same order. **No bug.**

- **epub_exporter.py:133** — `style.css` uses `page-break-before: always` on `h1`, which means even the first chapter's heading gets a page break in EPUB readers. This is a minor rendering quirk, not a crash or wrong-output bug.

- **pdf_exporter.py:52** — The `@page` CSS margin shorthand uses `{margins['top']} {margins['right']} {margins['bottom']} {margins['left']}`. If any margin key is missing, this would raise a KeyError. However, the earlier loop (line 38) ensures all keys exist. **No bug.**

**Verdict on blocking bugs: None.** All identified issues are either non-issues or minor rendering/style concerns.

## Non-Blocking Notes

- **epub_exporter.py:27** — `_chapter_to_xhtml` takes a `chapter_index` parameter but never uses it. Consider removing it for cleanliness.
- **epub_exporter.py:108** — Using `chr(10).join()` inside f-strings is unconventional. Consider building the strings with explicit newline joins outside the f-string for readability.
- **epub_exporter.py:133** — The CSS `text-indent: 1em` on paragraphs is good, but `text-align: justify` on body may cause uneven word spacing in narrow columns. Consider `text-align: left` or `text-align: start` for better EPUB rendering.
- **pdf_exporter.py:52** — The `@page` margin shorthand order (top right bottom left) is correct for CSS, but the variable interpolation could be clearer with a named format string.
- **mobi_exporter.py:62** — The fallback to EPUB with a `.mobi` extension rename would be more honest as `.epub`. The code already does this (line 61 strips `.mobi` and appends `.epub`), which is good.
- **__main__.py:15** — The plain-text parser is simple but doesn't handle edge cases like `#` without a space, or `##` inside a paragraph. This is acceptable for Phase 1.
- **models.py** — The `Chapter.add_heading()` and `Chapter.add_paragraph()` methods are convenient but bypass the dataclass constructor. Consider whether this adds value over direct list appends.
- **No type annotations** on `EPUBExporter.export()`, `PDFExporter.export()`, and `MOBIExporter.export()` return types (they return `str` implicitly). Adding explicit `-> str` would improve documentation.
- **No logging** anywhere in the codebase. Consider adding `logging` for debug/info output, especially in the MOBI exporter's calibre fallback path.
- **No input validation** on manuscript content (e.g., empty title, empty chapters). The CLI parser handles missing files, but the engine itself doesn't validate the manuscript.

## Reusable Components

1. **`_escape_html` helper** — A simple, self-contained HTML-escaping function used in both epub_exporter.py and pdf_exporter.py. Could be extracted to a shared utility module.
2. **`ExportEngine` registration pattern** — The `ExportEngine` class with its `register_exporter` / `export` dispatch pattern is a clean, reusable plugin architecture for format converters.
3. **`_parse_margins` CLI helper** — A self-contained function that parses margin strings like `'top=1in right=1in bottom=1in left=1in'` into a dict. Useful for any CLI that needs margin configuration.
4. **`Manuscript` data model** — The `Manuscript`, `Chapter`, `Heading`, `Paragraph` dataclass hierarchy is a clean, reusable document model that could serve as a foundation for other document-processing projects.

## Verdict

**PASS** — No blocking bugs; all acceptance criteria met, code is importable, and the architecture is clean and extensible.
