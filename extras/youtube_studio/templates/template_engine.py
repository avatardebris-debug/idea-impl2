"""Template engine for YouTube Studio.

This module provides functionality for rendering templates with
variable substitution and dynamic content insertion.
"""

import re
from typing import Dict, List, Optional, Callable


class TemplateEngine:
    """Engine for rendering templates with variable substitution.
    
    This class handles template rendering with support for:
    - Simple variable substitution {{variable_name}}
    - Conditional blocks {% if condition %}...{% endif %}
    - Loop blocks {% for item in items %}...{% endfor %}
    - Function calls {{variable|function}} and {{variable|function(arg)}}
    """
    
    def __init__(self):
        """Initialize template engine."""
        self._variables: Dict[str, any] = {}
        self._custom_functions: Dict[str, Callable] = {}
        self._load_builtin_functions()
    
    def _load_builtin_functions(self) -> None:
        """Load built-in template functions."""
        self._custom_functions['upper'] = lambda x: x.upper() if isinstance(x, str) else x
        self._custom_functions['lower'] = lambda x: x.lower() if isinstance(x, str) else x
        self._custom_functions['title'] = lambda x: x.title() if isinstance(x, str) else x
        self._custom_functions['capitalize'] = lambda x: x.capitalize() if isinstance(x, str) else x
        self._custom_functions['strip'] = lambda x: x.strip() if isinstance(x, str) else x
        self._custom_functions['len'] = lambda x: len(x) if isinstance(x, (str, list)) else x
        
        # Join function - takes a separator and returns a lambda that joins a list
        def make_join(sep):
            return lambda x: sep.join(x) if isinstance(x, list) else x
        
        self._custom_functions['join'] = make_join
        
        # Default function - takes a default value and returns a lambda
        def make_default(default_val):
            return lambda x: x if x is not None else default_val
        
        self._custom_functions['default'] = make_default
    
    def _parse_function_args(self, func_args: str) -> List:
        """Parse function arguments, handling quoted strings.
        
        Args:
            func_args: Raw argument string.
            
        Returns:
            List of parsed arguments.
        """
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        
        for char in func_args:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == ',' and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg:
            args.append(current_arg.strip())
        
        # Remove quotes from string arguments
        parsed_args = []
        for arg in args:
            if (arg.startswith('"') and arg.endswith('"')) or \
               (arg.startswith("'") and arg.endswith("'")):
                arg = arg[1:-1]
            parsed_args.append(arg)
        
        return parsed_args
    
    def _apply_function(self, value: any, func_name: str, func_args: List) -> any:
        """Apply a function to a value.
        
        Args:
            value: Value to apply function to.
            func_name: Name of the function.
            func_args: List of function arguments.
            
        Returns:
            Result of function application.
        """
        if func_name not in self._custom_functions:
            return value
        
        func = self._custom_functions[func_name]
        
        # Handle functions that take arguments (like join, default)
        if func_name in ('join', 'default'):
            if func_args:
                return func(func_args[0])(value)
            return value
        
        # Handle functions that take no arguments
        return func(value)
    
    def set_variable(self, name: str, value: any) -> None:
        """Set a template variable.
        
        Args:
            name: Variable name.
            value: Variable value.
        """
        self._variables[name] = value
    
    def set_variables(self, variables: Dict[str, any]) -> None:
        """Set multiple template variables.
        
        Args:
            variables: Dictionary of variable names and values.
        """
        self._variables.update(variables)
    
    def clear_variables(self) -> None:
        """Clear all template variables."""
        self._variables.clear()
    
    def render(self, template: str) -> str:
        """Render a template with current variables.
        
        Args:
            template: Template string to render.
            
        Returns:
            Rendered template string.
        """
        result = template
        
        # Process conditional blocks first
        result = self._process_conditionals(result)
        
        # Process loop blocks
        result = self._process_loops(result)
        
        # Process variable substitutions
        result = self._process_variables(result)
        
        return result
    
    def _process_conditionals(self, template: str) -> str:
        """Process conditional blocks in template.
        
        Args:
            template: Template string.
            
        Returns:
            Template with conditionals processed.
        """
        # Simple if/endif processing
        pattern = r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}'
        
        def replace_if(match):
            var_name = match.group(1)
            content = match.group(2)
            
            # Check if variable exists and is truthy
            value = self._variables.get(var_name)
            if value:
                return content
            return ''
        
        result = re.sub(pattern, replace_if, template, flags=re.DOTALL)
        return result
    
    def _process_loops(self, template: str) -> str:
        """Process loop blocks in template.
        
        Args:
            template: Template string.
            
        Returns:
            Template with loops processed.
        """
        # Simple for loop processing
        pattern = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
        
        def replace_for(match):
            item_var = match.group(1)
            list_var = match.group(2)
            content = match.group(3)
            
            # Get the list
            items = self._variables.get(list_var, [])
            if not isinstance(items, list):
                return ''
            
            # Render for each item
            result_parts = []
            for item in items:
                # Create a copy of variables for this iteration
                iteration_vars = self._variables.copy()
                iteration_vars[item_var] = item
                
                # Temporarily set variables
                old_vars = self._variables.copy()
                self._variables.update(iteration_vars)
                
                # Render content with current item
                rendered = self._process_variables(content)
                result_parts.append(rendered)
                
                # Restore variables
                self._variables = old_vars
            
            return ''.join(result_parts)
        
        result = re.sub(pattern, replace_for, template, flags=re.DOTALL)
        return result
    
    def _process_variables(self, template: str) -> str:
        """Process variable substitutions in template.
        
        Args:
            template: Template string.
            
        Returns:
            Template with variables substituted.
        """
        # Pattern to match {{variable|function(args)}} or {{variable}}
        pattern = r'\{\{(\w+)(?:\|(\w+)(?:\(([^)]*)\))?)?\}\}'
        
        def replace_variable(match):
            var_name = match.group(1)
            func_name = match.group(2)
            func_args_str = match.group(3)
            
            # Get variable value
            value = self._variables.get(var_name)
            if value is None:
                return ''
            
            # Convert to string if needed
            if not isinstance(value, str):
                value = str(value)
            
            # Apply function if specified
            if func_name:
                func_args = []
                if func_args_str:
                    func_args = self._parse_function_args(func_args_str)
                value = self._apply_function(value, func_name, func_args)
            
            return str(value)
        
        result = re.sub(pattern, replace_variable, template)
        return result
    
    def render_template_file(self, filepath: str) -> str:
        """Render a template from a file.
        
        Args:
            filepath: Path to template file.
            
        Returns:
            Rendered template string.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            template = f.read()
        
        return self.render(template)
