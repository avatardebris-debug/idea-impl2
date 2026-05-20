"""
Runtime module for JSON skills.

Provides the SkillRuntime class that orchestrates loading skills,
registering functions, and executing the skill loop.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import json

from .loader import load_skill, validate_skill_schema
from .dispatcher import FunctionDispatcher


class SkillExecutionError(Exception):
    """Raised when a skill execution fails."""
    pass


class SkillRuntime:
    """
    Runtime for executing JSON skills.
    
    This class manages the lifecycle of a skill:
    1. Loading the skill definition
    2. Registering function handlers
    3. Executing the skill loop (prompting AI, handling tool calls, etc.)
    """
    
    def __init__(self, skill_path: Optional[Union[str, Path]] = None):
        """
        Initialize the skill runtime.
        
        Args:
            skill_path: Optional path to a JSON skill file to load immediately
        """
        self.skill_path = skill_path
        self.skill_data: Optional[Dict[str, Any]] = None
        self.dispatcher = FunctionDispatcher()
        self._is_loaded = False
    
    def load(self, skill_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load a skill from a JSON file.
        
        Args:
            skill_path: Path to the JSON skill file. If None, uses the path
                       provided during initialization.
        """
        path = skill_path or self.skill_path
        
        if not path:
            raise SkillExecutionError("No skill path provided")
        
        self.skill_data = load_skill(path)
        self.skill_path = path
        self._is_loaded = True
        
        # Register all functions from the skill
        self._register_functions()
    
    def _register_functions(self) -> None:
        """Register all functions defined in the loaded skill."""
        if not self.skill_data:
            raise SkillExecutionError("No skill loaded")
        
        for func_def in self.skill_data["functions"]:
            name = func_def["name"]
            # Note: In a real implementation, you would map these to actual
            # handler functions. For now, we just register them as placeholders.
            # The actual handlers would be provided by the application using this library.
            self.dispatcher.register(name, self._default_handler)
    
    def _default_handler(self, **kwargs) -> str:
        """
        Default handler for unregistered functions.
        
        This is used as a placeholder for functions that haven't been
        explicitly registered with a real implementation.
        
        Args:
            **kwargs: Arguments passed to the function
            
        Returns:
            A string indicating the function was not implemented
        """
        return "Function not implemented"
    
    def register_function(self, name: str, handler: Any) -> None:
        """
        Register a function handler.
        
        Args:
            name: The name of the function to register
            handler: The callable to invoke when this function is called
        """
        self.dispatcher.register(name, handler)
    
    def unregister_function(self, name: str) -> bool:
        """
        Unregister a function handler.
        
        Args:
            name: The name of the function to unregister
            
        Returns:
            True if the function was found and removed, False otherwise
        """
        return self.dispatcher.unregister(name)
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the skill.
        
        Returns:
            The system prompt string
        """
        if not self.skill_data:
            raise SkillExecutionError("No skill loaded")
        
        return self.skill_data["system_prompt"]
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the function definitions from the skill.
        
        Returns:
            List of function definition dictionaries
        """
        if not self.skill_data:
            raise SkillExecutionError("No skill loaded")
        
        return self.skill_data["functions"]
    
    def execute(self, user_input: str, ai_client=None) -> Dict[str, Any]:
        """
        Execute the skill with the given user input.
        
        This is the main entry point for running a skill. It handles:
        1. Sending the prompt to the AI
        2. Processing any tool calls returned by the AI
        3. Returning the final result
        
        Args:
            user_input: The user's input message
            ai_client: Optional AI client to use for generating responses.
                      If None, a simple mock implementation is used.
                      
        Returns:
            Dictionary containing the execution result
        """
        if not self.skill_data:
            raise SkillExecutionError("No skill loaded")
        
        # Build the conversation history
        conversation = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": user_input}
        ]
        
        # Execute the skill loop
        result = self._execute_loop(conversation, ai_client)
        
        return result
    
    def _execute_loop(self, conversation: List[Dict[str, Any]], ai_client=None) -> Dict[str, Any]:
        """
        Execute the skill loop until completion.
        
        Args:
            conversation: List of conversation messages
            ai_client: Optional AI client
            
        Returns:
            Dictionary containing the final result
        """
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from AI
            if ai_client:
                response = ai_client.generate(conversation, self.get_function_definitions())
            else:
                response = self._mock_ai_response(conversation, self.get_function_definitions())
            
            # Check if the AI wants to call a function
            if response.get("function_call"):
                func_call = response["function_call"]
                func_name = func_call["name"]
                func_args = func_call.get("arguments", {})
                
                # Execute the function
                try:
                    result = self.dispatcher.dispatch(func_name, func_args)
                except KeyError:
                    result = f"Function '{func_name}' not found"
                except Exception as e:
                    result = f"Error executing function '{func_name}': {str(e)}"
                
                # Add function result to conversation
                conversation.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": func_call
                })
                conversation.append({
                    "role": "function",
                    "name": func_name,
                    "content": str(result)
                })
            else:
                # No more function calls, return the final response
                return {
                    "success": True,
                    "result": response.get("content", ""),
                    "iterations": iteration
                }
        
        # Max iterations reached
        return {
            "success": False,
            "error": "Max iterations reached",
            "iterations": iteration
        }
    
    def _mock_ai_response(self, conversation: List[Dict[str, Any]], functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mock AI response for testing.
        
        Args:
            conversation: List of conversation messages
            functions: List of available functions
            
        Returns:
            Dictionary containing the mock response
        """
        # Simple mock: if there are functions available, call the first one
        if functions and not any(msg.get("role") == "function" for msg in conversation):
            return {
                "function_call": {
                    "name": functions[0]["name"],
                    "arguments": {}
                }
            }
        
        return {
            "content": "This is a mock response. In production, this would be the AI's actual response."
        }
    
    def reset(self) -> None:
        """Reset the runtime state."""
        self.skill_data = None
        self.skill_path = None
        self.dispatcher = FunctionDispatcher()
        self._is_loaded = False
