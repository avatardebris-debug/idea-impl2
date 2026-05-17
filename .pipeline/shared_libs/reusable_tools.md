# Reusable Tools

## PhraseDatabase
- **Location**: `.pipeline/shared_libs/PhraseDatabase/`
- **Description**: Generic phrase/language data store with indexing by language and frequency rank.
- **Source**: `babble/models.py` (Phrase, PhraseDatabase)
- **Use case**: Any language-learning or phrase-management project.

## LearningSession
- **Location**: `.pipeline/shared_libs/LearningSession/`
- **Description**: Mastery-tracking learning session engine with spaced repetition timing, priority-based study queue, and session statistics.
- **Source**: `babble/learner.py` (LearningSession, MasteryLevel, PhraseProgress, SessionStats)
- **Use case**: Any flashcard, quiz, or spaced-repetition application.

## MnemonicHelpers
- **Location**: `.pipeline/shared_libs/MnemonicHelpers/`
- **Description**: Keyword association and memory palace slot assignment using deterministic hashing.
- **Source**: `babble/mnemonics.py` (generate_mnemonic, assign_phrase_to_palace)
- **Use case**: Any mnemonic or memory-augmentation tool.

## SessionStats
- **Location**: `.pipeline/shared_libs/SessionStats/`
- **Description**: Self-contained statistics dataclass with summary formatting for learning session metrics.
- **Source**: `babble/learner.py` (SessionStats)
- **Use case**: Any session-tracking application.
