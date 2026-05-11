"""Template manager for YouTube Studio.

This module provides template management functionality for storing,
loading, and rendering templates.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from .template_engine import TemplateEngine


class TemplateManager:
    """Manager for storing and loading templates."""
    
    def __init__(self, template_dir: str = './templates'):
        """Initialize template manager.
        
        Args:
            template_dir: Directory to store templates
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.engine = TemplateEngine()
        self.templates = {}  # In-memory cache
    
    def save_template(self, name: str, template: Dict[str, str]) -> bool:
        """Save a template to disk.
        
        Args:
            name: Name of the template
            template: Template dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not name or not template:
            return False
        
        template_file = self.template_dir / f"{name}.json"
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            # Update in-memory cache
            self.templates[name] = template
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def load_template(self, name: str) -> Optional[Dict[str, str]]:
        """Load a template from disk.
        
        Args:
            name: Name of the template
            
        Returns:
            Template dictionary or None if not found
        """
        # Check in-memory cache first
        if name in self.templates:
            return self.templates[name]
        
        template_file = self.template_dir / f"{name}.json"
        
        if not template_file.exists():
            return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Update in-memory cache
            self.templates[name] = template
            return template
        except Exception as e:
            print(f"Error loading template: {e}")
            return None
    
    def delete_template(self, name: str) -> bool:
        """Delete a template.
        
        Args:
            name: Name of the template
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from in-memory cache
        if name in self.templates:
            del self.templates[name]
        
        template_file = self.template_dir / f"{name}.json"
        
        if template_file.exists():
            try:
                template_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting template: {e}")
                return False
        
        return False
    
    def list_templates(self) -> List[str]:
        """List all available templates.
        
        Returns:
            List of template names
        """
        # Update cache from disk
        for template_file in self.template_dir.glob('*.json'):
            name = template_file.stem
            if name not in self.templates:
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        self.templates[name] = json.load(f)
                except Exception:
                    pass
        
        return list(self.templates.keys())
    
    def render_template(self, name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a named template with variables.
        
        Args:
            name: Name of the template
            variables: Dictionary of variable values
            
        Returns:
            Rendered template string or None if template not found
        """
        template = self.load_template(name)
        if template is None:
            return None
        
        try:
            # If template is a dict, extract the 'content' field or join all values
            if isinstance(template, dict):
                template_str = template.get('content', '')
                if not template_str:
                    # If no 'content' key, use the first value
                    template_str = next(iter(template.values())) if template else ''
            else:
                template_str = template
            return self.engine.render_template(template_str, variables)
        except (ValueError, KeyError) as e:
            print(f"Error rendering template: {e}")
            return None
