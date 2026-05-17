## Phase 1 — MVP: Core Abstraction & Single-Device Pairing

**Goal:** A working prototype that can pair one device, translate simple English commands, and send/receive data.

### Description

Build the foundational layer: a device abstraction interface, a minimal English-to-structured-command parser, and a pairing mechanism for a single device type. This proves the core concept end-to-end.

### Deliverable

A CLI tool that:
1. Discovers and pairs a single device type (e.g., an Arduino over serial/UART)
2. Accepts English input like `"turn on the LED"` and translates it to `{"action": "set_pin", "pin": 13, "state": "HIGH"}`
3. Sends the command to the device and reads back a response
4. Returns the result to the user in natural language

### Dependencies

- Python 3.10+ (or Rust for performance-critical paths)
- pyserial for serial communication
- A simple rule-based parser (no LLM dependency yet — use template matching + keyword extraction)
- One test device (Arduino Uno or similar)

### Success Criteria

- [ ] Can pair a device via serial connection within 30 seconds
- [ ] Translates ≥5 distinct English commands to device-specific format with 100% accuracy
- [ ] Sends commands to device and receives responses reliably
- [ ] Device registry stores pairing state persistently (JSON config file)
- [ ] End-to-end round-trip latency < 2 seconds for simple commands

### Tasks

- [ ] Design device abstraction interface (trait/protocol definition)
- [ ] Implement serial transport adapter
- [ ] Build device registry (pairing state persistence)
- [ ] Build rule-based English parser with ≥5 command templates
- [ ] Build command router that maps structured commands to device protocols
- [ ] Implement bidirectional message handler
- [ ] Write CLI interface
- [ ] Integration test with Arduino test device
- [ ] Document pairing flow and command syntax

---