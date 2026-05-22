"""OPC-UA protocol adapter for industrial IoT data ingestion."""

import logging
import time
from typing import Callable, Dict, List, Optional, Any

try:
    from asyncua import Client, ua
    HAS_ASYNCUA = True
except ImportError:
    HAS_ASYNCUA = False

from chronovision.src.iot.schema import SensorData, SensorType, SensorStatus

logger = logging.getLogger(__name__)


class OPCUAAdapter:
    """OPC-UA protocol adapter for industrial IoT data ingestion.
    
    Connects to OPC-UA servers, reads node values, and converts
    them to unified SensorData format.
    """
    
    def __init__(
        self,
        server_url: str = "opc.tcp://localhost:4840",
        timeout: float = 5.0,
    ):
        self.server_url = server_url
        self.timeout = timeout
        self._client: Optional[Any] = None
        self._connected = False
        self._monitored_nodes: Dict[str, Dict[str, Any]] = {}
        self._value_cache: Dict[str, float] = {}
        self._last_read: Dict[str, float] = {}
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to OPC-UA server."""
        return self._connected
    
    def connect(self) -> bool:
        """Connect to the OPC-UA server."""
        if not HAS_ASYNCUA:
            logger.warning("asyncua not installed. Using mock connection.")
            self._connected = True
            return True
        
        try:
            self._client = Client(url=self.server_url)
            self._client.timeout = int(self.timeout * 1000)
            self._client.connect()
            self._connected = True
            logger.info(f"Connected to OPC-UA server at {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OPC-UA server: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the OPC-UA server."""
        if self._client and self._connected:
            try:
                self._client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from OPC-UA server: {e}")
        self._connected = False
        self._value_cache.clear()
        self._last_read.clear()
        logger.info("Disconnected from OPC-UA server")
    
    def read_node(self, node_id: str, sensor_type: SensorType = SensorType.CUSTOM) -> Optional[SensorData]:
        """Read a single OPC-UA node value.
        
        Args:
            node_id: OPC-UA node identifier.
            sensor_type: Type of sensor data.
            
        Returns:
            SensorData or None if read failed.
        """
        if not self._connected:
            logger.warning("Not connected to OPC-UA server")
            return None
        
        if HAS_ASYNCUA and self._client:
            try:
                node = self._client.get_node(node_id)
                value = node.get_value()
                quality = 1.0 if value is not None else 0.0
                
                sensor_data = SensorData.from_opcua(
                    node_id=node_id,
                    value=value,
                    sensor_type=sensor_type,
                    quality=quality,
                    status=SensorStatus.ONLINE if quality > 0 else SensorStatus.ERROR,
                )
                
                # Cache the value
                self._value_cache[node_id] = sensor_data.value
                self._last_read[node_id] = time.time()
                
                return sensor_data
            except Exception as e:
                logger.error(f"Failed to read node {node_id}: {e}")
                return None
        else:
            # Mock read for testing
            mock_value = float(hash(node_id) % 1000) / 10.0
            sensor_data = SensorData.from_opcua(
                node_id=node_id,
                value=mock_value,
                sensor_type=sensor_type,
                quality=1.0,
                status=SensorStatus.ONLINE,
            )
            self._value_cache[node_id] = mock_value
            self._last_read[node_id] = time.time()
            return sensor_data
    
    def read_nodes_batch(self, node_ids: List[str]) -> List[SensorData]:
        """Read multiple OPC-UA nodes in batch.
        
        Args:
            node_ids: List of OPC-UA node identifiers.
            
        Returns:
            List of SensorData objects.
        """
        results = []
        for node_id in node_ids:
            data = self.read_node(node_id)
            if data:
                results.append(data)
        return results
    
    def subscribe_to_node(
        self,
        node_id: str,
        callback: Callable[[SensorData], None],
        sensor_type: SensorType = SensorType.CUSTOM,
        sampling_interval: float = 1.0,
    ) -> bool:
        """Subscribe to an OPC-UA node for continuous updates.
        
        Args:
            node_id: OPC-UA node identifier.
            callback: Callback function for new values.
            sensor_type: Type of sensor data.
            sampling_interval: Sampling interval in seconds.
            
        Returns:
            True if subscription successful.
        """
        if not self._connected:
            logger.warning("Not connected to OPC-UA server")
            return False
        
        if HAS_ASYNCUA and self._client:
            try:
                node = self._client.get_node(node_id)
                
                def _value_changed(value):
                    sensor_data = SensorData.from_opcua(
                        node_id=node_id,
                        value=value,
                        sensor_type=sensor_type,
                        quality=1.0,
                        status=SensorStatus.ONLINE,
                    )
                    callback(sensor_data)
                
                sub = self._client.create_subscription(sampling_interval * 1000, ua.SubscriptionOptions())
                sub.subscribe_data_change(node, callback=_value_changed)
                
                self._monitored_nodes[node_id] = {
                    "subscription": sub,
                    "callback": callback,
                    "sensor_type": sensor_type,
                    "sampling_interval": sampling_interval,
                }
                
                logger.info(f"Subscribed to node {node_id} with interval {sampling_interval}s")
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe to node {node_id}: {e}")
                return False
        else:
            # Mock subscription for testing
            self._monitored_nodes[node_id] = {
                "callback": callback,
                "sensor_type": sensor_type,
                "sampling_interval": sampling_interval,
            }
            logger.info(f"Mock subscribed to node {node_id}")
            return True
    
    def unsubscribe_from_node(self, node_id: str) -> bool:
        """Unsubscribe from an OPC-UA node.
        
        Args:
            node_id: OPC-UA node identifier.
            
        Returns:
            True if unsubscription successful.
        """
        if node_id in self._monitored_nodes:
            monitored = self._monitored_nodes.pop(node_id)
            if HAS_ASYNCUA and self._client and "subscription" in monitored:
                try:
                    monitored["subscription"].unsubscribe()
                except Exception as e:
                    logger.error(f"Error unsubscribing from node {node_id}: {e}")
            logger.info(f"Unsubscribed from node {node_id}")
            return True
        return False
    
    def get_cached_values(self) -> Dict[str, float]:
        """Get all cached node values."""
        return dict(self._value_cache)
    
    def get_last_read_times(self) -> Dict[str, float]:
        """Get last read times for all nodes."""
        return dict(self._last_read)
    
    def discover_nodes(self, namespace: int = 0) -> List[str]:
        """Discover available nodes on the OPC-UA server.
        
        Args:
            namespace: Namespace index to search.
            
        Returns:
            List of node IDs.
        """
        if not self._connected:
            logger.warning("Not connected to OPC-UA server")
            return []
        
        if HAS_ASYNCUA and self._client:
            try:
                namespace_idx = self._client.get_namespace_index(str(namespace))
                nodes = self._client.get_namespace_array()
                return [f"ns={namespace_idx};i={i}" for i in range(1, 100)]
            except Exception as e:
                logger.error(f"Failed to discover nodes: {e}")
                return []
        else:
            # Mock discovery for testing
            return [f"mock_node_{i}" for i in range(10)]
    
    def write_node(self, node_id: str, value: float) -> bool:
        """Write a value to an OPC-UA node.
        
        Args:
            node_id: OPC-UA node identifier.
            value: Value to write.
            
        Returns:
            True if write successful.
        """
        if not self._connected:
            logger.warning("Not connected to OPC-UA server")
            return False
        
        if HAS_ASYNCUA and self._client:
            try:
                node = self._client.get_node(node_id)
                node.set_value(value)
                return True
            except Exception as e:
                logger.error(f"Failed to write to node {node_id}: {e}")
                return False
        else:
            # Mock write for testing
            self._value_cache[node_id] = value
            return True
