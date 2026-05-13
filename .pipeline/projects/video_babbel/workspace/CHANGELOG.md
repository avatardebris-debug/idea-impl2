# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full CLI with Click-based interface (`video-babbel` command)
- `process` sub-command for end-to-end video processing
- `list-languages` sub-command to show supported languages
- `validate` sub-command for pipeline health checks
- `--output-json` flag for JSON output
- `--output-file` flag for file output
- `--verbose` flag for DEBUG-level logging
- Docker support with multi-stage Dockerfile
- Docker Compose configuration
- Comprehensive test suite (unit + integration + CLI tests)
- `MANIFEST.in` for proper package distribution
- MIT License
- CHANGELOG.md

### Changed
- Refactored pipeline into modular components (Ingestor, Transcriber, Translator, Summarizer, QAEngine)
- Improved error handling with custom exception hierarchy
- Enhanced logging with structured output
- Updated dependencies to latest compatible versions

### Fixed
- Fixed transcript segment serialization
- Fixed QA engine handling of empty transcripts
- Fixed CLI argument validation

## [0.1.0] - 2024-01-01

### Added
- Initial release of VideoBabbel
- Video ingestion via ffmpeg
- Speech transcription via Whisper
- Translation via googletrans / DeepL
- Text summarization
- Q&A engine
- Basic Python API
