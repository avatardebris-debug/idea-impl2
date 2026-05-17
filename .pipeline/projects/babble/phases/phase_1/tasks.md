# Phase 1 Tasks

- [ ] Task 1: Create project structure and package skeleton
  - What: Set up the babble Python package with __init__.py, core module layout, and basic package metadata
  - Files: Create babble/__init__.py, babble/core.py, babble/phrases.py, babble/learner.py, babble/models.py, setup.py
  - Done when: Package is importable as `import babble` and `from babble.core import *` without errors

- [ ] Task 2: Implement phrase data model and phrase database
  - What: Build the Phrase data class and a PhraseDatabase class that stores common phrases across multiple languages with usage-frequency metadata
  - Files: babble/models.py, babble/phrases.py
  - Done when: Can create Phrase objects with fields (text, language, frequency_rank, translation, context), instantiate a PhraseDatabase, add phrases, and query by language or frequency rank

- [ ] Task 3: Implement the learning session engine
  - What: Build the core learning loop that presents phrases to the user in order of usage value, tracks progress, and implements spaced repetition basics
  - Files: babble/learner.py
  - Done when: Can create a LearningSession, add phrases to it, get the next phrase to study, mark a phrase as known/partially known, and get session statistics

- [ ] Task 4: Implement memory palace / acceleration techniques
  - What: Add mnemonic generation helpers — keyword association, visual encoding prompts, and memory palace slot assignment for each phrase
  - Files: babble/mnemonics.py
  - Done when: Can call generate_mnemonic(phrase) to get a keyword-based memory aid, and assign_phrase_to_palace(phrase, palace_id) to get a memory palace slot suggestion

- [ ] Task 5: Implement the default phrase dataset
  - What: Create a built-in dataset of the 100 most common phrases across at least 3 languages (e.g., English, Spanish, French) with frequency rankings and translations
  - Files: babble/data/default_phrases.py
  - Done when: Can import DEFAULT_PHRASES and get a list of Phrase objects for at least 3 languages, each with text, language, frequency_rank, translation, and context fields

- [ ] Task 6: Wire up the CLI entry point
  - What: Add a command-line interface so users can start a learning session from the terminal
  - Files: babble/cli.py (with if __name__ == "__main__" block)
  - Done when: Running `python -m babble` starts a learning session using the default dataset, presents phrases one at a time, accepts user input for self-assessment, and prints session summary