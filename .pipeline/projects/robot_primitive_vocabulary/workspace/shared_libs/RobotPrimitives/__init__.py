"""RobotPrimitives - Canonical atomic robot action primitives library.

Provides ~29 canonical robot action primitives across 5 categories:
- locomotion: move_to, rotate_to, approach, retreat
- manipulation: grasp, release, push, pull, lift, place, insert, rotate_object
- observation: look_at, scan, measure_distance, detect_object
- force: apply_force, apply_torque, maintain_contact
- control_flow: sequence, parallel, repeat_until, conditional, wait, signal_done, request_human
"""

__version__ = "0.1.0"

from .primitive import Primitive, VALID_CATEGORIES
from .locomotion import MoveTo, RotateTo, Approach, Retreat
from .manipulation import Grasp, Release, Push, Pull, Lift, Place, Insert, RotateObject
from .observation import LookAt, Scan, MeasureDistance, DetectObject
from .force import ApplyForce, ApplyTorque, MaintainContact
from .control_flow import Sequence, Parallel, RepeatUntil, Conditional, Wait, SignalDone, RequestHuman
from ._registry import load_all_primitives, category_map

__all__ = [
    "Primitive",
    "VALID_CATEGORIES",
    "MoveTo", "RotateTo", "Approach", "Retreat",
    "Grasp", "Release", "Push", "Pull", "Lift", "Place", "Insert", "RotateObject",
    "LookAt", "Scan", "MeasureDistance", "DetectObject",
    "ApplyForce", "ApplyTorque", "MaintainContact",
    "Sequence", "Parallel", "RepeatUntil", "Conditional", "Wait", "SignalDone", "RequestHuman",
    "load_all_primitives",
    "category_map",
]
