"""Observation primitives: look_at, scan, measure_distance, detect_object."""

from .primitive import Primitive
from ._registry import register_primitive


class LookAt(Primitive):
    """Direct the robot's sensor/eye to look at a target.

    Parameters:
        target_id (str): Identifier of the target to look at.
        frame (str): Sensor frame to use (e.g., 'head', 'hand').
    """

    def __init__(self, target_id: str = "", frame: str = "head"):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"LookAt.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(frame, str) or not frame.strip():
            raise ValueError(f"LookAt.frame must be a non-empty string, got {frame!r}")
        super().__init__(
            name="look_at",
            category="observation",
            parameters={
                "target_id": "str: Identifier of the target to look at",
                "frame": "str: Sensor frame to use (e.g., 'head', 'hand')",
            },
            description="Direct the robot's sensor/eye to look at a target.",
            preconditions=["Sensor is powered", "Target is visible"],
            postconditions=["Sensor is oriented toward target"],
        )
        self.target_id = target_id
        self.frame = frame

    def execute(self, **kwargs) -> dict:
        """Execute the look_at primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        frame = kwargs.get("frame", self.frame)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(frame, str):
            raise TypeError(f"execute: frame must be a string")
        return {"status": "success", "looking_at": target_id, "frame": frame}


class Scan(Primitive):
    """Perform a 360-degree scan of the environment.

    Parameters:
        frame (str): Sensor frame to use for scanning.
        resolution (float): Scan resolution in degrees (default 1.0).
    """

    def __init__(self, frame: str = "head", resolution: float = 1.0):
        if not isinstance(frame, str) or not frame.strip():
            raise ValueError(f"Scan.frame must be a non-empty string, got {frame!r}")
        if not isinstance(resolution, (int, float)):
            raise TypeError(f"Scan.resolution must be a float, got {type(resolution).__name__}")
        if resolution <= 0:
            raise ValueError(f"Scan.resolution must be positive, got {resolution}")
        super().__init__(
            name="scan",
            category="observation",
            parameters={
                "frame": "str: Sensor frame to use for scanning",
                "resolution": "float: Scan resolution in degrees (default 1.0)",
            },
            description="Perform a 360-degree scan of the environment.",
            preconditions=["Sensor is powered", "Environment is accessible"],
            postconditions=["Scan data is collected"],
        )
        self.frame = frame
        self.resolution = float(resolution)

    def execute(self, **kwargs) -> dict:
        """Execute the scan primitive."""
        frame = kwargs.get("frame", self.frame)
        resolution = kwargs.get("resolution", self.resolution)
        if not isinstance(frame, str):
            raise TypeError(f"execute: frame must be a string")
        if not isinstance(resolution, (int, float)):
            raise TypeError(f"execute: resolution must be a float")
        if resolution <= 0:
            raise ValueError(f"execute: resolution must be positive")
        return {"status": "success", "scanned": frame, "resolution": resolution}


class MeasureDistance(Primitive):
    """Measure the distance to a target object.

    Parameters:
        target_id (str): Identifier of the target to measure distance to.
        sensor_frame (str): Sensor frame to use for measurement.
    """

    def __init__(self, target_id: str = "", sensor_frame: str = "head"):
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"MeasureDistance.target_id must be a non-empty string, got {target_id!r}")
        if not isinstance(sensor_frame, str) or not sensor_frame.strip():
            raise ValueError(f"MeasureDistance.sensor_frame must be a non-empty string, got {sensor_frame!r}")
        super().__init__(
            name="measure_distance",
            category="observation",
            parameters={
                "target_id": "str: Identifier of the target to measure distance to",
                "sensor_frame": "str: Sensor frame to use for measurement",
            },
            description="Measure the distance to a target object.",
            preconditions=["Target is visible", "Sensor is calibrated"],
            postconditions=["Distance measurement is obtained"],
        )
        self.target_id = target_id
        self.sensor_frame = sensor_frame

    def execute(self, **kwargs) -> dict:
        """Execute the measure_distance primitive."""
        target_id = kwargs.get("target_id", self.target_id)
        sensor_frame = kwargs.get("sensor_frame", self.sensor_frame)
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError(f"execute: target_id must be a non-empty string")
        if not isinstance(sensor_frame, str):
            raise TypeError(f"execute: sensor_frame must be a string")
        return {"status": "success", "measured_to": target_id, "from": sensor_frame}


class DetectObject(Primitive):
    """Detect and identify an object in the environment.

    Parameters:
        sensor_frame (str): Sensor frame to use for detection.
        object_class (str, optional): Class of object to detect (default '').
    """

    def __init__(self, sensor_frame: str = "head", object_class: str = ""):
        if not isinstance(sensor_frame, str) or not sensor_frame.strip():
            raise ValueError(f"DetectObject.sensor_frame must be a non-empty string, got {sensor_frame!r}")
        if not isinstance(object_class, str):
            raise TypeError(f"DetectObject.object_class must be a string, got {type(object_class).__name__}")
        super().__init__(
            name="detect_object",
            category="observation",
            parameters={
                "sensor_frame": "str: Sensor frame to use for detection",
                "object_class": "str: Class of object to detect (default '')",
            },
            description="Detect and identify an object in the environment.",
            preconditions=["Sensor is powered", "Environment is accessible"],
            postconditions=["Object detection result is obtained"],
        )
        self.sensor_frame = sensor_frame
        self.object_class = object_class

    def execute(self, **kwargs) -> dict:
        """Execute the detect_object primitive."""
        sensor_frame = kwargs.get("sensor_frame", self.sensor_frame)
        object_class = kwargs.get("object_class", self.object_class)
        if not isinstance(sensor_frame, str):
            raise TypeError(f"execute: sensor_frame must be a string")
        if not isinstance(object_class, str):
            raise TypeError(f"execute: object_class must be a string")
        return {"status": "success", "detected_from": sensor_frame, "class": object_class}


# Register primitives
register_primitive(LookAt, "observation", "Direct the robot's sensor/eye to look at a target.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to look at"},
    {"name": "frame", "type": "str", "description": "Sensor frame to use (e.g., 'head', 'hand')"},
])
register_primitive(Scan, "observation", "Perform a 360-degree scan of the environment.", [
    {"name": "frame", "type": "str", "description": "Sensor frame to use (default 'head')"},
    {"name": "resolution", "type": "float", "description": "Scan resolution in degrees (default 1.0)"},
])
register_primitive(MeasureDistance, "observation", "Measure distance to a target.", [
    {"name": "target_id", "type": "str", "description": "Identifier of the target to measure"},
    {"name": "sensor_frame", "type": "str", "description": "Sensor frame (default 'hand')"},
])
register_primitive(DetectObject, "observation", "Detect and identify objects in the field of view.", [
    {"name": "frame", "type": "str", "description": "Sensor frame (default 'head')"},
    {"name": "class_filter", "type": "str", "description": "Optional class filter (default None)"},
])
