# SessionStats

## Description
A self-contained statistics dataclass with summary formatting for tracking learning session metrics: total phrases, known/partially known/new/mastered counts, streaks, and timestamps.

## Files
- `SessionStats.py` — The `SessionStats` dataclass with `summary()` method

## Usage
```python
from SessionStats import SessionStats

stats = SessionStats(total_phrases=10, phrases_known=5, phrases_new=5)
print(stats.summary())
```

## Dependencies
- Python 3.8+ (dataclasses, datetime)
