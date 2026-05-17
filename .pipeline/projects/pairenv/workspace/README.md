# pairenv — Hardware-Software Bridge

A Python library that bridges natural language commands to physical hardware devices (Arduino, ESP32, etc.) via serial transport.

## Architecture

```
User (English) → EnglishParser → CommandRouter → SerialTransport → Device
Device → SerialTransport → MessageHandler → User (English)
```

## Components

- **`parser.EnglishParser`**: Rule-based parser mapping ≥8 English templates to structured commands
- **`registry.DeviceRegistry`**: JSON-backed device registry with CRUD operations
- **`router.CommandRouter`**: Routes structured commands to paired devices
- **`router.MessageHandler`**: Converts device responses to natural language
- **`transports.serial_transport.SerialTransport`**: Async serial communication layer
- **`abstraction.DeviceABC`**: Abstract base class for device adapters
- **`cli`**: Command-line interface

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
# Register a device
pairenv pair --name arduino1 --type arduino --port /dev/ttyUSB0

# Send a command
pairenv send "turn on the LED" --device arduino1

# List devices
pairenv list

# Check status
pairenv status --device arduino1
```

### Python API

```python
from pairenv.parser import EnglishParser
from pairenv.registry import DeviceRegistry
from pairenv.router import CommandRouter, MessageHandler

# Register device
registry = DeviceRegistry()
registry.add("arduino1", "arduino", {"port": "/dev/ttyUSB0"})

# Parse command
parser = EnglishParser()
cmd = parser.parse("turn on the LED")
# → {"action": "set_pin", "pin": 13, "state": "HIGH"}

# Route to device
router = CommandRouter(registry)
response = await router.route("arduino1", cmd)

# Format response
formatted = MessageHandler.format_response(response)
# → "The LED on pin 13 is now ON"
```

## Supported English Templates

| Template | Parsed Action |
|----------|--------------|
| `turn on the LED` | `set_pin(pin=13, state=HIGH)` |
| `turn off the LED` | `set_pin(pin=13, state=LOW)` |
| `set pin X to HIGH` | `set_pin(pin=X, state=HIGH)` |
| `set pin X to LOW` | `set_pin(pin=X, state=LOW)` |
| `read sensor on pin X` | `read_sensor(pin=X)` |
| `read pin X` | `read_pin(pin=X)` |
| `blink LED N times` | `blink(pin=13, count=N)` |
| `blink pin X N times` | `blink(pin=X, count=N)` |

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT
