# Phase 3 Specification: Polish & Advanced Features

## 1. Overview
In Phase 3, Video Scribe matures from a basic extraction pipeline into a production-ready, feature-rich tool. This phase introduces robust caching, advanced media analysis (audio and optical flow for camera movement), local model support, and diverse export formats.

## 2. Core Features

### 2.1 Caching & Resuming
- **Goal:** Never re-run costly VLM inferences for identical frames.
- **Mechanism:** Implement a SQLite-based cache that hashes input frames and stores their corresponding LLM/VLM JSON responses.
- **Outcome:** Rerunning the tool on the same video or resuming an aborted run is near-instantaneous.

### 2.2 Advanced Export Formats
- **Goal:** Support industry-standard screenplay and web formats.
- **Mechanism:** Add support for Fountain (`.fountain`) and HTML.
- **Outcome:** Writers can immediately import the Scribe output into Final Draft or Highland via Fountain.

### 2.3 Audio Analysis (Placeholder/Mock)
- **Goal:** Correlate Scribe's visual descriptions with audio events.
- **Mechanism:** Add a module that extracts the audio track and generates a timestamped waveform or silence detection log. (Full transcription may be out of scope without external ASR, but we will scaffold the module).
- **Outcome:** Scene descriptions contain hints about "loud noise" or "dialogue".

### 2.4 Local Model Fallback Interface
- **Goal:** Enable offline or privacy-preserving execution.
- **Mechanism:** Introduce a provider interface in `vlm_analyzer.py` supporting OpenAI, Anthropic, and a generic `Ollama` or `llama.cpp` local endpoint.
- **Outcome:** Users can run `--provider ollama` to use a local VLM model.

## 3. Success Criteria
- [ ] SQLite cache intercepts and serves previously processed frames.
- [ ] CLI supports `--format fountain` and `--format html`.
- [ ] VLM Analyzer supports pluggable providers.
- [ ] Integration tests verify cache hits.
