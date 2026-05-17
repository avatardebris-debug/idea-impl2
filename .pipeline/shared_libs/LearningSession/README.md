# LearningSession

## Description
A mastery-tracking learning session engine with spaced repetition timing, priority-based study queue, and session statistics. Suitable for flashcard, quiz, or spaced-repetition applications.

## Files
- `LearningSession.py` — The `LearningSession` class, `MasteryLevel` enum, `PhraseProgress` dataclass, `SessionStats` dataclass

## Usage
```python
from LearningSession import LearningSession, MasteryLevel

session = LearningSession()
session.add_phrase(phrase)
next_p = session.get_next_phrase()
session.mark_known(next_p.text)
stats = session.end_session()
print(stats.summary())
```

## Dependencies
- Python 3.8+ (dataclasses, datetime, enum)
