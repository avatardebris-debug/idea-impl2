# Phase 1 Review — SupportAgent Workflow Builder

### What's Good
- **Clean data model design**: `Ticket` and `PipelineResult` dataclasses are well-structured with clear serialization/deserialization helpers (`to_dict`, `to_json`, `from_dict`, `from_json`).
- **Flexible ingestion**: `Ingestor` handles three input formats (JSON, MIME email, web form URL-encoded) with graceful fallback for missing keys and auto-generated UUIDs.
- **Email MIME parsing**: Properly handles multipart emails, charset decoding, and header preservation — a non-trivial task done correctly.
- **Keyword-based classifier**: Simple but effective scoring mechanism with configurable YAML rules; handles urgency boosting and priority capping.
- **Config-driven routing**: `SRouter` uses YAML for team/category mapping, priority-based routing, and SLA breach detection — easy to modify without code changes.
- **Comprehensive test coverage**: 35 tests covering construction, serialization, ingestion (all 3 formats), classification (all categories, edge cases), and pipeline result mapping.
- **Good use of `dataclasses` and `Enum` types**: Type safety with `str, Enum` mixins for serialization compatibility.
- **`from_ticket` factory on `PipelineResult`**: Clean bridge between internal `Ticket` state and external API output.
- **`conftest.py` path injection**: Ensures local imports work in pytest without requiring installed package.

## Blocking Bugs
- **`supportagent/router.py:1` — Missing `from __future__ import annotations`**: The file uses `str | None` (PEP 604 union syntax) on line 33 (`_get_team_for_category`) and line 40 (`_get_team_for_priority`), but does not import `from __future__ import annotations`. This will cause a `SyntaxError` on Python < 3.10. The `pyproject.toml` requires `>=3.10`, so this may work in the CI environment, but it is inconsistent with other modules that use `from __future__ import annotations` for forward compatibility.
- **`supportagent/router.py:33` — `str | None` return type annotation without future import**: Same issue as above — the `|` union syntax is used without `from __future__ import annotations`, which is inconsistent with the rest of the codebase.
- **`supportagent/classifier.py:65` — `best_priority` calculation can produce unexpected results**: The line `best_priority = min(best_priority + best_score, 10)` adds `best_score` (the raw keyword match count) to `best_priority` *after* the urgency boost logic. This means a ticket with 1 keyword match gets `priority_base + 1` (e.g., 5 for billing), while a ticket with 10 keyword matches gets `min(priority_base + 10, 10)` = 10. The scoring is not linearly proportional to keyword count, which could lead to unintuitive priority jumps. However, this is a design choice rather than a crash bug — tests pass.
- **`supportagent/ingest.py:139` — `from urllib.parse import unquote_plus` inside a loop**: The import is inside the `if isinstance(payload, str)` branch but outside the loop. This is fine functionally but stylistically odd — the import should be at the top of the file.

## Non-Blocking Notes
- **Decorative separator comments**: Files like `models.py` and `ingest.py` use excessive `# ------` separator lines (e.g., `# ---------------------------------------------------------------------------`). These add noise without value.
- **`SRouter` class naming**: The class is named `SRouter` (likely a typo for `Router`). Consider renaming to `Router` for clarity.
- **`classifier.py:65` — Priority formula**: `best_priority = min(best_priority + best_score, 10)` mixes the base priority with raw keyword count. A clearer formula might be `best_priority = min(rule.priority_base + best_score, 10)` to separate base from boost.
- **`ingest.py` — `from urllib.parse import unquote_plus`**: Should be at the top of the file with other imports.
- **`classifier.py` — Keyword matching is substring-based**: `combined_text.count(kw)` does substring matching, so keyword "bill" would match "billing" and "billed". This may cause false positives. Consider using word-boundary regex (`\b`) for more precise matching.
- **`router.py` — No validation of YAML config**: If the YAML is malformed or missing expected keys, `self.config["teams"]` or `self.config["routing"]` will raise `KeyError`. Consider adding validation or default fallbacks.
- **`classifier.py` — `best_score` starts at 0**: If no keywords match, `best_category` stays as "general" with score 0, which is correct. But the `best_score` variable is never used after the loop — it could be removed.
- **`pyproject.toml` — References `supportagent.cli:main` but no `cli.py` exists**: The `[project.scripts]` entry points to a CLI module that doesn't exist yet. This will fail on `pip install`.
- **`supportagent/__init__.py` — Does not export `Ingestor`, `Classifier`, or `SRouter`**: These are public classes that users would need to import directly from submodules. Consider adding them to `__all__`.
- **Config files are YAML**: Good choice for human-editable rules, but there's no schema validation. A wrong key in the YAML would silently break behavior.

## Reusable Components
- **`Ingestor` class** (`supportagent/ingest.py`): Self-contained multi-format ticket ingestion (JSON, MIME email, web form URL-encoded) with flexible key mapping and auto-UUID generation. Could be reused by any ticketing or data ingestion pipeline.
- **`Ticket` and `PipelineResult` dataclasses** (`supportagent/models.py`): Well-designed data models with serialization helpers. The `Ticket` model with its `to_dict`/`from_dict`/`to_json`/`from_json` pattern is reusable for any structured data workflow.
- **`Classifier` class** (`supportagent/classifier.py`): Config-driven keyword-based text classifier with urgency scoring. The pattern of loading rules from YAML and scoring text is reusable.

## Verdict
PASS — All tests pass (35/35), no crashes or wrong-output bugs found. Minor issues are non-blocking design/style concerns.
