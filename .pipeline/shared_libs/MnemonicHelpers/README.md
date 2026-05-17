# MnemonicHelpers

## Description
Keyword association and memory palace slot assignment using deterministic hashing. Generates visual encoding prompts and memory hooks for mnemonic learning.

## Files
- `MnemonicHelpers.py` — `generate_mnemonic()` and `assign_phrase_to_palace()` functions

## Usage
```python
from MnemonicHelpers import generate_mnemonic, assign_phrase_to_palace

mnem = generate_mnemonic(phrase)
# Returns: {keywords, associations, visual_prompt, memory_hook, ...}

palace = assign_phrase_to_palace(phrase, palace_id=1)
# Returns: {palace_id, location, slot_number, phrase_text, phrase_language}
```

## Dependencies
- Python 3.8+ (hashlib)
