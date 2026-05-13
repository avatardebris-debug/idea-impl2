# Phase 3 Tasks

- [ ] Task 1: Git helper utilities
  - What: Build a `GitHelper` class that wraps git operations — reading commit history, extracting diffs, parsing commit messages, and categorizing changes (Added/Changed/Fixed/Removed/Deprecated).
  - Files: Create `docsai/utils/git_helper.py` (GitHelper class with methods: `get_commit_history`, `get_commit_diff`, `parse_commit_message`, `categorize_changes`), update `docsai/utils/__init__.py` to export it
  - Done when: `GitHelper` can read the last N commits from a git repo, extract file changes and commit messages, and categorize them correctly; unit tests verify parsing of various commit message formats (conventional commits, regular messages); handles repos without git history gracefully.

- [ ] Task 2: Changelog template engine integration
  - What: Create a default changelog template following Keep a Changelog conventions, and integrate it with the existing template engine from Phase 2.
  - Files: Create `docsai/templates/changelog_default.md` (Jinja2 template with sections for each version/date), update `docsai/generators/readme_templates.py` to support changelog templates, update `docsai/core/config.py` to add `changelog_template_dir` and `changelog_template_file` config keys
  - Done when: Template renders versioned changelog entries with proper formatting (date, version, categories); supports custom changelog templates via config; template engine can load and render changelog templates alongside README templates.

- [ ] Task 3: Changelog generator (LLM-powered)
  - What: Build a `ChangelogGenerator` class that takes git history data, uses the LLM to summarize changes into categorized entries, and produces a versioned changelog.
  - Files: Create `docsai/generators/changelog.py` (ChangelogGenerator class with methods: `generate_version_entry`, `categorize_commits`, `generate_summary`), update `docsai/generators/__init__.py` to export it
  - Done when: `ChangelogGenerator` accepts git history data and produces categorized changelog entries (Added/Changed/Fixed/Removed/Deprecated); uses LLM to generate human-readable summaries of commit diffs; supports semver version bumping; unit test with mock git history verifies output format and categorization accuracy.

- [ ] Task 4: CLI `docsai changelog` subcommand
  - What: Add the `changelog` subcommand to the Typer CLI that wires together git history reading, changelog generation, template rendering, and output writing.
  - Files: Create `docsai/cli/changelog.py` (changelog_app Typer app with `changelog` command), update `docsai/cli/__init__.py` to register the `changelog` subcommand
  - Done when: Running `docsai changelog ./my_project` reads git history, generates categorized changelog entries, renders the template, and writes `CHANGELOG.md` to the configured output path; CLI accepts `--output <path>`, `--template <path>`, `--bump <major|minor|patch>`, `--config <path>`, and `--since <tag>` flags; `docsai --help` shows the new `changelog` subcommand; running on a sample project with git history produces a properly formatted CHANGELOG.md.

- [ ] Task 5: End-to-end test for changelog generation
  - What: Create an end-to-end test that runs `docsai changelog` against a sample project with realistic git history and validates the output CHANGELOG.md.
  - Files: Create `tests/test_changelog_e2e.py`
  - Done when: `test_changelog_e2e.py` runs `docsai changelog` on a sample project with git history, loads the output CHANGELOG.md, and asserts: (1) file exists and is non-empty, (2) contains versioned entries with dates, (3) contains categorized sections (Added/Changed/Fixed/Removed/Deprecated), (4) entries are coherent and accurately reflect the git history, (5) semver bumping works correctly when `--bump` flag is used; test passes with `pytest`.