# Phase 3 Specification: Packaging & Distribution

## 1. Overview
In Phase 3, we finalize the Invoice Processor by making it a fully distributable and containerized package. While the core API and CLI surface are fully functional, they need standard Python packaging configuration and a Dockerfile for reproducible deployments.

## 2. Core Features

### 2.1 Package Configuration
- **pyproject.toml**: Standard build system definition using `setuptools`. Defines the `invoice-processor` executable and dependencies.

### 2.2 Containerization
- **Dockerfile**: Minimal Dockerfile to containerize the application, allowing users to mount directories and run the invoice parser without installing system dependencies for PyMuPDF.

## 3. Success Criteria
- [ ] `pyproject.toml` is created with proper metadata.
- [ ] `Dockerfile` is built to run the CLI by default.
- [ ] Tool can be installed via `pip install .`
