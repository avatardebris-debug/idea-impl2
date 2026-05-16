# Fix Report — Phase 3

## Current Issues
# Validation Report — Phase 3
## Summary
- Tests: 95 passed, 25 failed
## Verdict: FAIL

### Failure Details

**25 tests failed across 2 test files:**

1. **tests/test_cli.py** — 7 failures (all `assert 1 == 0`):
   - `test_keywords_basic`
   - `test_keywords_top_option`
   - `test_keywords_output_file`
   - `test_keywords_vtt_file`
   - `test_keywords_txt_file`
   - `test_keywords_empty_file`
   - `test_keywords_json_structure`
   - Root cause: CLI commands are returning non-zero exit codes, indicating runtime errors in the CLI implementation.

2. **tests/test_extractor.py** — 18 failures (all `OSError: [E050] Can't find model 'en_core_web_sm'`):
   - `test_extract_returns_list`
   - `test_extract_returns_dicts`
   - `test_extract_has_required_keys`
   - `test_extract_respects_top_n`
   - `test_extract_sorted_by_score`
   - `test_extract_no_duplicates`
   - `test_extract_categories_assigned`
   - `test_extract_empty_text`
   - `test_extract_single_word`
   - `test_extract_scores_are_floats`
   - `test_extract_occurrences_are_ints`
   - `test_extract_rounded_scores`
   - `test_stop_words_excluded`
   - `test_technical_keywords`
   - `test_health_keywords`
   - `test_business_keywords`
   - `test_general_keywords`
   - `test_large_file_performance`
   - Root cause: The spaCy NLP model `en_core_web_sm` is not installed in the environment.

### Root Causes
- **Missing dependency**: The spaCy English model (`en_core_web_sm`) is not installed. This can be fixed with `python -m spacy download en_core_web_sm`.
- **CLI exit code issues**: The CLI module appears to have bugs causing non-zero exit codes on valid inputs.

### Recommendation
Fix the missing spaCy model and CLI exit code issues, then re-run tests. The dashboard models tests (20 tests) all pass, indicating the dashboard model layer is solid.


## Attempt History

### Attempt 1
- **Failures**: 0 (↓ improving)
- **Previous failures**: 1

#### Test Output
```
# Validation Report — Phase 3
## Summary
- Tests: 95 passed, 25 failed
## Verdict: FAIL

### Failure Details

**25 tests failed across 2 test files:**

1. **tests/test_cli.py** — 7 failures (all `assert 1 == 0`):
   - `test_keywords_basic`
   - `test_keywords_top_option`
   - `test_keywords_output_file`
   - `test_keywords_vtt_file`
   - `test_keywords_txt_file`
   - `test_keywords_empty_file`
   - `test_keywords_json_structure`
   - Root cause: CLI commands are returning non-zero exit codes, indicating runtime errors in the CLI implementation.

2. **tests/test_extractor.py** — 18 failures (all `OSError: [E050] Can't find model 'en_core_web_sm'`):
   - `test_extract_returns_list`
   - `test_extract_returns_dicts`
   - `test_extract_has_required_keys`
   - `test_extract_respects_top_n`
   - `test_extract_sorted_by_score`
   - `test_extract_no_duplicates`
   - `test_extract_categories_assigned`
   - `test_extract_empty_text`
   - `test_extract_single_word`
   - `test_extract_scores_are_floats`
   - `test_extract_occurrences_are_ints`
   - `test_extract_rounded_scores`
   - `test_stop_words_excluded`
   - `test_technical_keywords`
   - `test_health_keywords`
   - `test_business_keywords`
   - `test_general_keywords`
   - `test_large_file_performance`
   - Root cause: The spaCy NLP model `en_core_web_sm` is not installed in the environment.

### Root Causes
- **Missing dependency**: The spaCy English model (`en_core_web_sm`) is not installed. This can be fixed with `python -m spacy download en_core_web_sm`.
- **CLI exit code issues**: The CLI module appears to have bugs causing non-zero exit codes on valid inputs.

### Recommendation
Fix the missing spaCy model and CLI exit code issues, then re-run tests. The dashboard models tests (20 tests) all pass, indicating the dashboard model layer is solid.

```


### Attempt 2
- **Failures**: 0 (→ stalled)
- **Previous failures**: 0

#### Test Output
```
# Validation Report — Phase 3
## Summary
- Tests: 95 passed, 25 failed
## Verdict: FAIL

### Failure Details

**25 tests failed across 2 test files:**

1. **tests/test_cli.py** — 7 failures (all `assert 1 == 0`):
   - `test_keywords_basic`
   - `test_keywords_top_option`
   - `test_keywords_output_file`
   - `test_keywords_vtt_file`
   - `test_keywords_txt_file`
   - `test_keywords_empty_file`
   - `test_keywords_json_structure`
   - Root cause: CLI commands are returning non-zero exit codes, indicating runtime errors in the CLI implementation.

2. **tests/test_extractor.py** — 18 failures (all `OSError: [E050] Can't find model 'en_core_web_sm'`):
   - `test_extract_returns_list`
   - `test_extract_returns_dicts`
   - `test_extract_has_required_keys`
   - `test_extract_respects_top_n`
   - `test_extract_sorted_by_score`
   - `test_extract_no_duplicates`
   - `test_extract_categories_assigned`
   - `test_extract_empty_text`
   - `test_extract_single_word`
   - `test_extract_scores_are_floats`
   - `test_extract_occurrences_are_ints`
   - `test_extract_rounded_scores`
   - `test_stop_words_excluded`
   - `test_technical_keywords`
   - `test_health_keywords`
   - `test_business_keywords`
   - `test_general_keywords`
   - `test_large_file_performance`
   - Root cause: The spaCy NLP model `en_core_web_sm` is not installed in the environment.

### Root Causes
- **Missing dependency**: The spaCy English model (`en_core_web_sm`) is not installed. This can be fixed with `python -m spacy download en_core_web_sm`.
- **CLI exit code issues**: The CLI module appears to have bugs causing non-zero exit codes on valid inputs.

### Recommendation
Fix the missing spaCy model and CLI exit code issues, then re-run tests. The dashboard models tests (20 tests) all pass, indicating the dashboard model layer is solid.

```


### Attempt 3
- **Failures**: 3 (→ stalled)
- **Previous failures**: 0

#### Test Output
```
# Validation Report — Phase 3
## Summary
- Tests: 174 passed, 6 failed
## Verdict: FAIL

## Details

### Test Results
- **174 tests passed**, **6 tests failed**
- All failures are in `tests/test_show_notes.py`

### Failed Tests
1. `TestShowNotesGenerate::test_generate_with_both_empty` — TypeError: `isinstance()` arg 2 must be a type (test bug: `isinstance(result, result)`)
2. `TestShowNotesGenerateTakeaways::test_takeaways_respects_max_count` — TypeError: 'FixtureFunctionDefinition' object is not iterable (fixture misuse in test)
3. `TestShowNotesGenerateTakeaways::test_takeaways_with_empty_transcript` — AssertionError: expected 'No key takeaways available' not found in output
4. `TestShowNotesGenerateTimestamps::test_timestamps_respects_max_count` — TypeError: expected string or bytes-like object, got 'FixtureFunctionDefinition'
5. `TestShowNotesGenerateRelatedTopics::test_related_topics_with_empty_transcript` — AssertionError: expected 'No related topics available' not found in output
6. `TestShowNotesIntegration::test_full_pipeline_html` — AssertionError: expected `<h1>` in rendered HTML output

### Core Files Present
- `podcastseo/show_notes_generator.py`
- `podcastseo/cli.py`
- `podcastseo/keyword_extractor.py`
- `podcastseo/transcript_parser.py`
- `src/dashboard/models.py`
- `src/dashboard/panels.py`
- `src/dashboard/tickers.py`
- `src/dashboard/visualization.py`
- `src/ticker.py`
- `llm_interface.py`
- `health_check.py`
- `quality_scorer.py`
- `tools.py`
- `sweep_all.py`
- `conftest.py`
- `tests/test_show_notes.py`
- `tests/test_cli.py`
- `tests/test_dashboard_models.py`
- `tests/test_dashboard_panels.py`
- `tests/test_dashboard_tickers.py`
- `tests/test_dashboard_visualization.py`
- `tests/test_extractor.py`
- `tests/test_parser.py`
- `tests/test_ticker.py`

### Root Cause
The 6 failures stem from bugs in `tests/test_show_notes.py` (test code issues like incorrect `isinstance` usage and fixture misuse) and corresponding issues in `podcastseo/show_notes_generator.py` (production code not handling edge cases properly).

```

