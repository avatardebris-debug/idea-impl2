"""Streaming connector for real-time IoT data ingestion."""

import logging
import time
import threading
from typing import Callable, Dict, List, Optional, Any
from collections import deque

from chronovision.src.iot.schema import SensorData, SensorType, SensorStatus
from chronovision.src.iot.broker import MQTTBroker
from chronovision.src.iot.protocol_opcua import OPCUAAdapter

logger = logging.getLogger(__name__)


class StreamingConnector:
    """Real-time streaming connector for IoT data.
    
    Coordinates data ingestion from both MQTT and OPC-UA sources,
    normalizes data into SensorData format, and routes to the
    StateSpace updater.
    """
    
    def __init__(
        self,
        mqtt_broker: Optional[MQTTBroker] = None,
        opcua_adapter: Optional[OPCUAAdapter] = None,
        max_buffer_size: int = 1000,
    ):
        self.mqtt_broker = mqtt_broker
        self.opcua_adapter = opcua_adapter
        self.max_buffer_size = max_buffer_size
        
        self._data_buffer: deque = deque(maxlen=max_buffer_size)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[SensorData], None]] = []
        self._sensor_count = 0
        self._data_count = 0
        self._error_count = 0
        self._lock = threading.Lock()
    
    @property
    def is_running(self) -> bool:
        """Check if streaming is active."""
        return self._running
    
    @property
    def buffer_size(self) -> int:
        """Current buffer size."""
        return len(self._data_buffer)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get streaming statistics."""
        return {
            "sensor_count": self._sensor_count,
            "data_count": self._data_count,
            "error_count": self._error_count,
            "buffer_size": self.buffer_size,
        }
    
    def start(self) -> bool:
        """Start the streaming connector."""
        if self._running:
            logger.warning("Streaming connector already running")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        logger.info("Streaming connector started")
        return True
    
    def stop(self) -> None:
        """Stop the streaming connector."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Streaming connector stopped")
    
    def add_callback(self, callback: Callable[[SensorData], None]) -> None:
        """Add a callback for processed sensor data."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SensorData], None]) -> bool:
        """Remove a callback for processed sensor data."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False
    
    def ingest_mqtt_data(self, topic: str, payload: Any) -> Optional[SensorData]:
        """Ingest data from MQTT source.
        
        Args:
            topic: MQTT topic.
            payload: Message payload.
            
        Returns:
            SensorData if successful, None otherwise.
        """
        try:
            sensor_data = SensorData.from_mqtt(topic, payload)
            self._add_to_buffer(sensor_data)
            self._data_count += 1
            return sensor_data
        except Exception as e:
            logger.error(f"Error ingesting MQTT data from topic {topic}: {e}")
            self._error_count += 1
            return None
    
    def ingest_opcua_data(self, node_id: str, value: Any, sensor_type: SensorType = SensorType.CUSTOM) -> Optional[SensorData]:
        """Ingest data from OPC-UA source.
        
        Args:
            node_id: OPC-UA node identifier.
            value: Node value.
            sensor_type: Type of sensor data.
            
        Returns:
            SensorData if successful, None otherwise.
        """
        try:
            sensor_data = SensorData.from_opcua(
                node_id=node_id,
                value=value,
                sensor_type=sensor_type,
                quality=1.0,
                status=SensorStatus.ONLINE,
            )
            self._add_to_buffer(sensor_data)
            self._data_count += 1
            return sensor_data
        except Exception as e:
            logger.error(f"Error ingesting OPC-UA data from node {node_id}: {e}")
            self._error_count += 1
            return None
    
    def ingest_sensor_data(self, sensor_data: SensorData) -> None:
        """Ingest pre-constructed SensorData.
        
        Args:
            sensor_data: SensorData object to ingest.
        """
        self._add_to_buffer(sensor_data)
        self._data_count += 1
    
    def get_buffered_data(self) -> List[SensorData]:
        """Get all buffered sensor data."""
        with self._lock:
            return list(self._data_buffer)
    
    def clear_buffer(self) -> None:
        """Clear the data buffer."""
        with self._lock:
            self._data_buffer.clear()
    
    def flush_buffer(self) -> List[SensorData]:
        """Get and clear all buffered sensor data."""
        with self._lock:
            data = list(self._data_buffer)
            self._data_buffer.clear()
        return data
    
    def _add_to_buffer(self, sensor_data: SensorData) -> None:
        """Add sensor data to the buffer."""
        with self._lock:
            self._data_buffer.append(sensor_data)
            if sensor_data.sensor_id not in [s.sensor_id for s in self._data_buffer]:
                self._sensor_count += 1
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(sensor_data)
            except Exception as e:
                logger.error(f"Error in sensor data callback: {e}")
    
    def _stream_loop(self) -> None:
        """Main streaming loop."""
        while self._running:
            try:
                # Process buffered data
                with self._lock:
                    data = list(self._data_buffer)
                
                for sensor_data in data:
                    # Process each sensor data point
                    self._process_sensor_data(sensor_data)
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                time.sleep(1.0)
    
    def _process_sensor_data(self, sensor_data: SensorData) -> None:
        """Process a single sensor data point."""
        # Validate data quality
        if sensor_data.quality < 0.5:
            logger.warning(f"Low quality data from sensor {sensor_data.sensor_id}")
            return
        
        # Route to appropriate handler based on sensor type
        if sensor_data.sensor_type in [SensorType.LOCATION, SensorType.PROXIMITY]:
            # Location/proximity data might trigger alerts
            pass
        elif sensor_data.sensor_type in [SensorType.TEMPERATURE, SensorType.PRESSURE]:
            # Environmental data might need threshold checking
            pass
        # Other sensor types are processed generically
    
    def get_sensor_summary(self) -> Dict[str, Any]:
        """Get a summary of all sensors in the buffer."""
        with self._lock:
            sensors = {}
            for data in self._data_buffer:
                if data.sensor_id not in sensors:
                    sensors[data.sensor_id] = {
                        "type": data.sensor_type.value,
                        "last_value": data.value,
                        "last_timestamp": data.timestamp,
                        "quality": data.quality,
                        "status": data.status.value,
                        "count": 1,
                    }
                else:
                    sensors[data.sensor_id]["count"] += 1
                    sensors[data.sensor_id]["last_value"] = data.value
                    sensors[data.sensor_id]["last_timestamp"] = data.timestamp
            
            return {
                "total_sensors": len(sensors),
                "total_data_points": self._data_count,
                "sensors": sensors,
            }
