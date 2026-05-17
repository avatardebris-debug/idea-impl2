## Phase 2 — Multi-Device Support & Robust Translation

**Goal:** Support multiple device types, multiple simultaneous connections, and significantly improve the English-to-command translation quality.

### Description

Expand the system beyond a single device type. Add transport protocol diversity (BLE, MQTT, HTTP), improve the command parser to handle more complex and ambiguous natural language, and build a device capability discovery mechanism.

### Deliverable

A multi-device capable system that:
1. Supports ≥3 transport protocols (serial, MQTT, HTTP/gRPC)
2. Manages ≥5 simultaneous device pairings across different device types
3. Uses an LLM-assisted parser that can handle ambiguous/complex English input
4. Auto-discovers device capabilities and builds a dynamic device registry
5. Provides a REST API for external software to interact with paired devices

### Dependencies

- Phase 1 complete (core abstraction, pairing, command routing)
- LLM integration (OpenAI API or local model via Ollama)
- MQTT broker (Mosquitto or cloud-hosted)
- BLE stack (bleak library)
- FastAPI for REST API surface

### Success Criteria

- [ ] Supports serial, MQTT, and BLE transport simultaneously
- [ ] Manages ≥5 devices of ≥3 different types concurrently
- [ ] LLM-assisted parser handles ≥20 command patterns with ≥90% accuracy
- [ ] Device capability discovery works for ≥3 device profiles
- [ ] REST API accepts English commands and returns structured results
- [ ] Error handling: graceful degradation when a device disconnects
- [ ] Command queue with retry logic for unreliable connections

### Tasks

- [ ] Implement MQTT transport adapter
- [ ] Implement BLE transport adapter
- [ ] Implement HTTP/gRPC transport adapter
- [ ] Build device capability discovery protocol
- [ ] Integrate LLM-assisted English parser
- [ ] Build dynamic device registry (in-memory + persistent store)
- [ ] Implement command queue with retry logic
- [ ] Build REST API (FastAPI)
- [ ] Implement disconnect/reconnect handling
- [ ] Integration tests with multi-device setup
- [ ] Performance benchmarks (latency, throughput)

---

