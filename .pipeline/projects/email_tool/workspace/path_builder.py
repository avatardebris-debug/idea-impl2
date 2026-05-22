"""Path builder module for template-based path construction."""

import re
import os
from datetime import datetime
from typing import Optional
from email_tool.models import Email, Rule


class PathBuilder:
    """
    Constructs file paths from templates with variable substitution.
    
    Supports template variables:
    - {{year}} - 4-digit year from email date
    - {{month}} - 2-digit month from email date
    - {{day}} - 2-digit day from email date
    - {{from_domain}} - domain part of sender's email address
    - {{subject_sanitized}} - subject with invalid filename characters removed
    - {{rule_name}} - name of the matched rule
    """
    
    # Invalid filename characters for Windows and common filesystems
    INVALID_FILENAME_CHARS = r'<>:"/\\|?*?!'
    
    # Template variable pattern
    TEMPLATE_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    
    def __init__(self, template: str = "{{year}}/{{month}}/{{from_domain}}/{{subject_sanitized}}"):
        """
        Initialize the path builder with a template.
        
        Args:
            template: Path template string with variable placeholders.
        """
        self.template = template
    
    def build_path(
        self,
        email: Email,
        rule: Optional[Rule] = None,
        base_path: str = ""
    ) -> str:
        """
        Build a complete file path from the template.
        
        Args:
            email: The email object to extract data from.
            rule: Optional matched rule for rule_name substitution.
            base_path: Optional base path to prepend.
        
        Returns:
            Constructed file path with OS-specific separators.
        """
        # Build the path components from template
        path_parts = self._expand_template(email, rule)
        
        # Combine with base path if provided
        if base_path:
            path_parts = os.path.join(base_path, path_parts)
        
        # Normalize separators to OS-specific
        path_parts = self._normalize_separators(path_parts)
        
        return path_parts
    
    def _expand_template(self, email: Email, rule: Optional[Rule] = None) -> str:
        """
        Expand template variables in the template string.
        
        Args:
            email: The email object.
            rule: Optional matched rule.
        
        Returns:
            Template string with variables substituted.
        """
        def replace_var(match):
            var_name = match.group(1)
            return self._get_variable_value(email, rule, var_name)
        
        return self.TEMPLATE_PATTERN.sub(replace_var, self.template)
    
    def _get_variable_value(self, email: Email, rule: Optional[Rule], var_name: str) -> str:
        """
        Get the value for a template variable.
        
        Args:
            email: The email object.
            rule: Optional matched rule.
            var_name: The variable name.
        
        Returns:
            String value for the variable.
        """
        if var_name == "year":
            return self._get_year(email)
        elif var_name == "month":
            return self._get_month(email)
        elif var_name == "day":
            return self._get_day(email)
        elif var_name == "from_domain":
            return self._get_from_domain(email)
        elif var_name == "subject_sanitized":
            return self._sanitize_subject(email.subject)
        elif var_name == "rule_name":
            return rule.name if rule else ""
        else:
            # Unknown variable - return empty string
            return ""
    
    def _get_year(self, email: Email) -> str:
        """Get 4-digit year from email date."""
        if email.date:
            return email.date.strftime("%Y")
        return "unknown"
    
    def _get_month(self, email: Email) -> str:
        """Get 2-digit month from email date."""
        if email.date:
            return email.date.strftime("%m")
        return "unknown"
    
    def _get_day(self, email: Email) -> str:
        """Get 2-digit day from email date."""
        if email.date:
            return email.date.strftime("%d")
        return "unknown"
    
    def _get_from_domain(self, email: Email) -> str:
        """
        Extract domain from sender's email address.
        
        Returns:
            Domain part of email address, or the original string if no @ symbol.
        """
        from_addr = email.from_addr
        if not from_addr:
            return "unknown"
        
        # Extract domain part (after @)
        if "@" in from_addr:
            domain = from_addr.split("@")[-1]
            # Sanitize domain to be filesystem-safe
            return self._sanitize_filename(domain)
        
        # Return the original string if no @ symbol (for invalid emails)
        return from_addr
    
    def _sanitize_subject(self, subject: Optional[str]) -> str:
        """
        Sanitize subject for use in filename.
        
        Args:
            subject: The email subject.
        
        Returns:
            Sanitized subject with invalid characters removed.
        """
        if not subject:
            return "untitled"
        
        # Sanitize the subject
        sanitized = self._sanitize_filename(subject)
        
        # Ensure non-empty
        if not sanitized:
            return "untitled"
        
        # Truncate if too long (filesystem limit)
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Remove invalid filename characters from a string.
        
        Args:
            name: The string to sanitize.
        
        Returns:
            Sanitized string safe for use as filename.
        """
        if not name:
            return ""
        
        # Replace invalid characters with underscores
        sanitized = name
        for char in self.INVALID_FILENAME_CHARS:
            sanitized = sanitized.replace(char, "_")
        
        # Replace multiple consecutive underscores with single
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Strip leading/trailing underscores and spaces
        sanitized = sanitized.strip("._ ")
        
        return sanitized
    
    def _normalize_separators(self, path: str) -> str:
        """
        Normalize path separators to OS-specific separators.
        
        Args:
            path: Path string with potentially mixed separators.
        
        Returns:
            Path with OS-specific separators.
        """
        # Replace forward slashes with OS-specific separator
        return path.replace("/", os.sep).replace("\\", os.sep)
    
    def build_filename(
        self,
        email: Email,
        extension: str = "eml",
        rule: Optional[Rule] = None
    ) -> str:
        """
        Build a filename from email data.
        
        Args:
            email: The email object.
            extension: File extension without dot.
            rule: Optional matched rule for rule name suffix.
        
        Returns:
            Sanitized filename with extension.
        """
        # Check if subject is empty or None - use timestamp-based name
        if not email.subject:
            base_name = f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        else:
            # Use subject as base filename
            base_name = self._sanitize_subject(email.subject)
            
            # Replace spaces with underscores for filename compatibility
            base_name = base_name.replace(" ", "_")
            
            # Append rule name if available
            if rule:
                base_name = f"{base_name}_{rule.name}"
        
        # Add extension
        filename = f"{base_name}.{extension}"
        
        return filename
