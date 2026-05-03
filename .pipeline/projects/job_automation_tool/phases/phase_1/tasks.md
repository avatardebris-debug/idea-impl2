# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package skeleton with pyproject.toml, package directory, and entry point configuration
  - Files: pyproject.toml, job_automation_tool/__init__.py, job_automation_tool/cli.py
  - Done when: pyproject.toml declares the package with a CLI entry point, __init__.py exports public symbols, cli.py has a working argparse setup with --version and --help

- [ ] Task 2: Job profile data model
  - What: Build the core data model for a job profile — title, company, description, required skills, experience level, salary range, location, and metadata (source URL, parsed date, score)
  - Files: job_automation_tool/profile.py
  - Done when: Profile class has typed fields with defaults, a from_dict() classmethod, a to_dict() instance method, and a validate() method that raises ValueError on missing required fields (title, company, description)

- [ ] Task 3: Job description parser
  - What: Build a parser that takes raw job description text and extracts structured fields: title, company, skills (as a list), experience level, salary range, location, and key responsibilities
  - Files: job_automation_tool/parser.py
  - Done when: parse_job_description(text) returns a dict with keys: title, company, skills (list[str]), experience_level (str or None), salary_min (int or None), salary_max (int or None), location (str or None), responsibilities (list[str]); handles empty input gracefully returning None; regex-based extraction for skills (capitalized words after "skills", "requirements", "must have"), salary ranges (patterns like "$50k-$80k", "$60,000"), experience level (patterns like "3+ years", "entry-level", "senior"), location (patterns like "Remote", "New York, NY")

- [ ] Task 4: Profile matcher
  - What: Build a matcher that scores how well a candidate profile matches a job profile — computes a match score (0-100) based on skill overlap, experience level compatibility, and salary alignment
  - Files: job_automation_tool/matcher.py
  - Done when: match_profiles(candidate_skills, candidate_experience, job_profile) returns a dict with score (int 0-100), matched_skills (list[str]), missing_skills (list[str]), salary_match (bool); skill overlap uses Jaccard similarity scaled to 0-60 points, experience level compatibility adds 0-25 points, salary alignment adds 0-15 points; total caps at 100

- [ ] Task 5: CLI interface for parsing and matching
  - What: Build the CLI that accepts a job description file or stdin, parses it, and optionally matches against a candidate profile file
  - Files: job_automation_tool/cli.py (extend from Task 1)
  - Done when: CLI supports subcommands: `parse` (reads a file, prints parsed JSON to stdout), `match` (reads job file + candidate skills file, prints match score and breakdown); --output flag supports json or text format; returns exit code 0 on success, 1 on error

- [ ] Task 6: Unit tests for Phase 1
  - What: Write comprehensive unit tests for all modules — profile, parser, matcher, and CLI
  - Files: tests/test_profile.py, tests/test_parser.py, tests/test_matcher.py, tests/test_cli.py, tests/fixtures/sample_job.txt
  - Done when: All tests pass with pytest; profile tests cover from_dict, to_dict, validate (valid and invalid); parser tests cover realistic job descriptions, edge cases (empty, no salary, no location); matcher tests cover full overlap, partial overlap, no overlap, salary mismatch; CLI tests use subprocess to verify parse and match subcommands with sample fixtures