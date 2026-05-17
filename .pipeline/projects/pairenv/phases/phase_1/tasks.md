# Phase 1 Tasks

- [ ] Task 1: Design and implement the device abstraction interface and serial transport adapter
  - What: Define a Python protocol/ABC for device abstraction (connect, disconnect, send, receive) and implement a concrete SerialTransport adapter using pyserial for UART communication with an Arduino
  - Files: src/pairenv/abstraction.py, src/pairenv/transports/serial_transport.py, src/pairenv/transports/__init__.py
  - Done when: The SerialTransport class can open a serial port, send a byte string to the device, and read a response; the DeviceABC defines connect/disconnect/send/receive methods; `python -c "from pairenv.transports.serial_transport import SerialTransport; print('OK')"` succeeds

- [ ] Task 2: Build the device registry with JSON-based pairing state persistence
  - What: Implement a DeviceRegistry class that stores device pairings (device_id, type, transport config, connection state) in a JSON file on disk, with methods to add, list, get, and remove paired devices
  - Files: src/pairenv/registry.py, src/pairenv/config/default_registry.json
  - Done when: A DeviceRegistry can persist a device entry to disk, reload it on restart, list all paired devices, and remove a device; `python -c "from pairenv.registry import DeviceRegistry; r = DeviceRegistry(); r.add('test', 'arduino', {'port': '/dev/ttyUSB0'}); print(r.list_devices())"` works and the JSON file is created

- [ ] Task 3: Build the rule-based English parser with ≥5 command templates
  - What: Implement an EnglishParser class that uses regex/template matching to convert natural language commands into structured command dicts. Must support at least: "turn on the LED", "turn off the LED", "set pin X to HIGH", "set pin X to LOW", "read sensor on pin X", "blink LED N times"
  - Files: src/pairenv/parser.py
  - Done when: parser.parse("turn on the LED") returns {"action": "set_pin", "pin": 13, "state": "HIGH"}; parser.parse("read sensor on pin A0") returns {"action": "read_pin", "pin": "A0"}; all ≥5 templates produce correct structured output; `python -c "from pairenv.parser import EnglishParser; p = EnglishParser(); assert p.parse('turn on the LED')['action'] == 'set_pin'"` passes

- [ ] Task 4: Implement the command router and bidirectional message handler
  - What: Build a CommandRouter that takes structured command dicts from the parser and routes them to the correct device via the appropriate transport adapter; implement a MessageHandler that reads responses from the device and formats them back into natural language for the user
  - Files: src/pairenv/router.py, src/pairenv/handler.py
  - Done when: CommandRouter can look up a paired device by ID, translate a structured command into transport-specific bytes, send it, and receive a response; MessageHandler converts device responses like "PIN13=HIGH" back to "The LED is now ON"; `python -c "from pairenv.router import CommandRouter; from pairenv.handler import MessageHandler; print('OK')"` succeeds

- [ ] Task 5: Write the CLI interface and integration test harness
  - What: Create a CLI entry point (pairenv) with subcommands: `pair` (register a device), `send` (translate English → send to device), `list` (show paired devices), and `status` (show device state). Also write an integration test script that exercises the full pipeline
  - Files: src/pairenv/cli.py, tests/test_integration.py, README.md
  - Done when: `pairenv pair --name test --type arduino --port /dev/ttyUSB0` registers a device; `pairenv send "turn on the LED"` parses, routes, and returns a result; `pairenv list` shows paired devices; integration test script runs the full pipeline end-to-end; README documents the pairing flow and command syntax