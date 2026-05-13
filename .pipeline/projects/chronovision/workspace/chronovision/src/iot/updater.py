"""IoT updater that integrates sensor data into the StateSpace."""

import logging
from typing import Dict, List, Optional, Any

from chronovision.src.iot.schema import SensorData, SensorType, SensorStatus
from chronovision.src.iot.registry import SensorRegistry
from chronovision.src.iot.streaming import StreamingConnector
from chronovision.src.state_space import StateSpace

logger = logging.getLogger(__name__)


class IoTUpdater:
    """Updates the StateSpace with real-time IoT sensor data.
    
    Acts as the bridge between the IoT subsystem and the StateSpace,
    ensuring that sensor readings are properly integrated into the
    spatial model.
    """
    
    def __init__(
        self,
        state_space: StateSpace,
        sensor_registry: Optional[SensorRegistry] = None,
        streaming_connector: Optional[StreamingConnector] = None,
    ):
        self.state_space = state_space
        self.sensor_registry = sensor_registry or SensorRegistry()
        self.streaming_connector = streaming_connector or StreamingConnector()
        
        self._initialized = False
        self._update_count = 0
        self._error_count = 0
    
    @property
    def is_initialized(self) -> bool:
        """Check if the updater is initialized."""
        return self._initialized
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get updater statistics."""
        return {
            "update_count": self._update_count,
            "error_count": self._error_count,
        }
    
    def initialize(self) -> bool:
        """Initialize the IoT updater.
        
        Returns:
            True if initialization successful.
        """
        if self._initialized:
            logger.warning("IoT updater already initialized")
            return True
        
        try:
            # Connect streaming connector to sensor registry
            self.streaming_connector.add_callback(self._on_sensor_data)
            
            # Start streaming if not already running
            if not self.streaming_connector.is_running:
                self.streaming_connector.start()
            
            self._initialized = True
            logger.info("IoT updater initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize IoT updater: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the IoT updater."""
        if self.streaming_connector.is_running:
            self.streaming_connector.stop()
        self._initialized = False
        logger.info("IoT updater shutdown")
    
    def update_from_sensor_data(self, sensor_data: SensorData) -> bool:
        """Update the StateSpace with sensor data.
        
        Args:
            sensor_data: Sensor data to process.
            
        Returns:
            True if update successful.
        """
        try:
            # Validate sensor data
            if not sensor_data or not sensor_data.sensor_id:
                logger.warning("Invalid sensor data received")
                return False
            
            # Update registry
            self.sensor_registry.add_sensor_data(sensor_data)
            
            # Update StateSpace based on sensor type
            if sensor_data.sensor_type == SensorType.LOCATION:
                self._update_location(sensor_data)
            elif sensor_data.sensor_type == SensorType.PROXIMITY:
                self._update_proximity(sensor_data)
            elif sensor_data.sensor_type == SensorType.TEMPERATURE:
                self._update_temperature(sensor_data)
            elif sensor_data.sensor_type == SensorType.PRESSURE:
                self._update_pressure(sensor_data)
            else:
                # Generic update for other sensor types
                self._update_generic(sensor_data)
            
            self._update_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error updating StateSpace with sensor data: {e}")
            self._error_count += 1
            return False
    
    def _on_sensor_data(self, sensor_data: SensorData) -> None:
        """Callback for incoming sensor data."""
        self.update_from_sensor_data(sensor_data)
    
    def _update_location(self, sensor_data: SensorData) -> None:
        """Update location information in the StateSpace."""
        if hasattr(sensor_data, 'coordinates') and sensor_data.coordinates:
            self.state_space.update_location(
                sensor_id=sensor_data.sensor_id,
                coordinates=sensor_data.coordinates,
                timestamp=sensor_data.timestamp,
            )
            logger.debug(f"Updated location for sensor {sensor_data.sensor_id}")
    
    def _update_proximity(self, sensor_data: SensorData) -> None:
        """Update proximity information in the StateSpace."""
        if hasattr(sensor_data, 'distance') and sensor_data.distance is not None:
            self.state_space.update_proximity(
                sensor_id=sensor_data.sensor_id,
                distance=sensor_data.distance,
                timestamp=sensor_data.timestamp,
            )
            logger.debug(f"Updated proximity for sensor {sensor_data.sensor_id}")
    
    def _update_temperature(self, sensor_data: SensorData) -> None:
        """Update temperature information in the StateSpace."""
        self.state_space.update_environmental(
            sensor_id=sensor_data.sensor_id,
            temperature=sensor_data.value,
            timestamp=sensor_data.timestamp,
        )
        logger.debug(f"Updated temperature for sensor {sensor_data.sensor_id}")
    
    def _update_pressure(self, sensor_data: SensorData) -> None:
        """Update pressure information in the StateSpace."""
        self.state_space.update_environmental(
            sensor_id=sensor_data.sensor_id,
            pressure=sensor_data.value,
            timestamp=sensor_data.timestamp,
        )
        logger.debug(f"Updated pressure for sensor {sensor_data.sensor_id}")
    
    def _update_generic(self, sensor_data: SensorData) -> None:
        """Update generic sensor data in the StateSpace."""
        self.state_space.update_environmental(
            sensor_id=sensor_data.sensor_id,
            temperature=sensor_data.value,  # Use value as generic metric
            timestamp=sensor_data.timestamp,
        )
        logger.debug(f"Updated generic data for sensor {sensor_data.sensor_id}")
    
    def get_sensor_summary(self) -> Dict[str, Any]:
        """Get a summary of all sensors."""
        return self.sensor_registry.get_sensor_summary()
    
    def get_sensor_health(self, sensor_id: str) -> Dict[str, Any]:
        """Get health information for a specific sensor."""
        return self.sensor_registry.get_sensor_health(sensor_id)
    
    def register_sensor(self, config: Any) -> bool:
        """Register a new sensor.
        
        Args:
            config: Sensor configuration.
            
        Returns:
            True if registration successful.
        """
        return self.sensor_registry.register_sensor(config)
    
    def unregister_sensor(self, sensor_id: str) -> bool:
        """Unregister a sensor.
        
        Args:
            sensor_id: Sensor identifier.
            
        Returns:
            True if unregistration successful.
        """
        return self.sensor_registry.unregister_sensor(sensor_id)
