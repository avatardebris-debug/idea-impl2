"""
message_bus.py — Inter-agent communication for the OSINT Corp2 pipeline.

Provides Message class, MessageBus for send/receive/broadcast, and typed
message types for the pipeline.
"""
from __future__ import annotations

import json
import pathlib
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------

MSG_SEED_IDEA = "seed_idea"
MSG_TASK_COMPLETE = "task_complete"
MSG_REVIEW_REQUEST = "review_request"
MSG_REVIEW_FEEDBACK = "review_feedback"
MSG_HARVEST_READY = "harvest_ready"
MSG_ERROR = "error"
MSG_HEARTBEAT = "heartbeat"

ALL_MSG_TYPES = frozenset([
    MSG_SEED_IDEA, MSG_TASK_COMPLETE, MSG_REVIEW_REQUEST,
    MSG_REVIEW_FEEDBACK, MSG_HARVEST_READY, MSG_ERROR, MSG_HEARTBEAT,
])


# ---------------------------------------------------------------------------
# Message class
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A message between pipeline agents."""
    from_agent: str
    to_agent: str
    type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    msg_id: str = ""

    def __post_init__(self):
        if not self.msg_id:
            self.msg_id = f"{self.from_agent}->{self.to_agent}:{self.type}:{int(self.timestamp)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "msg_id": self.msg_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @classmethod
    def create(cls, from_agent: str, to_agent: str, type: str, payload: Dict[str, Any]) -> "Message":
        """Factory method for creating messages."""
        if type not in ALL_MSG_TYPES:
            raise ValueError(f"Unknown message type: {type}. Must be one of {ALL_MSG_TYPES}")
        return cls(
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            payload=payload,
        )

    def __repr__(self):
        return f"Message({self.from_agent}->{self.to_agent} [{self.type}])"


# ---------------------------------------------------------------------------
# MessageBus — in-memory message bus
# ---------------------------------------------------------------------------

class MessageBus:
    """Thread-safe message bus for inter-agent communication."""

    def __init__(self):
        self._lock = threading.Lock()
        self._queues: Dict[str, List[Message]] = {}  # agent_name -> [Message]
        self._broadcast_log: List[Message] = []
        self._agents: Set[str] = set()

    def register_agent(self, agent_name: str) -> None:
        """Register an agent with the bus."""
        with self._lock:
            self._agents.add(agent_name)
            if agent_name not in self._queues:
                self._queues[agent_name] = []

    def send(self, message: Message) -> str:
        """Send a message to a specific agent. Returns status string."""
        with self._lock:
            if message.to_agent not in self._queues:
                self._queues[message.to_agent] = []
            self._queues[message.to_agent].append(message)
            return f"OK: Sent {message.type} to {message.to_agent}"

    def receive(self, agent_name: str) -> Optional[Message]:
        """Receive the next message for an agent. Returns None if queue is empty."""
        with self._lock:
            if agent_name not in self._queues:
                return None
            if not self._queues[agent_name]:
                return None
            return self._queues[agent_name].pop(0)

    def wait_for(self, agent_name: str, msg_type: Optional[str] = None, timeout: float = 30.0) -> Optional[Message]:
        """Blocking receive with timeout. Returns message or None."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.receive(agent_name)
            if msg is not None:
                if msg_type is None or msg.type == msg_type:
                    return msg
            time.sleep(0.05)
        return None

    def broadcast(self, msg_type: str, payload: Dict[str, Any], exclude: Optional[Set[str]] = None) -> str:
        """Send a message to all registered agents."""
        if exclude is None:
            exclude = set()
        msg = Message.create("orchestrator", "all", msg_type, payload)
        with self._lock:
            for agent in self._agents:
                if agent not in exclude:
                    if agent not in self._queues:
                        self._queues[agent] = []
                    self._queues[agent].append(msg)
            self._broadcast_log.append(msg)
        return f"OK: Broadcast {msg_type} to {len(self._agents) - len(exclude)} agents"

    def get_queue_size(self, agent_name: str) -> int:
        """Get the number of pending messages for an agent."""
        with self._lock:
            return len(self._queues.get(agent_name, []))

    def get_all_queues(self) -> Dict[str, int]:
        """Get all queue sizes."""
        with self._lock:
            return {name: len(msgs) for name, msgs in self._queues.items()}

    def clear_queue(self, agent_name: str) -> int:
        """Clear all pending messages for an agent. Returns count cleared."""
        with self._lock:
            count = len(self._queues.get(agent_name, []))
            self._queues[agent_name] = []
            return count

    def list_agents(self) -> List[str]:
        """List all registered agents."""
        with self._lock:
            return sorted(self._agents)


# ---------------------------------------------------------------------------
# File-backed message bus (for persistence across restarts)
# ---------------------------------------------------------------------------

class FileMessageBus(MessageBus):
    """MessageBus backed by files on disk for persistence."""

    def __init__(self, queue_dir: str = ".pipeline/queues"):
        super().__init__()
        self._queue_dir = pathlib.Path(queue_dir)
        self._queue_dir.mkdir(parents=True, exist_ok=True)

    def send(self, message: Message) -> str:
        """Send and persist a message to disk."""
        result = super().send(message)
        # Persist to file
        agent_dir = self._queue_dir / message.to_agent
        agent_dir.mkdir(parents=True, exist_ok=True)
        msg_file = agent_dir / f"{message.msg_id}.json"
        msg_file.write_text(json.dumps(message.to_dict(), indent=2))
        return result

    def receive(self, agent_name: str) -> Optional[Message]:
        """Receive and remove a message from disk."""
        msg = super().receive(agent_name)
        if msg is not None:
            # Remove from disk
            msg_file = self._queue_dir / agent_name / f"{msg.msg_id}.json"
            if msg_file.exists():
                msg_file.unlink()
        return msg

    def broadcast(self, msg_type: str, payload: Dict[str, Any], exclude: Optional[Set[str]] = None) -> str:
        """Broadcast and persist messages to disk."""
        result = super().broadcast(msg_type, payload, exclude)
        # Persist broadcast log
        log_file = self._queue_dir / "_broadcast_log.json"
        log_file.write_text(json.dumps(self._broadcast_log[-100:], indent=2))
        return result
