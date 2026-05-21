"""
Dispatcher module for JSON skills.

Handles dispatching function calls defined in skill JSON files to their
corresponding implementations.
"""

from typing import Any, Callable, Dict, List, Optional


class FunctionDispatcher:
    """
    Dispatches function calls to registered handlers.
    
    The dispatcher maintains a registry of function names to callable
    implementations. When a skill requests a function call, the dispatcher
    looks up the handler and executes it.
    """
    
    def __init__(self) -> None:
        self._registry: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable) -> None:
        """Register a function handler by name."""
        self._registry[name] = func
    
    def unregister(self, name: str) -> None:
        """Unregister a function handler by name."""
        self._registry.pop(name, None)
    
    def dispatch(self, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """
        Dispatch a function call by name with the given arguments.
        
        Args:
            name: The function name to dispatch.
            args: Optional keyword arguments dict.
            
        Returns:
            The result of the function call.
            
        Raises:
            KeyError: If the function name is not registered.
        """
        if name not in self._registry:
            raise KeyError(f"Function '{name}' is not registered")
        handler = self._registry[name]
        if args is None:
            args = {}
        return handler(**args)
    
    def register_from_skill_functions(
        self,
        functions: List[Dict[str, Any]],
        handler_map: Dict[str, Callable],
    ) -> None:
        """
        Register all functions from a skill's function definitions.
        
        Args:
            functions: List of function definition dicts from a skill.
            handler_map: Mapping of function names to callables.
        """
        for func_def in functions:
            name = func_def.get("name")
            if name and name in handler_map:
                self.register(name, handler_map[name])
    
    def list_functions(self) -> List[str]:
        """Return a list of registered function names."""
        return list(self._registry.keys())
    
    def has_function(self, name: str) -> bool:
        """Check if a function is registered."""
        return name in self._registry
