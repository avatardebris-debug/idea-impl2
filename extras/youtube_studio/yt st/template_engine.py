"""Template engine for YouTube Studio.

This module provides functionality for rendering templates with
variable substitution and dynamic content insertion.
"""

import re
from typing import Dict, List, Optional, Callable, Any


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
        self._variables: Dict[str, Any] = {}
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
                # Include the quote character in the argument
                current_arg += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                # Include the closing quote character
                current_arg += char
            elif char == ',' and not in_quotes:
                # End of argument
                if current_arg.strip():
                    arg = current_arg.strip()
                    # Remove quotes if present
                    if (arg.startswith("'") and arg.endswith("'")) or \
                       (arg.startswith('"') and arg.endswith('"')):
                        arg = arg[1:-1]
                    args.append(arg)
                current_arg = ""
                continue
            else:
                current_arg += char
        
        # Don't forget the last argument
        if current_arg.strip():
            arg = current_arg.strip()
            if (arg.startswith("'") and arg.endswith("'")) or \
               (arg.startswith('"') and arg.endswith('"')):
                arg = arg[1:-1]
            args.append(arg)
        
        return args
    
    def set_variable(self, name: str, value: any) -> None:
        """Set a single variable.
        
        Args:
            name: Variable name.
            value: Variable value.
        """
        self._variables[name] = value
    
    def set_variables(self, variables: Dict[str, any]) -> None:
        """Set multiple variables.
        
        Args:
            variables: Dictionary of variable names and values.
        """
        self._variables.update(variables)
    
    def clear_variables(self) -> None:
        """Clear all variables."""
        self._variables.clear()
    
    def _apply_function(self, value: any, func_name: str, args: List) -> any:
        """Apply a function to a value.
        
        Args:
            value: The value to apply the function to.
            func_name: Name of the function.
            args: List of function arguments.
            
        Returns:
            Result of applying the function.
        """
        if func_name in self._custom_functions:
            func = self._custom_functions[func_name]
            if args:
                # If the function expects arguments, pass them
                return func(*args)
            else:
                # Otherwise, apply to the value
                return func(value)
        return value
    
    def _render_condition(self, condition: str, true_block: str, false_block: str, 
                          variables: Dict[str, any]) -> str:
        """Render a conditional block.
        
        Args:
            condition: The condition to evaluate.
            true_block: Content if condition is true.
            false_block: Content if condition is false.
            variables: Current variables.
            
        Returns:
            Rendered content based on condition.
        """
        # Handle 'and' and 'or' operators
        if ' and ' in condition:
            parts = condition.split(' and ')
            result = all(self._evaluate_condition(part.strip(), variables) for part in parts)
        elif ' or ' in condition:
            parts = condition.split(' or ')
            result = any(self._evaluate_condition(part.strip(), variables) for part in parts)
        else:
            result = self._evaluate_condition(condition, variables)
        
        if result:
            return self.render_template(true_block, variables)
        elif false_block:
            return self.render_template(false_block, variables)
        return ""
    
    def _evaluate_condition(self, condition: str, variables: Dict[str, any]) -> bool:
        """Evaluate a simple condition.
        
        Args:
            condition: The condition string.
            variables: Current variables.
            
        Returns:
            Boolean result of the condition.
        """
        # Handle equality check
        if '==' in condition:
            parts = condition.split('==')
            left = parts[0].strip()
            right = parts[1].strip()
            
            left_val = self._get_value(left, variables)
            right_val = self._get_value(right, variables)
            
            return left_val == right_val
        
        # Handle inequality check
        if '!=' in condition:
            parts = condition.split('!=')
            left = parts[0].strip()
            right = parts[1].strip()
            
            left_val = self._get_value(left, variables)
            right_val = self._get_value(right, variables)
            
            return left_val != right_val
        
        # Handle truthiness check
        value = self._get_value(condition, variables)
        return bool(value)
    
    def _get_value(self, name: str, variables: Dict[str, any]) -> any:
        """Get a value from variables, handling nested access.
        
        Args:
            name: Variable name or path (e.g., 'user.name').
            variables: Current variables.
            
        Returns:
            Value from variables.
        """
        # Handle nested access (e.g., 'user.name')
        parts = name.split('.')
        value = variables
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                try:
                    index = int(part)
                    value = value[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        
        return value
    
    def _render_loop(self, var_name: str, iterable_name: str, loop_block: str, 
                     variables: Dict[str, any]) -> str:
        """Render a loop block.
        
        Args:
            var_name: Loop variable name.
            iterable_name: Name of the iterable.
            loop_block: Content to repeat.
            variables: Current variables.
            
        Returns:
            Rendered loop content.
        """
        iterable = self._get_value(iterable_name, variables)
        
        if not iterable or not hasattr(iterable, '__iter__'):
            return ""
        
        result = []
        for i, item in enumerate(iterable):
            # Create loop variables
            loop_vars = variables.copy()
            loop_vars[var_name] = item
            loop_vars[f'{var_name}_index'] = i
            loop_vars[f'{var_name}_first'] = i == 0
            loop_vars[f'{var_name}_last'] = i == len(iterable) - 1
            loop_vars[f'{var_name}_length'] = len(iterable)
            
            # Render the loop block with these variables
            rendered = self.render_template(loop_block, loop_vars)
            result.append(rendered)
        
        return ''.join(result)
    
    def render_template(self, template: str, variables: Optional[Dict[str, any]] = None) -> str:
        """Render a template string.
        
        Args:
            template: The template string to render.
            variables: Optional dictionary of variables.
            
        Returns:
            Rendered template string.
        """
        if variables is not None:
            self.set_variables(variables)
        
        result = template
        
        # Process loops first (they may contain conditionals)
        while '{% for ' in result:
            result = self._process_loops(result)
        
        # Process conditionals
        while '{% if ' in result:
            result = self._process_conditionals(result)
        
        # Process variable substitutions
        result = self._process_variables(result)
        
        return result
    
    def _process_loops(self, template: str) -> str:
        """Process all loop blocks in the template.
        
        Args:
            template: The template string.
            
        Returns:
            Template with loops processed.
        """
        pattern = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
        
        def replace_loop(match):
            var_name = match.group(1)
            iterable_name = match.group(2)
            loop_block = match.group(3)
            
            return self._render_loop(var_name, iterable_name, loop_block, self._variables)
        
        return re.sub(pattern, replace_loop, template, flags=re.DOTALL)
    
    def _process_conditionals(self, template: str) -> str:
        """Process all conditional blocks in the template.
        
        Args:
            template: The template string.
            
        Returns:
            Template with conditionals processed.
        """
        pattern = r'\{%\s*if\s+(.*?)\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}'
        
        def replace_condition(match):
            condition = match.group(1)
            true_block = match.group(2)
            false_block = match.group(3)
            
            return self._render_condition(condition, true_block, false_block, self._variables)
        
        return re.sub(pattern, replace_condition, template, flags=re.DOTALL)
    
    def _process_variables(self, template: str) -> str:
        """Process all variable substitutions in the template.
        
        Args:
            template: The template string.
            
        Returns:
            Template with variables substituted.
        """
        pattern = r'\{\{(.*?)\}\}'
        
        def replace_variable(match):
            expression = match.group(1).strip()
            
            # Check for function call
            if '|' in expression:
                var_name, func_part = expression.split('|', 1)
                var_name = var_name.strip()
                
                # Parse function name and arguments
                if '(' in func_part:
                    func_name, func_args = func_part.split('(', 1)
                    func_name = func_name.strip()
                    func_args = func_args.rstrip(')')
                    args = self._parse_function_args(func_args)
                else:
                    func_name = func_part.strip()
                    args = []
                
                value = self._get_value(var_name, self._variables)
                return str(self._apply_function(value, func_name, args))
            else:
                # Simple variable substitution
                value = self._get_value(expression, self._variables)
                return str(value) if value is not None else ''
        
        return re.sub(pattern, replace_variable, template)
    
    def render_template_file(self, file_path: str, variables: Optional[Dict[str, any]] = None) -> str:
        """Render a template from a file.
        
        Args:
            file_path: Path to the template file.
            variables: Optional dictionary of variables.
            
        Returns:
            Rendered template string.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        return self.render_template(template, variables)
