"""Sensor registry for managing IoT sensor configurations and metadata."""

import logging
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict

from chronovision.src.iot.schema import SensorConfig, SensorData, SensorType, SensorStatus

logger = logging.getLogger(__name__)


class SensorRegistry:
    """Registry for managing IoT sensor configurations and metadata.
    
    Tracks all registered sensors, their configurations, and current status.
    Provides lookup, filtering, and management capabilities.
    """
    
    def __init__(self):
        self._sensors: Dict[str, SensorConfig] = {}
        self._sensor_data: Dict[str, List[SensorData]] = defaultdict(list)
        self._sensor_types: Dict[SensorType, List[str]] = defaultdict(list)
        self._sensor_status: Dict[str, SensorStatus] = {}
        self._max_data_points_per_sensor = 1000
    
    def register_sensor(self, config: SensorConfig) -> bool:
        """Register a new sensor."""
        if config.sensor_id in self._sensors:
            logger.warning(f"Sensor {config.sensor_id} already registered, updating config")
        self._sensors[config.sensor_id] = config
        self._sensor_types[config.sensor_type].append(config.sensor_id)
        self._sensor_status[config.sensor_id] = SensorStatus.ONLINE
        logger.info(f"Registered sensor {config.sensor_id} of type {config.sensor_type.value}")
        return True
    
    def unregister_sensor(self, sensor_id: str) -> bool:
        """Unregister a sensor."""
        if sensor_id not in self._sensors:
            logger.warning(f"Sensor {sensor_id} not found in registry")
            return False
        config = self._sensors.pop(sensor_id)
        if sensor_id in self._sensor_types[config.sensor_type]:
            self._sensor_types[config.sensor_type].remove(sensor_id)
        self._sensor_status.pop(sensor_id, None)
        self._sensor_data.pop(sensor_id, None)
        logger.info(f"Unregistered sensor {sensor_id}")
        return True
    
    def get_sensor_config(self, sensor_id: str) -> Optional[SensorConfig]:
        """Get configuration for a sensor."""
        return self._sensors.get(sensor_id)
    
    def get_sensor_status(self, sensor_id: str) -> Optional[SensorStatus]:
        """Get current status of a sensor."""
        return self._sensor_status.get(sensor_id)
    
    def update_sensor_status(self, sensor_id: str, status: SensorStatus) -> None:
        """Update the status of a sensor."""
        self._sensor_status[sensor_id] = status
    
    def add_sensor_data(self, sensor_data: SensorData) -> None:
        """Add sensor data to the registry."""
        self._sensor_data[sensor_data.sensor_id].append(sensor_data)
        if len(self._sensor_data[sensor_data.sensor_id]) > self._max_data_points_per_sensor:
            self._sensor_data[sensor_data.sensor_id] = self._sensor_data[sensor_data.sensor_id][-self._max_data_points_per_sensor:]
    
    def get_sensor_data(self, sensor_id: str, limit: Optional[int] = None) -> List[SensorData]:
        """Get historical data for a sensor."""
        data = self._sensor_data.get(sensor_id, [])
        return data[-limit:] if limit else data
    
    def get_sensors_by_type(self, sensor_type: SensorType) -> List[str]:
        """Get all sensors of a specific type."""
        return list(self._sensor_types.get(sensor_type, []))
    
    def get_all_sensors(self) -> Dict[str, SensorConfig]:
        """Get all registered sensors."""
        return dict(self._sensors)
    
    def get_active_sensors(self) -> List[str]:
        """Get all active (online) sensors."""
        return [sid for sid, status in self._sensor_status.items() if status == SensorStatus.ONLINE]
    
    def get_sensor_summary(self) -> Dict[str, Any]:
        """Get a summary of all sensors in the registry."""
        return {
            "total_sensors": len(self._sensors),
            "active_sensors": len(self.get_active_sensors()),
            "sensor_types": {st.value: len(sids) for st, sids in self._sensor_types.items()},
            "sensors": {
                sid: {
                    "type": cfg.sensor_type.value,
                    "status": self._sensor_status.get(sid, SensorStatus.UNKNOWN).value,
                    "data_points": len(self._sensor_data.get(sid, [])),
                    "last_value": self._sensor_data[sid][-1].value if self._sensor_data.get(sid) else None,
                    "last_timestamp": self._sensor_data[sid][-1].timestamp if self._sensor_data.get(sid) else None,
                }
                for sid, cfg in self._sensors.items()
            }
        }
    
    def get_sensor_health(self, sensor_id: str) -> Dict[str, Any]:
        """Get health information for a specific sensor."""
        config = self._sensors.get(sensor_id)
        if not config:
            return {"error": "Sensor not found"}
        data = self._sensor_data.get(sensor_id, [])
        if not data:
            return {"sensor_id": sensor_id, "status": self._sensor_status.get(sensor_id, SensorStatus.UNKNOWN).value,
                    "health": "no_data", "data_points": 0}
        avg_quality = sum(d.quality for d in data) / len(data)
        health = "healthy" if avg_quality >= 0.5 else ("degraded" if avg_quality >= 0.2 else "critical")
        return {
            "sensor_id": sensor_id, "type": config.sensor_type.value,
            "status": self._sensor_status.get(sensor_id, SensorStatus.UNKNOWN).value,
            "health": health, "data_points": len(data), "avg_quality": avg_quality,
            "last_value": data[-1].value, "last_timestamp": data[-1].timestamp,
        }
    
    def clear_sensor_data(self, sensor_id: Optional[str] = None) -> None:
        """Clear sensor data history."""
        if sensor_id:
            self._sensor_data.pop(sensor_id, None)
        else:
            self._sensor_data.clear()
