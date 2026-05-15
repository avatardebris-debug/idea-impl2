# Phase 3 Tasks

- [x] Task 1: Tree Visualization and Exclude Flags
  - What: Implement visual dependency trees and pattern exclusions.
  - Files:
    - `depvuln/cli.py` — Add `tree` command and `--exclude` options
    - `depvuln/tree_builder.py` — Logic to build and format hierarchical trees
    - `depvuln/reports/tree_report.py` — ASCII and DOT renderers

- [x] Task 2: Configuration Manager & Watch Mode
  - What: Implement `.depvulnrc` loading and continuous file watching.
  - Files:
    - `depvuln/config.py` — Enhance to support `.depvulnrc` YAML parsing
    - `depvuln/watcher.py` — File system polling/watchdog implementation
    - `depvuln/cli.py` — Add `watch` and `config init` commands

- [x] Task 3: Plugin System Architecture
  - What: Allow third-party parsers and CVE sources via dynamic loading.
  - Files:
    - `depvuln/plugins/loader.py` — `pkg_resources` or `importlib.metadata` entry point discovery
    - `depvuln/plugins/base.py` — Abstract plugin interfaces

- [x] Task 4: Parallel CVE Lookups & Export DB
  - What: Optimize fetchers with threading/asyncio and add DB export.
  - Files:
    - `depvuln/cve/fetcher.py` — Refactor to use `ThreadPoolExecutor` or `asyncio.gather`
    - `depvuln/cli.py` — Add `export-db` command

- [x] Task 5: CI/CD Packaging (GitHub Actions & Docker)
  - What: Wrap the CLI into a Docker container and a standard GitHub action.
  - Files:
    - `Dockerfile` — Optimized CLI runner image
    - `action.yml` — GitHub action definition mapping inputs to CLI flags
    - `ci_templates/gitlab-ci.yml` — Example GitLab snippet
