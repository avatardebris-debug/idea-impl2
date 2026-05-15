# Phase 3 Specification: Integration, API, and Documentation

## 1. Overview
The final phase of the Logistics CSV Optimizer project transitions the basic prototype into a robust, installable tool with both CLI and programmatic API interfaces, complete with thorough documentation and Docker support.

## 2. Core Features

### 2.1 API Surface (Programmatic Interface)
- Refactor the core pipeline logic out of `cli.py` into an `api.py` module so developers can easily import and run the optimization engine in Python code without invoking `subprocess`.
- The API should accept either file paths or raw Python dictionaries and return a structured result object.

### 2.2 Docker Containerization
- Add a `Dockerfile` that packages the application.
- The Docker image should be capable of accepting mounted volumes for input CSVs and output JSONs.

### 2.3 Advanced CLI Capabilities
- Add support for piping: allow reading from `stdin` if `-i -` is provided, and writing to `stdout` if `-o -` is provided. This allows chaining the tool with other bash utilities.

### 2.4 Deployment Documentation
- Expand `README.md` to include API usage examples, Docker execution instructions, and CI/CD integration snippets.

## 3. Success Criteria
- [ ] `api.py` exposes a clean `run_optimization(input_data)` function.
- [ ] CLI correctly supports standard I/O via `-`.
- [ ] Dockerfile builds successfully and the image runs the CLI.
- [ ] `README.md` covers all usage modalities (CLI, API, Docker).