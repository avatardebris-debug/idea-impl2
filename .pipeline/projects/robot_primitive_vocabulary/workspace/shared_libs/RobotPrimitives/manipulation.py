"""Manipulation primitives: grasp, release, push, pull, lift, place, insert, rotate_object."""

from .primitive import Primitive
from ._registry import register_primitive


class Grasp(Primitive):
    """Grasp an object at a specified location.

    Parameters:
        object_id (str): Identifier of the object to grasp.
        grasp_type (str): Type of grasp (e.g., 'power', 'precision').
    """

    def __init__(self, object_id: str = "", grasp_type: str = "power"):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Grasp.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(grasp_type, str) or not grasp_type.strip():
            raise ValueError(f"Grasp.grasp_type must be a non-empty string, got {grasp_type!r}")
        valid_types = {"power", "precision", "pinch", "suction"}
        if grasp_type not in valid_types:
            raise ValueError(f"Grasp.grasp_type must be one of {valid_types}, got {grasp_type!r}")
        super().__init__(
            name="grasp",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to grasp",
                "grasp_type": "str: Type of grasp (power, precision, pinch, suction)",
            },
            description="Grasp an object at a specified location.",
            preconditions=["Object is detected", "Gripper is open", "Arm is at grasp position"],
            postconditions=["Object is held by gripper"],
        )
        self.object_id = object_id
        self.grasp_type = grasp_type

    def execute(self, **kwargs) -> dict:
        """Execute the grasp primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        grasp_type = kwargs.get("grasp_type", self.grasp_type)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(grasp_type, str):
            raise TypeError(f"execute: grasp_type must be a string")
        return {"status": "success", "grasped": object_id, "grasp_type": grasp_type}


class Release(Primitive):
    """Release a held object.

    Parameters:
        object_id (str): Identifier of the object to release.
        position (str, optional): Release position (default 'current').
    """

    def __init__(self, object_id: str = "", position: str = "current"):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Release.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(position, str) or not position.strip():
            raise ValueError(f"Release.position must be a non-empty string, got {position!r}")
        super().__init__(
            name="release",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to release",
                "position": "str: Release position (default 'current')",
            },
            description="Release a held object.",
            preconditions=["Object is held by gripper"],
            postconditions=["Object is no longer held"],
        )
        self.object_id = object_id
        self.position = position

    def execute(self, **kwargs) -> dict:
        """Execute the release primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        position = kwargs.get("position", self.position)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(position, str):
            raise TypeError(f"execute: position must be a string")
        return {"status": "success", "released": object_id, "position": position}


class Push(Primitive):
    """Push an object in a specified direction.

    Parameters:
        object_id (str): Identifier of the object to push.
        force_magnitude (float): Magnitude of the push force.
        direction_x (float): Direction X component.
        direction_y (float): Direction Y component.
    """

    def __init__(self, object_id: str = "", force_magnitude: float = 1.0,
                 direction_x: float = 1.0, direction_y: float = 0.0):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Push.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"Push.force_magnitude must be a float, got {type(force_magnitude).__name__}")
        if force_magnitude <= 0:
            raise ValueError(f"Push.force_magnitude must be positive, got {force_magnitude}")
        if not isinstance(direction_x, (int, float)):
            raise TypeError(f"Push.direction_x must be a float, got {type(direction_x).__name__}")
        if not isinstance(direction_y, (int, float)):
            raise TypeError(f"Push.direction_y must be a float, got {type(direction_y).__name__}")
        super().__init__(
            name="push",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to push",
                "force_magnitude": "float: Magnitude of the push force",
                "direction_x": "float: Direction X component",
                "direction_y": "float: Direction Y component",
            },
            description="Push an object in a specified direction.",
            preconditions=["Object is in contact", "Force sensor is active"],
            postconditions=["Object has moved in the push direction"],
        )
        self.object_id = object_id
        self.force_magnitude = float(force_magnitude)
        self.direction_x = float(direction_x)
        self.direction_y = float(direction_y)

    def execute(self, **kwargs) -> dict:
        """Execute the push primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        force_magnitude = kwargs.get("force_magnitude", self.force_magnitude)
        direction_x = kwargs.get("direction_x", self.direction_x)
        direction_y = kwargs.get("direction_y", self.direction_y)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"execute: force_magnitude must be a float")
        if force_magnitude <= 0:
            raise ValueError(f"execute: force_magnitude must be positive")
        return {"status": "success", "pushed": object_id, "force": force_magnitude,
                "direction": (direction_x, direction_y)}


class Pull(Primitive):
    """Pull an object toward the robot.

    Parameters:
        object_id (str): Identifier of the object to pull.
        force_magnitude (float): Magnitude of the pull force.
        direction_x (float): Direction X component.
        direction_y (float): Direction Y component.
    """

    def __init__(self, object_id: str = "", force_magnitude: float = 1.0,
                 direction_x: float = -1.0, direction_y: float = 0.0):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Pull.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"Pull.force_magnitude must be a float, got {type(force_magnitude).__name__}")
        if force_magnitude <= 0:
            raise ValueError(f"Pull.force_magnitude must be positive, got {force_magnitude}")
        if not isinstance(direction_x, (int, float)):
            raise TypeError(f"Pull.direction_x must be a float, got {type(direction_x).__name__}")
        if not isinstance(direction_y, (int, float)):
            raise TypeError(f"Pull.direction_y must be a float, got {type(direction_y).__name__}")
        super().__init__(
            name="pull",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to pull",
                "force_magnitude": "float: Magnitude of the pull force",
                "direction_x": "float: Direction X component",
                "direction_y": "float: Direction Y component",
            },
            description="Pull an object toward the robot.",
            preconditions=["Object is in contact", "Force sensor is active"],
            postconditions=["Object has moved toward the robot"],
        )
        self.object_id = object_id
        self.force_magnitude = float(force_magnitude)
        self.direction_x = float(direction_x)
        self.direction_y = float(direction_y)

    def execute(self, **kwargs) -> dict:
        """Execute the pull primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        force_magnitude = kwargs.get("force_magnitude", self.force_magnitude)
        direction_x = kwargs.get("direction_x", self.direction_x)
        direction_y = kwargs.get("direction_y", self.direction_y)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"execute: force_magnitude must be a float")
        if force_magnitude <= 0:
            raise ValueError(f"execute: force_magnitude must be positive")
        return {"status": "success", "pulled": object_id, "force": force_magnitude,
                "direction": (direction_x, direction_y)}


class Lift(Primitive):
    """Lift an object vertically.

    Parameters:
        object_id (str): Identifier of the object to lift.
        height (float): Height to lift the object.
    """

    def __init__(self, object_id: str = "", height: float = 0.5):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Lift.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(height, (int, float)):
            raise TypeError(f"Lift.height must be a float, got {type(height).__name__}")
        if height <= 0:
            raise ValueError(f"Lift.height must be positive, got {height}")
        super().__init__(
            name="lift",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to lift",
                "height": "float: Height to lift the object",
            },
            description="Lift an object vertically.",
            preconditions=["Object is grasped", "Gripper is secure"],
            postconditions=["Object is lifted to specified height"],
        )
        self.object_id = object_id
        self.height = float(height)

    def execute(self, **kwargs) -> dict:
        """Execute the lift primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        height = kwargs.get("height", self.height)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(height, (int, float)):
            raise TypeError(f"execute: height must be a float")
        if height <= 0:
            raise ValueError(f"execute: height must be positive")
        return {"status": "success", "lifted": object_id, "height": height}


class Place(Primitive):
    """Place a held object at a specified location.

    Parameters:
        object_id (str): Identifier of the object to place.
        target_x (float): Target X coordinate.
        target_y (float): Target Y coordinate.
        target_z (float): Target Z coordinate.
    """

    def __init__(self, object_id: str = "", target_x: float = 0.0, target_y: float = 0.0,
                 target_z: float = 0.0):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Place.object_id must be a non-empty string, got {object_id!r}")
        for val, name in [(target_x, "target_x"), (target_y, "target_y"), (target_z, "target_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"Place.{name} must be a float, got {type(val).__name__}")
        super().__init__(
            name="place",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to place",
                "target_x": "float: Target X coordinate",
                "target_y": "float: Target Y coordinate",
                "target_z": "float: Target Z coordinate",
            },
            description="Place a held object at a specified location.",
            preconditions=["Object is held", "Target position is reachable"],
            postconditions=["Object is placed at target location"],
        )
        self.object_id = object_id
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.target_z = float(target_z)

    def execute(self, **kwargs) -> dict:
        """Execute the place primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        target_x = kwargs.get("target_x", self.target_x)
        target_y = kwargs.get("target_y", self.target_y)
        target_z = kwargs.get("target_z", self.target_z)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        for val, name in [(target_x, "target_x"), (target_y, "target_y"), (target_z, "target_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"execute: {name} must be a float")
        return {"status": "success", "placed": object_id, "position": (target_x, target_y, target_z)}


class Insert(Primitive):
    """Insert an object into a target.

    Parameters:
        object_id (str): Identifier of the object to insert.
        target_id (str): Identifier of the target receptacle.
    """

    def __init__(self, object_id: str = "", target_id: str = ""):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"Insert.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"Insert.target_id must be a non-empty string, got {target_id!r}")
        super().__init__(
            name="insert",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to insert",
                "target_id": "str: Identifier of the target receptacle",
            },
            description="Insert an object into a target.",
            preconditions=["Object is grasped", "Target is aligned"],
            postconditions=["Object is inserted into target"],
        )
        self.object_id = object_id
        self.target_id = target_id

    def execute(self, **kwargs) -> dict:
        """Execute the insert primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        target_id = kwargs.get("target_id", self.target_id)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        return {"status": "success", "inserted": object_id, "into": target_id}


class RotateObject(Primitive):
    """Rotate a held object around its axis.

    Parameters:
        object_id (str): Identifier of the object to rotate.
        angle (float): Rotation angle in degrees.
        axis (str): Axis of rotation ('x', 'y', or 'z').
    """

    def __init__(self, object_id: str = "", angle: float = 90.0, axis: str = "z"):
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"RotateObject.object_id must be a non-empty string, got {object_id!r}")
        if not isinstance(angle, (int, float)):
            raise TypeError(f"RotateObject.angle must be a float, got {type(angle).__name__}")
        if not isinstance(axis, str) or axis not in ("x", "y", "z"):
            raise ValueError(f"RotateObject.axis must be 'x', 'y', or 'z', got {axis!r}")
        super().__init__(
            name="rotate_object",
            category="manipulation",
            parameters={
                "object_id": "str: Identifier of the object to rotate",
                "angle": "float: Rotation angle in degrees",
                "axis": "str: Axis of rotation ('x', 'y', or 'z')",
            },
            description="Rotate a held object around its axis.",
            preconditions=["Object is grasped", "Gripper is secure"],
            postconditions=["Object is rotated by specified angle"],
        )
        self.object_id = object_id
        self.angle = float(angle)
        self.axis = axis

    def execute(self, **kwargs) -> dict:
        """Execute the rotate_object primitive."""
        object_id = kwargs.get("object_id", self.object_id)
        angle = kwargs.get("angle", self.angle)
        axis = kwargs.get("axis", self.axis)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError(f"execute: object_id must be a non-empty string")
        if not isinstance(angle, (int, float)):
            raise TypeError(f"execute: angle must be a float")
        if not isinstance(axis, str) or axis not in ("x", "y", "z"):
            raise ValueError(f"execute: axis must be 'x', 'y', or 'z'")
        return {"status": "success", "rotated": object_id, "angle": angle, "axis": axis}


# Register primitives
register_primitive(Grasp, "manipulation", "Grasp an object at a specified location.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to grasp"},
    {"name": "grasp_type", "type": "str", "description": "Type of grasp (e.g., 'power', 'precision')"},
])
register_primitive(Release, "manipulation", "Release a held object.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to release"},
    {"name": "place_x", "type": "float", "description": "X coordinate to place at (default 0)"},
    {"name": "place_y", "type": "float", "description": "Y coordinate to place at (default 0)"},
])
register_primitive(Push, "manipulation", "Push an object in a specified direction.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to push"},
    {"name": "direction_x", "type": "float", "description": "Direction X component"},
    {"name": "direction_y", "type": "float", "description": "Direction Y component"},
    {"name": "force_magnitude", "type": "float", "description": "Force magnitude (default 1.0)"},
])
register_primitive(Pull, "manipulation", "Pull an object toward the robot.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to pull"},
    {"name": "force_magnitude", "type": "float", "description": "Force magnitude (default 1.0)"},
])
register_primitive(Lift, "manipulation", "Lift an object vertically.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to lift"},
    {"name": "height", "type": "float", "description": "Lift height (default 0.1)"},
])
register_primitive(Place, "manipulation", "Place a held object at a target location.", [
    {"name": "target_x", "type": "float", "description": "Target X coordinate"},
    {"name": "target_y", "type": "float", "description": "Target Y coordinate"},
    {"name": "target_z", "type": "float", "description": "Target Z coordinate"},
])
register_primitive(Insert, "manipulation", "Insert an object into a target slot or hole.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to insert"},
    {"name": "slot_id", "type": "str", "description": "Identifier of the target slot"},
])
register_primitive(RotateObject, "manipulation", "Rotate a held object around an axis.", [
    {"name": "object_id", "type": "str", "description": "Identifier of the object to rotate"},
    {"name": "axis", "type": "str", "description": "Rotation axis (x, y, or z)"},
    {"name": "angle", "type": "float", "description": "Rotation angle in degrees"},
])
