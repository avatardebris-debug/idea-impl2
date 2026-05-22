"""IoT subsystem for Chronovision.

This package provides the infrastructure for integrating real-time IoT sensor data
into the Chronovision spatial model. It includes:

- Schema definitions for sensor data and configurations
- A streaming connector for ingesting data from various sources
- A sensor registry for managing sensor metadata
- An updater that integrates sensor data into the StateSpace
"""

from chronovision.src.iot.schema import (
    SensorConfig,
    SensorData,
    SensorType,
    SensorStatus,
)
from chronovision.src.iot.streaming import StreamingConnector
from chronovision.src.iot.registry import SensorRegistry
from chronovision.src.iot.updater import IoTUpdater

__all__ = [
    "SensorConfig",
    "SensorData",
    "SensorType",
    "SensorStatus",
    "StreamingConnector",
    "SensorRegistry",
    "IoTUpdater",
]
