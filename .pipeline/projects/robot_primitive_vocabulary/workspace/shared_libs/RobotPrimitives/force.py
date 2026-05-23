"""Force primitives: apply_force, apply_torque, maintain_contact."""

from .primitive import Primitive
from ._registry import register_primitive


class ApplyForce(Primitive):
    """Apply a force to a target in a specified direction.

    Parameters:
        target_id (str): Identifier of the target to apply force to.
        force_x (float): Force component in X direction.
        force_y (float): Force component in Y direction.
        force_z (float): Force component in Z direction.
    """

    def __init__(self, target_id: str = "", force_x: float = 0.0, force_y: float = 0.0,
                 force_z: float = 0.0):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"ApplyForce.target_id must be a non-empty string, got {target_id!r}")
        for val, name in [(force_x, "force_x"), (force_y, "force_y"), (force_z, "force_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"ApplyForce.{name} must be a float, got {type(val).__name__}")
        super().__init__(
            name="apply_force",
            category="force",
            parameters={
                "target_id": "str: Identifier of the target to apply force to",
                "force_x": "float: Force component in X direction",
                "force_y": "float: Force component in Y direction",
                "force_z": "float: Force component in Z direction",
            },
            description="Apply a force to a target in a specified direction.",
            preconditions=["Target is accessible", "Force sensor is active"],
            postconditions=["Force is applied to target"],
        )
        self.target_id = target_id
        self.force_x = float(force_x)
        self.force_y = float(force_y)
        self.force_z = float(force_z)

    def execute(self, **kwargs) -> dict:
        """Execute the apply_force primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        force_x = kwargs.get("force_x", self.force_x)
        force_y = kwargs.get("force_y", self.force_y)
        force_z = kwargs.get("force_z", self.force_z)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        for val, name in [(force_x, "force_x"), (force_y, "force_y"), (force_z, "force_z")]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"execute: {name} must be a float")
        return {"status": "success", "applied_force_to": target_id, "force": (force_x, force_y, force_z)}


class ApplyTorque(Primitive):
    """Apply a torque to a target around an axis.

    Parameters:
        target_id (str): Identifier of the target to apply torque to.
        torque_magnitude (float): Magnitude of the torque.
        axis (str): Axis of rotation ('x', 'y', or 'z').
    """

    def __init__(self, target_id: str = "", torque_magnitude: float = 1.0, axis: str = "z"):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"ApplyTorque.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(torque_magnitude, (int, float)):
            raise TypeError(f"ApplyTorque.torque_magnitude must be a float, got {type(torque_magnitude).__name__}")
        if not isinstance(axis, str) or axis not in ("x", "y", "z"):
            raise ValueError(f"ApplyTorque.axis must be 'x', 'y', or 'z', got {axis!r}")
        super().__init__(
            name="apply_torque",
            category="force",
            parameters={
                "target_id": "str: Identifier of the target to apply torque to",
                "torque_magnitude": "float: Magnitude of the torque",
                "axis": "str: Axis of rotation ('x', 'y', or 'z')",
            },
            description="Apply a torque to a target around an axis.",
            preconditions=["Target is accessible", "Torque sensor is active"],
            postconditions=["Torque is applied to target"],
        )
        self.target_id = target_id
        self.torque_magnitude = float(torque_magnitude)
        self.axis = axis

    def execute(self, **kwargs) -> dict:
        """Execute the apply_torque primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        torque_magnitude = kwargs.get("torque_magnitude", self.torque_magnitude)
        axis = kwargs.get("axis", self.axis)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(torque_magnitude, (int, float)):
            raise TypeError(f"execute: torque_magnitude must be a float")
        if not isinstance(axis, str) or axis not in ("x", "y", "z"):
            raise ValueError(f"execute: axis must be 'x', 'y', or 'z'")
        return {"status": "success", "applied_torque_to": target_id, "torque": torque_magnitude, "axis": axis}


class MaintainContact(Primitive):
    """Maintain contact with a target object.

    Parameters:
        target_id (str): Identifier of the target to maintain contact with.
        force_magnitude (float): Magnitude of the contact force.
    """

    def __init__(self, target_id: str = "", force_magnitude: float = 1.0):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"MaintainContact.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"MaintainContact.force_magnitude must be a float, got {type(force_magnitude).__name__}")
        if force_magnitude <= 0:
            raise ValueError(f"MaintainContact.force_magnitude must be positive, got {force_magnitude}")
        super().__init__(
            name="maintain_contact",
            category="force",
            parameters={
                "target_id": "str: Identifier of the target to maintain contact with",
                "force_magnitude": "float: Magnitude of the contact force",
            },
            description="Maintain contact with a target object.",
            preconditions=["Target is in contact", "Force sensor is active"],
            postconditions=["Contact is maintained with specified force"],
        )
        self.target_id = target_id
        self.force_magnitude = float(force_magnitude)

    def execute(self, **kwargs) -> dict:
        """Execute the maintain_contact primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        force_magnitude = kwargs.get("force_magnitude", self.force_magnitude)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(force_magnitude, (int, float)):
            raise TypeError(f"execute: force_magnitude must be a float")
        if force_magnitude <= 0:
            raise ValueError(f"execute: force_magnitude must be positive")
        return {"status": "success", "maintaining_contact_with": target_id, "force": force_magnitude}


# Register primitives
register_primitive(ApplyForce, "force", "Apply a force to a target in a specified direction.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to apply force to"},
    {"name": "force_x", "type": "float", "description": "Force component in X direction"},
    {"name": "force_y", "type": "float", "description": "Force component in Y direction"},
    {"name": "force_z", "type": "float", "description": "Force component in Z direction"},
])
register_primitive(ApplyTorque, "force", "Apply a torque (rotational force) to a target.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to apply torque to"},
    {"name": "torque_x", "type": "float", "description": "Torque component in X direction"},
    {"name": "torque_y", "type": "float", "description": "Torque component in Y direction"},
    {"name": "torque_z", "type": "float", "description": "Torque component in Z direction"},
])
register_primitive(MaintainContact, "force", "Maintain continuous contact with a surface.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target surface"},
    {"name": "contact_force", "type": "float", "description": "Force to maintain during contact (default 5.0)"},
])
