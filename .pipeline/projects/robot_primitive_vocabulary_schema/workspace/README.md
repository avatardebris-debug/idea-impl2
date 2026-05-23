# Robot Primitive Vocabulary Schema

A JSON schema and Python dataclasses for robot motion primitives.

## Overview

This project defines atomic motion primitives (grasp, place, slide, push, lift, rotate) with parameters for position, orientation, velocity, acceleration, force limits, and duration.

## Installation

```bash
pip install -e .
```

## Usage

### Python API

```python
from pipeline.code.primitives import (
    GraspPrimitive,
    create_primitive,
    validate_primitive,
    load_schema,
)

# Create a primitive via factory
prim = create_primitive("grasp", position=[0.1, 0.2, 0.3])

# Or use the dataclass directly
prim = GraspPrimitive(position=[0.1, 0.2, 0.3], grasp_force=10.0)

# Validate
errors = validate_primitive(prim)
if errors:
    print("Errors:", errors)

# Serialize
print(prim.to_json())
```

### CLI

```bash
# Create a primitive
primitives create grasp --json grasp_data.json -o output.json

# Validate a primitive
primitives validate grasp_data.json

# Show the schema
primitives schema -o schema.json
```

## Project Structure

```
.pipeline/
  code/
    primitives.py      # Core data model
  schemas/
    primitive_schema.json  # JSON Schema
cli/
  primitives_cli.py    # CLI entry point
tests/
  test_primitives.py   # Test suite
```

## Testing

```bash
pytest tests/
```

## License

MIT
