"""Locomotion primitives: move_to, rotate_to, approach, retreat."""

from .primitive import Primitive
from ._registry import register_primitive


class MoveTo(Primitive):
    """Move the robot to a target position.

    Parameters:
        target_x (float): Target X coordinate.
        target_y (float): Target Y coordinate.
        target_z (float, optional): Target Z coordinate (default 0).
    """

    def __init__(self, target_x: float = 0.0, target_y: float = 0.0, target_z: float = 0.0):
        # Validate parameters
        for val, name in [(target_x, "target_x"), (target_y, "target_y"), (target_z, "target_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"MoveTo.{name} must be a float, got {type(val).__name__}: {val!r}")
        super().__init__(
            name="move_to",
            category="locomotion",
            parameters={
                "target_x": "float: Target X coordinate",
                "target_y": "float: Target Y coordinate",
                "target_z": "float: Target Z coordinate (default 0)",
            },
            description="Move the robot to a target position in 3D space.",
            preconditions=["Robot is powered on", "Navigation system is calibrated"],
            postconditions=["Robot is at target position", "Position confirmation received"],
        )
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.target_z = float(target_z)

    def execute(self, **kwargs) -> dict:
        """Execute the move_to primitive."""
        target_x = kwargs.get("target_x", self.target_x)
        target_y = kwargs.get("target_y", self.target_y)
        target_z = kwargs.get("target_z", self.target_z)
        for val, name in [(target_x, "target_x"), (target_y, "target_y"), (target_z, "target_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"execute: {name} must be a float, got {type(val).__name__}")
        return {"status": "success", "moved_to": (target_x, target_y, target_z)}


class RotateTo(Primitive):
    """Rotate the robot to a target orientation.

    Parameters:
        target_angle (float): Target angle in degrees (0-360).
        frame (str, optional): Reference frame for rotation (default 'base').
    """

    def __init__(self, target_angle: float = 0.0, frame: str = "base"):
        if not isinstance(target_angle, (int, float)):
            raise TypeError(f"RotateTo.target_angle must be a float, got {type(target_angle).__name__}")
        if not isinstance(frame, str) or not frame.strip():
            raise TypeError(f"RotateTo.frame must be a non-empty string, got {frame!r}")
        if not (0 <= target_angle <= 360):
            raise ValueError(f"RotateTo.target_angle must be in [0, 360], got {target_angle}")
        super().__init__(
            name="rotate_to",
            category="locomotion",
            parameters={
                "target_angle": "float: Target angle in degrees (0-360)",
                "frame": "str: Reference frame for rotation (default 'base')",
            },
            description="Rotate the robot to a target orientation.",
            preconditions=["Robot is powered on", "IMU is calibrated"],
            postconditions=["Robot is at target orientation"],
        )
        self.target_angle = float(target_angle)
        self.frame = frame

    def execute(self, **kwargs) -> dict:
        """Execute the rotate_to primitive."""
        target_angle = kwargs.get("target_angle", self.target_angle)
        frame = kwargs.get("frame", self.frame)
        if not isinstance(target_angle, (int, float)):
            raise TypeError(f"execute: target_angle must be a float, got {type(target_angle).__name__}")
        if not isinstance(frame, str):
            raise TypeError(f"execute: frame must be a string, got {type(frame).__name__}")
        return {"status": "success", "rotated_to": target_angle, "frame": frame}


class Approach(Primitive):
    """Approach a target object or position.

    Parameters:
        target_id (str): Identifier of the target to approach.
        distance (float, optional): Distance to maintain from target (default 1.0).
    """

    def __init__(self, target_id: str = "", distance: float = 1.0):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"Approach.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(distance, (int, float)):
            raise TypeError(f"Approach.distance must be a float, got {type(distance).__name__}")
        if distance <= 0:
            raise ValueError(f"Approach.distance must be positive, got {distance}")
        super().__init__(
            name="approach",
            category="locomotion",
            parameters={
                "target_id": "str: Identifier of the target to approach",
                "distance": "float: Distance to maintain from target (default 1.0)",
            },
            description="Approach a target object or position.",
            preconditions=["Target is detected", "Path is clear"],
            postconditions=["Robot is at specified distance from target"],
        )
        self.target_id = target_id
        self.distance = float(distance)

    def execute(self, **kwargs) -> dict:
        """Execute the approach primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        distance = kwargs.get("distance", self.distance)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(distance, (int, float)):
            raise TypeError(f"execute: distance must be a float")
        if distance <= 0:
            raise ValueError(f"execute: distance must be positive")
        return {"status": "success", "approached_to": target_id, "distance": distance}


class Retreat(Primitive):
    """Retreat from a target object or position.

    Parameters:
        target_id (str): Identifier of the target to retreat from.
        distance (float, optional): Distance to move away from target (default 1.0).
    """

    def __init__(self, target_id: str = "", distance: float = 1.0):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"Retreat.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(distance, (int, float)):
            raise TypeError(f"Retreat.distance must be a float, got {type(distance).__name__}")
        if distance <= 0:
            raise ValueError(f"Retreat.distance must be positive, got {distance}")
        super().__init__(
            name="retreat",
            category="locomotion",
            parameters={
                "target_id": "str: Identifier of the target to retreat from",
                "distance": "float: Distance to move away from target (default 1.0)",
            },
            description="Retreat from a target object or position.",
            preconditions=["Target is detected", "Path is clear"],
            postconditions=["Robot is at specified distance from target"],
        )
        self.target_id = target_id
        self.distance = float(distance)

    def execute(self, **kwargs) -> dict:
        """Execute the retreat primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        distance = kwargs.get("distance", self.distance)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(distance, (int, float)):
            raise TypeError(f"execute: distance must be a float")
        if distance <= 0:
            raise ValueError(f"execute: distance must be positive")
        return {"status": "success", "retreated_from": target_id, "distance": distance}


# Register primitives
register_primitive(MoveTo, "locomotion", "Move the robot to a target position in 3D space.", [
    {"name": "target_x", "type": "float", "description": "Target X coordinate"},
    {"name": "target_y", "type": "float", "description": "Target Y coordinate"},
    {"name": "target_z", "type": "float", "description": "Target Z coordinate (default 0)"},
])
register_primitive(RotateTo, "locomotion", "Rotate the robot to a target orientation.", [
    {"name": "target_angle", "type": "float", "description": "Target angle in degrees (0-360)"},
    {"name": "frame", "type": "str", "description": "Reference frame for rotation (default 'base')"},
])
register_primitive(Approach, "locomotion", "Approach a target object or position.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to approach"},
    {"name": "distance", "type": "float", "description": "Distance to maintain from target (default 1.0)"},
])
register_primitive(Retreat, "locomotion", "Retreat from a target object or position.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to retreat from"},
    {"name": "distance", "type": "float", "description": "Distance to move away from target (default 1.0)"},
])
