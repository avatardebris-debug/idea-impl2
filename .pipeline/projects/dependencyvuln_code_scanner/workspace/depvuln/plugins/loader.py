import importlib.metadata
import logging

logger = logging.getLogger(__name__)

class PluginLoader:
    """Discovers and loads depvuln plugins via Python entry points."""
    
    def __init__(self):
        self.parsers = {}
        self.cve_sources = {}
        self.reports = {}
        self._load_plugins()
        
    def _load_plugins(self):
        """Load plugins from `depvuln.plugins` entry points."""
        try:
            # We use importlib.metadata to find entry points
            entry_points = importlib.metadata.entry_points()
            
            # For Python 3.10+, entry_points() returns a dict-like object
            if hasattr(entry_points, "select"):
                depvuln_eps = entry_points.select(group="depvuln.plugins")
            else:
                depvuln_eps = entry_points.get("depvuln.plugins", [])
                
            for ep in depvuln_eps:
                try:
                    plugin_class = ep.load()
                    plugin_type = getattr(plugin_class, "PLUGIN_TYPE", None)
                    
                    if plugin_type == "parser":
                        self.parsers[ep.name] = plugin_class
                    elif plugin_type == "cve_source":
                        self.cve_sources[ep.name] = plugin_class
                    elif plugin_type == "report":
                        self.reports[ep.name] = plugin_class
                        
                    logger.debug(f"Loaded plugin: {ep.name} ({plugin_type})")
                except Exception as e:
                    logger.error(f"Failed to load plugin {ep.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")

    def get_parsers(self):
        return self.parsers
        
    def get_cve_sources(self):
        return self.cve_sources
        
    def get_reports(self):
        return self.reports
