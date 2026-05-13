# Phase 1 Tasks

- [x] Task 1: Create package structure
  - What: Set up the `movie_idea_generator` Python package with `__init__.py` and submodules for clean imports
  - Files: `workspace/movie_idea_generator/__init__.py`, `workspace/movie_idea_generator/generator.py`, `workspace/movie_idea_generator/cli.py`
  - Done when: `import movie_idea_generator` works from the workspace directory without errors

- [x] Task 2: Implement core idea generation engine
  - What: Build the `MovieIdeaGenerator` class with methods to generate movie ideas (title, genre, logline, characters). Use a rule-based approach with templates and randomization for the MVP (no LLM dependency required for core functionality)
  - Files: `workspace/movie_idea_generator/generator.py`
  - Done when: `MovieIdeaGenerator().generate()` returns a dict with keys: title, genre, logline, characters (list of dicts with name/description)

- [x] Task 3: Create CLI entry point
  - What: Build a simple CLI using `argparse` that allows users to generate movie ideas from the command line. Support flags for genre, number of ideas, and output format
  - Files: `workspace/movie_idea_generator/cli.py`
  - Done when: `python -m movie_idea_generator` prints a generated movie idea to stdout

- [x] Task 4: Verify importability and basic functionality
  - What: Write a quick smoke test that imports the package, generates an idea, and validates the output structure
  - Files: `workspace/test_movie_idea_generator.py`
  - Done when: `python test_movie_idea_generator.py` passes with no errors