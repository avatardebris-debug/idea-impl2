"""Template manager for YouTube Studio."""

import json
import os
from typing import Dict, List, Optional, Any


class Template:
    """Represents a template with fields."""
    
    def __init__(self, name: str, description: str = '', version: str = '1.0', fields: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.version = version
        self.fields = fields or {}
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "fields": self.fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Template':
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            version=data.get('version', '1.0'),
            fields=data.get('fields', {})
        )


class TemplateField:
    """Represents a single template field."""
    
    def __init__(self, name: str, type: str = 'text', required: bool = True):
        self.name = name
        self.type = type
        self.required = required
    
    def to_dict(self) -> Dict:
        return {"name": self.name, "type": self.type, "required": self.required}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TemplateField':
        return cls(
            name=data['name'],
            type=data.get('type', 'text'),
            required=data.get('required', True)
        )


class TemplateManager:
    """Manages templates for YouTube Studio."""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), 'templates')
        self.templates: Dict[str, Template] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from directory."""
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.templates_dir, filename)
                    with open(filepath, 'r') as f:
                        template_data = json.load(f)
                        name = filename[:-5]
                        self.templates[name] = Template.from_dict(template_data)
    
    def load_template(self, name: str) -> Optional[Template]:
        """Load a template by name."""
        return self.templates.get(name)
    
    def save_template(self, template: Template) -> bool:
        """Save a template."""
        self.templates[template.name] = template
        os.makedirs(self.templates_dir, exist_ok=True)
        filepath = os.path.join(self.templates_dir, f'{template.name}.json')
        with open(filepath, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
        return True
    
    def get_all_templates(self) -> Dict[str, Template]:
        """Get all templates."""
        return dict(self.templates)
    
    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        if name in self.templates:
            del self.templates[name]
            filepath = os.path.join(self.templates_dir, f'{name}.json')
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        return False
    
    def validate_template(self, template: Template) -> bool:
        """Validate a template has required fields."""
        required_fields = ['title', 'description']
        return all(field in template.fields for field in required_fields)
    
    def apply_template(self, template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Apply a template with the given context."""
        template = self.templates.get(template_name)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")
        
        result = {}
        for field_name, field_value in template.fields.items():
            # Simple variable substitution
            rendered = field_value
            for key, value in context.items():
                rendered = rendered.replace(f'{{{key}}}', str(value))
            result[field_name] = rendered
        return result
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about templates."""
        total = len(self.templates)
        field_counts = {}
        for template in self.templates.values():
            for field_name in template.fields:
                field_counts[field_name] = field_counts.get(field_name, 0) + 1
        return {
            'total_templates': total,
            'field_usage': field_counts,
        }
