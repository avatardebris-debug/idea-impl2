"""
Dispatcher module for JSON skills.

Handles dispatching function calls defined in skill JSON files to their
corresponding implementations.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import inspect


class FunctionDispatcher:
    """
    Dispatches function calls to registered handlers.
    
    The dispatcher maintains a registry of function names to callable
    implementations. When a skill requests a function call, the dispatcher
    looks up the handler and executes it with the provided arguments.
    """
    
    def __init__(self):
        """Initialize an empty dispatcher."""
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable) -> None:
        """
        Register a function handler.
        
        Args:
            name: The name to register the function under
            func: The callable to invoke when this function is dispatched
        """
        if not isinstance(name, str):
            raise TypeError("Function name must be a string")
        
        if not callable(func):
            raise TypeError("Handler must be callable")
        
        self._handlers[name] = func
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a function handler.
        
        Args:
            name: The name of the handler to remove
            
        Returns:
            True if the handler was found and removed, False otherwise
        """
        if name in self._handlers:
            del self._handlers[name]
            return True
        return False
    
    def list_functions(self) -> List[str]:
        """
        List all registered function names.
        
        Returns:
            List of registered function names
        """
        return list(self._handlers.keys())
    
    def dispatch(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Dispatch a function call to its handler.
        
        Args:
            name: The name of the function to call
            arguments: Dictionary of arguments to pass to the function
            
        Returns:
            The return value of the function
            
        Raises:
            KeyError: If the function is not registered
            TypeError: If arguments don't match the function signature
        """
        if name not in self._handlers:
            raise KeyError(f"Function '{name}' is not registered")
        
        handler = self._handlers[name]
        args = arguments or {}
        
        # Get the function signature
        sig = inspect.signature(handler)
        
        # Check if the handler accepts **kwargs
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        
        if not has_var_keyword:
            # Validate that all provided arguments are in the signature
            param_names = set(sig.parameters.keys())
            extra_args = set(args.keys()) - param_names
            if extra_args:
                raise TypeError(
                    f"Function '{name}' does not accept arguments: {extra_args}"
                )
        
        # Call the handler with the arguments
        try:
            result = handler(**args)
        except TypeError as e:
            raise TypeError(
                f"Error calling function '{name}': {e}"
            )
        
        return result
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """
        Get a registered handler by name.
        
        Args:
            name: The name of the handler to get
            
        Returns:
            The handler function, or None if not found
        """
        return self._handlers.get(name)
