# Phase 3 Specification: Production Hardening, CI/CD & Advanced Features

## 1. Overview
In Phase 3, we transition `depvuln` from a robust local CLI to a production-ready, extensible enterprise tool. We will add native CI/CD integrations, a plugin architecture for custom parsers/sources, visual dependency tree rendering, and continuous monitoring modes.

## 2. Core Features

### 2.1 Dependency Tree Visualization
- Implement a `TreeReporter` that outputs the dependency hierarchy visually in the terminal (ASCII art) and supports Graphviz DOT export.
- Command: `depvuln tree <path>`

### 2.2 Continuous Monitoring (`--watch` mode)
- Use file system watchers (e.g., `watchdog`) to monitor `package-lock.json`, `requirements.txt`, etc., and automatically trigger incremental scans when they change.

### 2.3 Configuration Management
- Introduce `.depvulnrc` YAML configuration to store project-level defaults (e.g., default threshold, disabled ecosystems, custom plugin paths).
- Command: `depvuln config init`

### 2.4 Plugin Architecture
- Add `PluginLoader` leveraging Python `entry_points` or dynamic module loading.
- Expose base classes: `CveSourcePlugin`, `ParserPlugin`, `ReportTemplatePlugin`.

### 2.5 Historical Export
- Add `depvuln export-db <path> <output.db>` to dump local SQLite vulnerability caches and scan history for long-term trend analysis.

### 2.6 Exclusions
- Add `--exclude <pattern>` to ignore known false-positives or specific subdirectories.

## 3. CI/CD Integrations
- Develop a GitHub Action (`action.yml`) packaged with a pre-built Docker image of `depvuln`.
- Develop a GitLab CI template (`.gitlab-ci.yml` snippet).
- Ensure the tool correctly returns non-zero exit codes when vulnerabilities exceeding the `--threshold` are found, enforcing pipeline gates.

## 4. Performance & Security
- Implement parallel fetching for CVE lookups using `asyncio` or `ThreadPoolExecutor`.
- Perform a security audit to ensure no secrets (like NPM tokens in `.npmrc`) are ever leaked into reports.
