"""Template manager for YouTube Studio.

This module provides functionality for loading, saving, and managing
JSON-based video metadata templates.
"""

import json
import os
from typing import Dict, List, Optional
from .constants import TEMPLATE_EXTENSION, TEMPLATE_REQUIRED_FIELDS


class TemplateManager:
    """Manager for loading, saving, and managing video templates.
    
    This class provides centralized template management with support
    for loading from JSON files, saving custom templates, and
    retrieving template configurations.
    """
    
    def __init__(self, template_directory: str = 'templates'):
        """Initialize template manager.
        
        Args:
            template_directory: Directory path where templates are stored.
        """
        self._template_directory = template_directory
        self._templates: Dict[str, dict] = {}
        self._ensure_directory_exists()
        self._load_all_templates()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the template directory exists."""
        if not os.path.exists(self._template_directory):
            os.makedirs(self._template_directory)
    
    def _load_all_templates(self) -> None:
        """Load all templates from the template directory."""
        if not os.path.exists(self._template_directory):
            return
        
        for filename in os.listdir(self._template_directory):
            if filename.endswith(TEMPLATE_EXTENSION):
                template_name = filename[:-len(TEMPLATE_EXTENSION)]
                self.load_template(filename)
    
    def load_template(self, template_name: str) -> Optional[dict]:
        """Load a template from a JSON file.
        
        Args:
            template_name: Name of the template (without extension).
            
        Returns:
            Template dictionary or None if loading fails.
        """
        if not template_name.endswith(TEMPLATE_EXTENSION):
            template_name += TEMPLATE_EXTENSION
        
        filepath = os.path.join(self._template_directory, template_name)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Validate required fields
            if not self._validate_template(template):
                return None
            
            self._templates[template_name] = template
            return template
        
        except (IOError, json.JSONDecodeError) as e:
            return None
    
    def save_template(self, template_name: str, template: dict) -> bool:
        """Save a template to a JSON file.
        
        Args:
            template_name: Name for the template.
            template: Template dictionary to save.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        if not template_name.endswith(TEMPLATE_EXTENSION):
            template_name += TEMPLATE_EXTENSION
        
        filepath = os.path.join(self._template_directory, template_name)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            self._templates[template_name] = template
            return True
        
        except IOError:
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template file.
        
        Args:
            template_name: Name of the template to delete.
            
        Returns:
            True if deleted successfully, False otherwise.
        """
        if not template_name.endswith(TEMPLATE_EXTENSION):
            template_name += TEMPLATE_EXTENSION
        
        filepath = os.path.join(self._template_directory, template_name)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                self._templates.pop(template_name, None)
                return True
            return False
        
        except IOError:
            return False
    
    def get_template(self, template_name: str) -> Optional[dict]:
        """Get a loaded template by name.
        
        Args:
            template_name: Name of the template.
            
        Returns:
            Template dictionary or None if not found.
        """
        if not template_name.endswith(TEMPLATE_EXTENSION):
            template_name += TEMPLATE_EXTENSION
        
        return self._templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List all available template names.
        
        Returns:
            List of template names.
        """
        return list(self._templates.keys())
    
    def _validate_template(self, template: dict) -> bool:
        """Validate that a template has all required fields.
        
        Args:
            template: Template dictionary to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        for field in TEMPLATE_REQUIRED_FIELDS:
            if field not in template:
                return False
        
        return True
    
    def get_template_config(self, template_name: str) -> Optional[dict]:
        """Get the configuration section of a template.
        
        Args:
            template_name: Name of the template.
            
        Returns:
            Template configuration dictionary or None.
        """
        template = self.get_template(template_name)
        if template:
            return template.get('config', {})
        return None
