# PhraseDatabase

## Description
A generic phrase/language data store with indexing by language and frequency rank. Supports adding phrases, querying by language, frequency rank, and rank ranges.

## Files
- `PhraseDatabase.py` — The `PhraseDatabase` class
- `Phrase.py` — The `Phrase` dataclass

## Usage
```python
from PhraseDatabase import Phrase, PhraseDatabase

db = PhraseDatabase()
db.add_phrase(Phrase(text="Hola", language="Spanish", frequency_rank=34))
phrases = db.get_by_language("Spanish")
top = db.get_phrases_by_rank_range(1, 10)
```

## Dependencies
- Python 3.8+ (dataclasses)
