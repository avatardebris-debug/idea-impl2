"""Memory management for email tool agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from email_tool.agent.base import AgentResult


class MemoryManager:
    """
    Manages persistent memory storage for the email tool agent.
    
    Provides functionality to store, retrieve, and manage key-value pairs
    along with an action history. Data is persisted to JSON files.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the memory manager.
        
        Args:
            storage_path: Path to store memory files. Defaults to
                         ~/.email_tool/memory directory.
        """
        if storage_path is None:
            storage_path = Path.home() / ".email_tool" / "memory"
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.storage_path / "memory.json"
        self.history_file = self.storage_path / "history.json"
        
        self._memory: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        
        self._load_memory()
        self._load_history()
    
    def _load_memory(self) -> None:
        """Load memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self._memory = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._memory = {}
    
    def _save_memory(self) -> None:
        """Save memory to file."""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self._memory, f, indent=2, ensure_ascii=False)
    
    def _load_history(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._history = []
    
    def _save_history(self) -> None:
        """Save history to file."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)
    
    def store(self, key: str, value: Any) -> AgentResult:
        """
        Store a value with the given key.
        
        Args:
            key: The key to store the value under.
            value: The value to store (any JSON-serializable type).
        
        Returns:
            AgentResult with success status and stored data.
        """
        self._memory[key] = value
        self._save_memory()
        
        return AgentResult(
            success=True,
            data={
                "key": key,
                "value": value
            },
            metadata={
                "operation": "store",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value by key.
        
        Args:
            key: The key to retrieve.
            default: Default value if key doesn't exist.
        
        Returns:
            The stored value or default if not found.
        """
        return self._memory.get(key, default)
    
    def delete(self, key: str) -> AgentResult:
        """
        Delete a value by key.
        
        Args:
            key: The key to delete.
        
        Returns:
            AgentResult with success status.
        """
        if key not in self._memory:
            return AgentResult(
                success=False,
                error_message=f"Key '{key}' not found in memory"
            )
        
        del self._memory[key]
        self._save_memory()
        
        return AgentResult(
            success=True,
            data={
                "key": key
            },
            metadata={
                "operation": "delete",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_history_entry(self, entry: Dict[str, Any]) -> AgentResult:
        """
        Add an entry to the action history.
        
        Args:
            entry: Dictionary containing action information.
        
        Returns:
            AgentResult with success status and added entry.
        """
        entry_with_timestamp = {
            **entry,
            "timestamp": datetime.now().isoformat()
        }
        
        self._history.append(entry_with_timestamp)
        self._save_history()
        
        return AgentResult(
            success=True,
            data=entry_with_timestamp,
            metadata={
                "operation": "add_history",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get action history entries.
        
        Args:
            limit: Maximum number of entries to return (most recent).
        
        Returns:
            List of history entries, newest first.
        """
        if limit is None:
            return list(self._history)
        
        return list(self._history[-limit:])
    
    def clear_history(self) -> AgentResult:
        """
        Clear all history entries.
        
        Returns:
            AgentResult with success status.
        """
        self._history = []
        self._save_history()
        
        return AgentResult(
            success=True,
            metadata={
                "operation": "clear_history",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_all_memory(self) -> Dict[str, Any]:
        """
        Get all stored memory.
        
        Returns:
            Dictionary of all key-value pairs.
        """
        return dict(self._memory)
    
    def clear_memory(self) -> AgentResult:
        """
        Clear all stored memory.
        
        Returns:
            AgentResult with success status.
        """
        self._memory = {}
        self._save_memory()
        
        return AgentResult(
            success=True,
            metadata={
                "operation": "clear_memory",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current memory status.
        
        Returns:
            Dictionary with memory statistics.
        """
        return {
            "storage_path": str(self.storage_path),
            "memory_keys": list(self._memory.keys()),
            "memory_count": len(self._memory),
            "history_count": len(self._history)
        }
