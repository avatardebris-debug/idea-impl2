# Phase 2 Tasks

- [ ] Task 1: Unit tests for PhraseDatabase (models.py / phrases.py)
  - What: Write pytest tests covering PhraseDatabase — add_phrase, add_phrases, get_by_language, get_by_frequency_rank, get_phrases_by_rank_range, get_all_phrases, get_languages, __len__, and create_default_database. Also test Phrase dataclass construction and repr.
  - Files: Create `tests/test_models.py` and `tests/test_phrases.py` in the workspace
  - Done when: All PhraseDatabase methods are covered by at least one assertion; create_default_database returns a non-empty database with 3 languages; tests pass with `pytest tests/ -v`

- [ ] Task 2: Unit tests for LearningSession (learner.py)
  - What: Write pytest tests covering LearningSession — add_phrase, add_phrases, get_next_phrase (priority ordering), mark_known, mark_partially_known, mark_new, get_session_stats, get_phrase_mastery, get_remaining_phrases, end_session. Also test PhraseProgress mastery transitions and SessionStats.summary().
  - Files: Create `tests/test_learner.py` in the workspace
  - Done when: Every public method of LearningSession and PhraseProgress is tested; priority ordering (NEW > PARTIALLY_KNOWN > KNOWN > MASTERED) is verified; tests pass with `pytest tests/ -v`

- [ ] Task 3: Unit tests for mnemonics module (mnemonics.py)
  - What: Write pytest tests covering generate_mnemonic (returns dict with keywords, associations, visual_prompt, memory_hook keys), assign_phrase_to_palace (returns dict with palace_id, location, slot_number), _extract_keywords, and _get_keyword_association.
  - Files: Create `tests/test_mnemonics.py` in the workspace
  - Done when: Mnemonic generation produces valid keyword lists and visual prompts for multi-word phrases; palace assignment is deterministic (same phrase + palace_id yields same result); tests pass with `pytest tests/ -v`

- [ ] Task 4: Error handling improvements
  - What: Add input validation and error handling to key areas: (a) CLI — validate language argument against available languages before creating session, handle empty phrase lists gracefully; (b) LearningSession — raise ValueError on invalid mastery transitions (e.g., marking unknown phrase as known); (c) PhraseDatabase — guard against duplicate phrases with same text/language; (d) mnemonics — handle empty or whitespace-only phrases.
  - Files: Modify `babble/cli.py`, `babble/learner.py`, `babble/models.py`, `babble/mnemonics.py`
  - Done when: Invalid language in CLI prints helpful message and exits with code 1; LearningSession raises ValueError for invalid operations; empty phrase lists handled without crashes; tests added for error paths in `tests/test_error_handling.py`

- [ ] Task 5: Integration / smoke test
  - What: Write a smoke test that exercises the full workflow end-to-end: create a PhraseDatabase, load default phrases, create a LearningSession with a subset of phrases, run a simulated learning loop (get_next_phrase, mark_known, mark_partially_known), and verify session stats are accurate.
  - Files: Create `tests/test_integration.py` in the workspace
  - Done when: Full workflow runs without errors; session stats match expected values (e.g., after marking 3 phrases known, phrases_known == 3); tests pass with `pytest tests/ -v`

- [ ] Task 6: README.md and project documentation
  - What: Write a comprehensive README.md at the workspace root covering: project overview, installation (pip install / from source), quick start example, CLI usage with flags, API usage example, architecture overview (modules), and contributing notes.
  - Files: Create `README.md` in the workspace root
  - Done when: README includes installation instructions, CLI usage examples with output, API code snippet, module descriptions, and project structure; all tests pass (`pytest tests/ -v` returns 0)