"""
Runtime module for JSON skills.

Provides the SkillRuntime class that orchestrates loading skills,
registering functions, and building the injected payload for the model.
"""

from typing import Any, Callable, Dict, List, Optional

from .loader import load_skill, validate_skill_schema
from .dispatcher import FunctionDispatcher


class SkillExecutionError(Exception):
    """Raised when a skill execution fails."""
    pass


class SkillRuntime:
    """
    Runtime for executing JSON skills.
    
    Loads a skill, registers its functions via a dispatcher, and builds
    the model-compatible payload.
    """
    
    def __init__(self) -> None:
        self.dispatcher = FunctionDispatcher()
    
    def load_skill(self, skill_path) -> Dict[str, Any]:
        """
        Load a skill from a JSON file.
        
        Args:
            skill_path: Path to the JSON skill file.
            
        Returns:
            The parsed skill dictionary.
        """
        return load_skill(skill_path)
    
    def register_functions(
        self,
        skill: Dict[str, Any],
        handler_map: Dict[str, Callable],
    ) -> None:
        """
        Register all functions from a skill with the dispatcher.
        
        Args:
            skill: The loaded skill dictionary.
            handler_map: Mapping of function names to callables.
        """
        self.dispatcher.register_from_skill_functions(
            functions=skill.get("functions", []),
            handler_map=handler_map,
        )
    
    def build_payload(self, skill: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a model-compatible payload from a loaded skill.
        
        Args:
            skill: The loaded skill dictionary.
            
        Returns:
            A dict with system_prompt, tools (functions), and examples.
        """
        payload: Dict[str, Any] = {
            "system_prompt": skill.get("system_prompt", ""),
            "tools": [],
        }
        
        for func_def in skill.get("functions", []):
            tool_entry = {
                "type": "function",
                "function": {
                    "name": func_def["name"],
                    "description": func_def.get("description", ""),
                    "parameters": func_def.get("parameters", {}),
                },
            }
            payload["tools"].append(tool_entry)
        
        if "examples" in skill:
            payload["examples"] = skill["examples"]
        
        return payload
    
    def run(self, skill_path, handler_map: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Full pipeline: load skill, register functions, build payload.
        
        Args:
            skill_path: Path to the JSON skill file.
            handler_map: Mapping of function names to callables.
            
        Returns:
            The model-compatible payload.
        """
        skill = self.load_skill(skill_path)
        self.register_functions(skill, handler_map)
        return self.build_payload(skill)
