# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-19

### Added
- - pipeline stall detector + get_processing_messages diagnostics
- - light-tier model routing via PIPELINE_LIGHT_MODEL env var
- - GPU-low veto on scale-down, executor continuity, fine-tune collector
- - EMA-3/10 crossover signal + GPU headroom veto in auto-tuner

### Fixed
- - prevent infinite silent loops on agent failures with retry limit, manager escalation, and light-model fallback
- - resolve session-agnostic throughput and enhance calibration UX
- - Fix Unicode decoding exceptions in agent state loading and clean corrupted state JSONs
- - Optimize pipeline startup (cache warming & model warmup) and fix parallelizer calibration lock
- - resolve stall detector undefined variable, retry_count payload tracking, SFT phase contamination, and enable metrics file trimming
- - UnboundLocalError in pre-seeding block

### Removed
- - Optimize pipeline startup (cache warming & model warmup) and fix parallelizer calibration lock


## [0.0.1] - 2026-05-19

### Added
- - parallel multi-project pipeline + executor scaling
- - show live tok/s in status line (last-call + session avg from throughput.json)
- - add TYPE_CHECKING guard for AgentResult annotation (no runtime cost)
- - add missing threading import; add corpus collector hook; VRAM-aware cloud setup
- - complete Ollama KV-cache (prefix reuse)
- - dynamic parallelizer + PufferLib strategy wiring
- - complete test_fixture_generator rebuild and pipeline observability dashboard

### Changed
- - complete test_fixture_generator rebuild and pipeline observability dashboard

### Fixed
- - dual-signal downscale guard â€” only scale down if both pipeline_tps AND inference_tps drop (prevents false downscale on overhead noise)
- - budget enforcement uses only session_started_at, stamps now if missing (prevents re-budget on manual reset)
- - add TYPE_CHECKING guard for AgentResult annotation (no runtime cost)
- - rewrite _recover_processing_messages for SQLite MessageBus
- - add missing threading import; add corpus collector hook; VRAM-aware cloud setup
- - complete Ollama KV-cache (prefix reuse)
- - complete test_fixture_generator rebuild and pipeline observability dashboard

