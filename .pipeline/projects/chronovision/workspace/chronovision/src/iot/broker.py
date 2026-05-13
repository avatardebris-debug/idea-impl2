"""MQTT broker client with subscribe/publish functionality."""

import logging
import time
import threading
from typing import Callable, Dict, List, Optional, Any
from collections import defaultdict

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

logger = logging.getLogger(__name__)


class MQTTBroker:
    """MQTT broker client for IoT data ingestion.
    
    Handles connection to MQTT broker, subscribing to topics,
    and publishing sensor events.
    """
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = 60,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"chronovision-{int(time.time())}"
        self.username = username
        self.password = password
        self.keepalive = keepalive
        
        self._client: Optional[Any] = None
        self._connected = False
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 10000
        self._lock = threading.Lock()
        
        # Callbacks
        self._on_connect_callback: Optional[Callable] = None
        self._on_disconnect_callback: Optional[Callable] = None
        self._on_message_callback: Optional[Callable] = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        if not HAS_MQTT:
            logger.warning("paho-mqtt not installed. Using mock connection.")
            self._connected = True
            if self._on_connect_callback:
                self._on_connect_callback(self)
            return True
        
        try:
            self._client = mqtt.Client(client_id=self.client_id)
            
            if self.username and self.password:
                self._client.username_pw_set(self.username, self.password)
            
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            self._client.connect(self.broker_host, self.broker_port, self.keepalive)
            self._client.loop_start()
            self._connected = True
            
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            if self._on_connect_callback:
                self._on_connect_callback(self)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self._client and self._connected:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
        self._connected = False
        logger.info("Disconnected from MQTT broker")
    
    def subscribe(self, topic: str, callback: Optional[Callable] = None) -> bool:
        """Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to.
            callback: Optional callback function for messages.
            
        Returns:
            True if subscription successful.
        """
        if not self._connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        if HAS_MQTT and self._client:
            try:
                self._client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to topic {topic}: {e}")
                return False
        
        if callback:
            self._subscribers[topic].append(callback)
        
        return True
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from an MQTT topic."""
        if not self._connected:
            return False
        
        if HAS_MQTT and self._client:
            try:
                self._client.unsubscribe(topic)
            except Exception as e:
                logger.error(f"Failed to unsubscribe from topic {topic}: {e}")
                return False
        
        self._subscribers.pop(topic, None)
        return True
    
    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic to publish to.
            payload: Message payload.
            qos: Quality of service level.
            retain: Whether to retain the message.
            
        Returns:
            True if publish successful.
        """
        if not self._connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        if HAS_MQTT and self._client:
            try:
                self._client.publish(topic, str(payload), qos=qos, retain=retain)
                return True
            except Exception as e:
                logger.error(f"Failed to publish to topic {topic}: {e}")
                return False
        
        # Mock publish for testing
        self._message_buffer.append({
            "topic": topic,
            "payload": payload,
            "timestamp": time.time(),
        })
        if len(self._message_buffer) > self._max_buffer_size:
            self._message_buffer.pop(0)
        return True
    
    def get_buffered_messages(self) -> List[Dict[str, Any]]:
        """Get messages from the buffer (for testing)."""
        with self._lock:
            return list(self._message_buffer)
    
    def clear_buffer(self) -> None:
        """Clear the message buffer."""
        with self._lock:
            self._message_buffer.clear()
    
    # Internal callbacks
    def _on_connect(self, client, userdata, flags, rc):
        """Internal MQTT connect callback."""
        self._connected = True
        logger.info("MQTT connected")
        if self._on_connect_callback:
            self._on_connect_callback(self)
    
    def _on_disconnect(self, client, userdata, rc):
        """Internal MQTT disconnect callback."""
        self._connected = False
        logger.info("MQTT disconnected")
        if self._on_disconnect_callback:
            self._on_disconnect_callback(self)
    
    def _on_message(self, client, userdata, msg):
        """Internal MQTT message callback."""
        topic = msg.topic
        payload = msg.payload.decode() if isinstance(msg.payload, bytes) else msg.payload
        
        # Store in buffer
        with self._lock:
            self._message_buffer.append({
                "topic": topic,
                "payload": payload,
                "timestamp": time.time(),
            })
            if len(self._message_buffer) > self._max_buffer_size:
                self._message_buffer.pop(0)
        
        # Call subscribers
        for callback in self._subscribers.get(topic, []):
            try:
                callback(topic, payload)
            except Exception as e:
                logger.error(f"Error in message callback for topic {topic}: {e}")
        
        if self._on_message_callback:
            try:
                self._on_message_callback(topic, payload)
            except Exception as e:
                logger.error(f"Error in global message callback: {e}")
    
    def set_connect_callback(self, callback: Callable) -> None:
        """Set callback for connection events."""
        self._on_connect_callback = callback
    
    def set_disconnect_callback(self, callback: Callable) -> None:
        """Set callback for disconnection events."""
        self._on_disconnect_callback = callback
    
    def set_message_callback(self, callback: Callable) -> None:
        """Set global message callback."""
        self._on_message_callback = callback
