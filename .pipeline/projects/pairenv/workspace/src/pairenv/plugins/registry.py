"""
Plugin registry for managing loaded plugins, versioning, and lifecycle.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from collections import defaultdict

from .base import PluginABC, PluginState

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Manages the lifecycle of loaded plugins.

    Tracks plugin state (loaded, active, error, disabled) and supports hot-reload.
    """

    def __init__(self):
        self._plugins: Dict[str, PluginABC] = {}
        self._states: Dict[str, PluginState] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._version_map: Dict[str, str] = {}

    @property
    def plugins(self) -> Dict[str, PluginABC]:
        return dict(self._plugins)

    @property
    def states(self) -> Dict[str, PluginState]:
        return dict(self._states)

    def register(self, plugin: PluginABC, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register a plugin instance."""
        name = plugin.name
        if name in self._plugins:
            logger.warning("Plugin '%s' already registered, replacing.", name)
        self._plugins[name] = plugin
        self._states[name] = PluginState.LOADED
        self._version_map[name] = plugin.version
        if metadata:
            self._metadata[name] = metadata
        logger.info("Registered plugin '%s' v%s", name, plugin.version)
        return True

    def activate(self, name: str) -> bool:
        """Activate a loaded plugin."""
        if name not in self._plugins:
            logger.error("Plugin '%s' not found.", name)
            return False
        try:
            self._plugins[name].connect()
            self._states[name] = PluginState.ACTIVE
            logger.info("Activated plugin '%s'", name)
            return True
        except Exception as e:
            self._states[name] = PluginState.ERROR
            logger.error("Failed to activate plugin '%s': %s", name, e)
            return False

    def deactivate(self, name: str) -> bool:
        """Deactivate a plugin."""
        if name not in self._plugins:
            return False
        try:
            self._plugins[name].disconnect()
            self._states[name] = PluginState.DISABLED
            logger.info("Deactivated plugin '%s'", name)
            return True
        except Exception as e:
            logger.error("Failed to deactivate plugin '%s': %s", name, e)
            return False

    def reload(self, name: str) -> bool:
        """Hot-reload a plugin by deactivating and reactivating."""
        if name not in self._plugins:
            return False
        self.deactivate(name)
        return self.activate(name)

    def get(self, name: str) -> Optional[PluginABC]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_state(self, name: str) -> Optional[PluginState]:
        """Get the state of a plugin."""
        return self._states.get(name)

    def get_capabilities(self, name: str) -> Optional[Dict[str, Any]]:
        """Get capabilities of a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            return plugin.get_capabilities()
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins with their state and metadata."""
        result = []
        for name in self._plugins:
            entry = {
                "name": name,
                "version": self._version_map.get(name, "unknown"),
                "state": self._states.get(name, PluginState.LOADED).value,
            }
            if name in self._metadata:
                entry["metadata"] = self._metadata[name]
            result.append(entry)
        return result

    def remove(self, name: str) -> bool:
        """Remove a plugin from the registry."""
        if name in self._plugins:
            self.deactivate(name)
            del self._plugins[name]
            self._states.pop(name, None)
            self._version_map.pop(name, None)
            self._metadata.pop(name, None)
            logger.info("Removed plugin '%s'", name)
            return True
        return False

    def get_active_plugins(self) -> List[str]:
        """Get names of all active plugins."""
        return [name for name, state in self._states.items() if state == PluginState.ACTIVE]

    def get_error_plugins(self) -> List[str]:
        """Get names of all error-state plugins."""
        return [name for name, state in self._states.items() if state == PluginState.ERROR]

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a plugin."""
        return self._metadata.get(name)

    def update_metadata(self, name: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a plugin."""
        if name in self._plugins:
            self._metadata[name] = metadata
            return True
        return False
