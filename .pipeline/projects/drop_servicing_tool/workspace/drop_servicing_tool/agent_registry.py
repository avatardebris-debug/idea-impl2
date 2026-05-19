"""Agent Registry for multi-agent SOP execution.

Manages registration, listing, and deletion of agents with metadata
persistence to the filesystem.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentRegistry:
    """In-memory + filesystem-backed agent registry."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base = base_dir or Path(os.environ.get("DST_AGENTS_DIR", "."))
        self._agents_dir = self._base / "agents"
        self._agents_dir.mkdir(parents=True, exist_ok=True)
        # In-memory store (name -> client)
        self._agents: Dict[str, Any] = {}
        # Metadata store (name -> metadata dict)
        self._metadata: Dict[str, Dict[str, Any]] = {}
        # Load existing agents from disk
        self._load_existing_agents()
    
    def _load_existing_agents(self) -> None:
        """Load existing agents from disk."""
        if not self._agents_dir.exists():
            return
        
        for agent_file in self._agents_dir.glob("*.json"):
            try:
                data = json.loads(agent_file.read_text(encoding="utf-8"))
                name = data.get("name")
                if name:
                    # Load metadata
                    self._metadata[name] = data.get("metadata", {})
                    # Load client if present (for backward compatibility)
                    client = data.get("client")
                    if client is not None:
                        self._agents[name] = client
                    else:
                        # Create placeholder client (client is not persisted)
                        self._agents[name] = {"type": "loaded_from_disk"}
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                continue

    # ---- Registration ----

    def register_agent(
        self,
        name: str,
        client: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an agent with a client and optional metadata."""
        if not name:
            raise ValueError("Agent name cannot be empty")
        self._agents[name] = client
        self._metadata[name] = metadata or {}
        # Persist to disk (metadata only, client is not persisted)
        agent_file = self._agents_dir / f"{name}.json"
        agent_data = {
            "name": name,
            "metadata": self._metadata[name],
        }
        agent_file.write_text(json.dumps(agent_data, indent=2), encoding="utf-8")

    # ---- Retrieval ----

    def get_agent(self, name: str) -> Any:
        """Get a registered agent by name.

        Raises:
            KeyError:  If no agent with *name* is registered.
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in registry.")
        return self._agents[name]

    # ---- Listing ----

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    # ---- Deletion ----

    def delete_agent(self, name: str) -> bool:
        """Delete an agent. Returns True if deleted, False if not found."""
        if name not in self._agents:
            return False
        del self._agents[name]
        if name in self._metadata:
            del self._metadata[name]
        # Remove from disk
        agent_file = self._agents_dir / f"{name}.json"
        agent_file.unlink(missing_ok=True)
        return True

    # ---- Metadata access ----

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for an agent."""
        if name not in self._metadata:
            raise KeyError(f"Agent '{name}' not found.")
        return self._metadata[name]

    def update_metadata(self, name: str, metadata: Dict[str, Any]) -> None:
        """Update metadata for an agent."""
        if name not in self._metadata:
            raise KeyError(f"Agent '{name}' not found.")
        self._metadata[name] = metadata
        # Persist
        agent_file = self._agents_dir / f"{name}.json"
        agent_data = {
            "name": name,
            "metadata": self._metadata[name],
        }
        agent_file.write_text(json.dumps(agent_data, indent=2), encoding="utf-8")

    # ---- Router creation ----

    def get_router(self) -> "LLMClientRouter":
        """Create an LLMClientRouter populated with all registered agents."""
        from .agent_router import LLMClientRouter

        router = LLMClientRouter()
        for name, client in self._agents.items():
            router.register_agent(name, client)
        return router
