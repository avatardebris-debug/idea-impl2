# RobotPrimitives

Canonical atomic robot primitives for task planning and execution.

## Overview

This library provides a vocabulary of atomic robot primitives organized into five categories:

- **Locomotion**: Move the robot's base (move_to, rotate_to, approach, retreat)
- **Manipulation**: Manipulate objects (grasp, release, push, pull, lift, place, insert, rotate_object)
- **Observation**: Gather sensor data (look_at, scan, measure_distance, detect_object)
- **Force**: Apply physical forces (apply_force, apply_torque, maintain_contact)
- **Control Flow**: Compose primitives (sequence, parallel, repeat_until, conditional, wait, signal_done, request_human)

## Installation

```bash
pip install robot_primitives
```

## Usage

```python
from shared_libs.RobotPrimitives.locomotion import MoveTo
from shared_libs.RobotPrimitives.manipulation import Grasp
from shared_libs.RobotPrimitives.control_flow import Sequence

# Create primitives
move = MoveTo(target_x=1.0, target_y=0.5)
grasp = Grasp(object_id="cup1", grasp_type="power")

# Compose into a sequence
task = Sequence(primitives=[move, grasp])

# Execute
result = task.execute()
print(result["status"])  # "success"
```

## Primitive Interface

All primitives inherit from `Primitive` and share a common interface:

```python
class Primitive:
    name: str              # Unique identifier (e.g., "move_to")
    category: str          # One of: locomotion, manipulation, observation, force, control_flow
    parameters: dict       # Primitive-specific parameters
    description: str       # Human-readable description
    execute() -> dict      # Execute the primitive, return {"status": "success"|"error", ...}
```

## Categories

### Locomotion
- `MoveTo(target_x, target_y, target_z)` - Move base to coordinates
- `RotateTo(target_angle)` - Rotate base by angle (degrees)
- `Approach(target_id, distance)` - Move toward an object
- `Retreat(target_id, distance)` - Move away from an object

### Manipulation
- `Grasp(object_id, grasp_type)` - Grasp an object
- `Release(object_id)` - Release held object
- `Push(object_id, direction_x, direction_y, direction_z)` - Push an object
- `Pull(object_id, direction_x, direction_y, direction_z)` - Pull an object
- `Lift(object_id, height)` - Lift an object vertically
- `Place(object_id, target_x, target_y, target_z)` - Place held object
- `Insert(object_id, target_id)` - Insert object into target
- `RotateObject(object_id, angle)` - Rotate held object

### Observation
- `LookAt(target_id, frame)` - Direct sensor to target
- `Scan(frame)` - Scan environment
- `MeasureDistance(target_id)` - Measure distance to target
- `DetectObject(frame)` - Detect objects in frame

### Force
- `ApplyForce(target_id, force_x, force_y, force_z)` - Apply force vector
- `ApplyTorque(target_id, torque_magnitude, axis)` - Apply torque
- `MaintainContact(target_id, force_magnitude)` - Maintain contact force

### Control Flow
- `Sequence(primitives)` - Execute primitives in order
- `Parallel(primitives)` - Execute primitives concurrently
- `RepeatUntil(primitive, condition)` - Repeat until condition met
- `Conditional(condition, primitive)` - Execute if condition true
- `Wait(duration)` - Wait for specified time
- `SignalDone(task_id)` - Signal task completion
- `RequestHuman(task_id, reason)` - Request human assistance

## Testing

```bash
pytest tests/
```

## License

MIT
