# Phase 1 Review — babble

## What's Good
- Package structure is clean and well-organized: `__init__.py`, `core.py`, `models.py`, `phrases.py`, `learner.py`, `mnemonics.py`, `cli.py`, and `data/` subpackage all present and correctly wired.
- All six tasks from the spec are implemented: data model, phrase database, learning session engine, memory palace/mnemonics, default dataset (100 phrases across 3 languages), and CLI entry point.
- `import babble` works without errors; all public APIs (`Phrase`, `PhraseDatabase`, `LearningSession`, `generate_mnemonic`, `assign_phrase_to_palace`) are importable at the top level.
- `Phrase` dataclass has all required fields: `text`, `language`, `frequency_rank`, `translation`, `context`.
- `PhraseDatabase` supports indexing by language and frequency rank, with `add_phrase`, `add_phrases`, `get_by_language`, `get_by_frequency_rank`, `get_phrases_by_rank_range`, and `get_all_phrases`.
- `LearningSession` implements the core learning loop with priority-based ordering (NEW > PARTIALLY_KNOWN > KNOWN > MASTERED), spaced repetition timing, and session statistics.
- `MasteryLevel` enum and `PhraseProgress` dataclass provide clean state tracking per phrase.
- `SessionStats` provides a human-readable summary with counts, streaks, and timestamps.
- `generate_mnemonic` returns a structured dict with keywords, associations, visual prompt, and memory hook.
- `assign_phrase_to_palace` uses deterministic MD5 hashing for reproducible slot assignment across 22 locations.
- Default dataset has 100 phrases across English (33), Spanish (33), and French (34) with frequency ranks 1–100.
- CLI (`python -m babble`) works with argparse, supports `-l/--language` and `-n/--num-phrases` flags, interactive loop, and session summary.
- `setup.py` correctly uses `find_packages()` and defines a `console_scripts` entry point.
- `core.py` provides a `create_session` convenience function.
- `phrases.py` provides utility functions: `create_default_database`, `load_phrases_from_list`, `filter_phrases`, `get_top_phrases`.

## Blocking Bugs
None

## Non-Blocking Notes
- `mnemonics.py`: `_KEYWORD_MAP` has duplicate keys (e.g., `"say"`, `"that"`, `"good"`, `"bad"`, `"old"`, `"must"`, `"should"`, `"can"`, `"will"`, `"shall"`, `"may"`, `"might"`, `"would"`, `"could"`, `"done"`, `"please"`, `"god"`, `"yes"`, `"no"`, `"good"`, `"bad"` appear twice). Python silently keeps the last value, so this is not a crash but may produce unexpected associations. Consider deduplicating or using a list of tuples.
- `mnemonics.py`: `slot_number` can be extremely large (e.g., `863417867526320268160036341943930595`) because it divides a 128-bit MD5 hash by the number of locations. Consider using `hash_val % (len(locations) * 100)` or similar to keep slot numbers in a reasonable range.
- `learner.py`: `get_next_phrase` sorts the entire `_study_queue` on every call, which is O(n log n) per call. For large sessions this could be slow. Consider using a heap or lazy re-sorting.
- `learner.py`: `mark_new` does not increment `total_reviews` unlike `mark_known` and `mark_partially_known`. This is a minor inconsistency in stats tracking.
- `learner.py`: The `MasteryLevel.MASTERED` state is defined but never set by any method — only `KNOWN`, `PARTIALLY_KNOWN`, and `NEW` are reachable. Consider adding a `mark_mastered` method or auto-promoting from `KNOWN` after a streak threshold.
- `learner.py`: `_calculate_next_review` always returns a future datetime based on `datetime.now()`, but the session never actually checks `next_review` to decide what to present next. The priority ordering is purely based on mastery level, not time-based scheduling.
- `cli.py`: The session summary uses `===` (three equals) instead of `===` (consistent with the `SessionStats.summary` format which also uses `===`). Minor cosmetic inconsistency.
- `default_phrases.py`: English phrases use `frequency_rank` 1–33, Spanish 34–66, French 67–100. These are global ranks, not per-language ranks. This is fine per spec but worth noting — the frequency ranking is across all languages combined.
- `mnemonics.py`: The `_KEYWORD_MAP` is hardcoded for English words only, which limits its usefulness for non-English phrases. Consider making it language-aware or generating associations dynamically.

## Reusable Components
- **PhraseDatabase** (`babble/phrases.py` + `babble/models.py`): A generic phrase/language data store with indexing by language and frequency rank. Could be reused for any language-learning or phrase-management project.
- **LearningSession** (`babble/learner.py`): A mastery-tracking learning session engine with spaced repetition timing, priority-based study queue, and session statistics. Could be reused for any quiz/flashcard/spaced-repetition application.
- **Mnemonic helpers** (`babble/mnemonics.py`): Keyword association and memory palace slot assignment using deterministic hashing. Could be reused for any mnemonic or memory-augmentation tool.
- **SessionStats** (`babble/learner.py`): A self-contained statistics dataclass with summary formatting. Could be reused for any session-tracking application.

## Verdict
PASS — All six Phase 1 tasks are implemented, the package is importable, all core features work correctly, and no blocking bugs were found.
