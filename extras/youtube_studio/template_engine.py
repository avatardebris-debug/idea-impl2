"""Template engine for YouTube Studio."""

import re
from typing import Dict, Any, Callable, Optional


class TemplateEngine:
    """Renders templates with variable substitution."""
    
    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._filters: Dict[str, Callable] = {}
        self._tags: Dict[str, Callable] = {}
        self._templates: Dict[str, Dict[str, str]] = {}
    
    def render_template(self, template: Dict[str, str], context: Dict[str, Any]) -> Dict[str, str]:
        """Render a template with the given context."""
        result = {}
        for key, value in template.items():
            result[key] = self._render_string(value, context)
        return result
    
    def _render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a single string template."""
        result = template_str
        
        # Handle {{variable}} substitution
        def replace_var(match):
            var_name = match.group(1).strip()
            # Handle filters like {{title|upper}}
            if '|' in var_name:
                var_name, filter_name = var_name.split('|', 1)
                var_name = var_name.strip()
                filter_name = filter_name.strip()
                value = context.get(var_name, '')
                if filter_name == 'upper':
                    return str(value).upper()
                elif filter_name == 'lower':
                    return str(value).lower()
                elif filter_name == 'join':
                    separator = filter_name.split('"')[1] if '"' in filter_name else ', '
                    if isinstance(value, list):
                        return separator.join(str(v) for v in value)
                    return str(value)
                return str(value)
            return str(context.get(var_name, ''))
        
        result = re.sub(r'\{\{([^}]+)\}\}', replace_var, result)
        return result
    
    def add_filter(self, name: str, func: Callable):
        """Add a custom filter."""
        self._filters[name] = func
    
    def add_tag(self, name: str, func: Callable):
        """Add a custom tag."""
        self._tags[name] = func
    
    def set_variable(self, name: str, value: Any):
        """Set a single variable."""
        self._variables[name] = value
    
    def set_variables(self, variables: Dict[str, Any]):
        """Set multiple variables."""
        self._variables.update(variables)
    
    def clear_variables(self):
        """Clear all variables."""
        self._variables.clear()
    
    def get_variable(self, name: str) -> Any:
        """Get a variable by name."""
        return self._variables.get(name)
    
    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables."""
        return dict(self._variables)
    
    def get_available_templates(self) -> Dict[str, Dict[str, str]]:
        """Get all available templates."""
        return dict(self._templates)
    
    def get_template(self, name: str) -> Optional[Dict[str, str]]:
        """Get a template by name."""
        return self._templates.get(name)
    
    def save_template(self, name: str, template: Dict[str, str]):
        """Save a template."""
        self._templates[name] = template
    
    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        if name in self._templates:
            del self._templates[name]
            return True
        return False
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about templates."""
        total = len(self._templates)
        field_counts = {}
        for template in self._templates.values():
            for field_name in template:
                field_counts[field_name] = field_counts.get(field_name, 0) + 1
        return {
            'total_templates': total,
            'field_usage': field_counts,
        }
