"""
Dynamic plugin discovery and loading via entry points and filesystem.
"""

import importlib
import logging
import os
import sys
from typing import Dict, List, Optional, Type

from .base import PluginABC
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Discovers and loads plugins from entry points and a plugins directory.
    """

    def __init__(self, registry: PluginRegistry, plugins_dir: Optional[str] = None):
        self.registry = registry
        self.plugins_dir = plugins_dir or os.path.join(os.path.dirname(__file__), "..", "transports")

    def discover_entry_points(self, group: str = "pairenv.plugins") -> List[str]:
        """Discover plugins registered as entry points."""
        discovered = []
        try:
            from importlib.metadata import entry_points
            eps = entry_points()
            if hasattr(eps, 'select'):
                group_eps = eps.select(group=group)
            else:
                group_eps = eps.get(group, [])
            for ep in group_eps:
                name = ep.name
                discovered.append(name)
                logger.info("Discovered entry point plugin: %s", name)
        except Exception as e:
            logger.warning("No entry point plugins found: %s", e)
        return discovered

    def discover_filesystem(self, directory: Optional[str] = None) -> List[str]:
        """Discover plugins as Python files in a directory."""
        target = directory or self.plugins_dir
        discovered = []
        if not os.path.isdir(target):
            logger.warning("Plugins directory not found: %s", target)
            return discovered
        for filename in os.listdir(target):
            if filename.endswith('.py') and not filename.startswith('_'):
                name = filename[:-3]
                discovered.append(name)
                logger.info("Discovered filesystem plugin: %s", name)
        return discovered

    def load_entry_point(self, group: str, name: str) -> Optional[PluginABC]:
        """Load a plugin from an entry point."""
        try:
            from importlib.metadata import entry_points
            eps = entry_points()
            if hasattr(eps, 'select'):
                group_eps = eps.select(group=group)
            else:
                group_eps = eps.get(group, [])
            for ep in group_eps:
                if ep.name == name:
                    plugin_class = ep.load()
                    if isinstance(plugin_class, type) and issubclass(plugin_class, PluginABC):
                        instance = plugin_class()
                        logger.info("Loaded entry point plugin: %s", name)
                        return instance
        except Exception as e:
            logger.error("Failed to load entry point plugin '%s': %s", name, e)
        return None

    def load_filesystem(self, name: str, directory: Optional[str] = None) -> Optional[PluginABC]:
        """Load a plugin from a filesystem module."""
        target = directory or self.plugins_dir
        module_path = os.path.join(target, f"{name}.py")
        if not os.path.isfile(module_path):
            return None
        try:
            spec = importlib.util.spec_from_file_location(f"pairenv.transports.{name}", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Find PluginABC subclass in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, PluginABC) and attr is not PluginABC:
                        instance = attr()
                        logger.info("Loaded filesystem plugin: %s", name)
                        return instance
        except Exception as e:
            logger.error("Failed to load filesystem plugin '%s': %s", name, e)
        return None

    def load_all(self) -> int:
        """Discover and load all available plugins. Returns count loaded."""
        count = 0
        # Load entry point plugins
        entry_points = self.discover_entry_points()
        for name in entry_points:
            plugin = self.load_entry_point("pairenv.plugins", name)
            if plugin:
                self.registry.register(plugin)
                count += 1

        # Load filesystem plugins
        fs_plugins = self.discover_filesystem()
        for name in fs_plugins:
            plugin = self.load_filesystem(name)
            if plugin:
                self.registry.register(plugin)
                count += 1

        logger.info("Loaded %d plugins total", count)
        return count
