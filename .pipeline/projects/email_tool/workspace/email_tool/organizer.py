"""Organizer module for high-level orchestration of email processing."""

import os
import yaml
from typing import List, Optional, Dict, Any
from datetime import datetime

from email_tool.models import Email, Rule, RuleType, ActionType
from email_tool.parser import parse_email_file, parse_email_content
from email_tool.rules import RuleEngine, RuleMatchStrategy
from email_tool.config import (
    load_rules_from_yaml,
    load_rules_from_dict,
    validate_rule_config,
    validate_rule_config_file,
    ConfigValidationError,
)
from email_tool.path_builder import PathBuilder
from email_tool.formatter import Formatter
from email_tool.dispatcher import Dispatcher
from email_tool.processor import EmailProcessor, PipelineBuilder


class EmailOrganizer:
    """
    High-level orchestrator for email processing pipeline.
    
    Provides a simplified interface for organizing emails based on rules.
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        dry_run: bool = False,
        collision_strategy: str = "rename"
    ):
        """
        Initialize the email organizer.
        
        Args:
            base_path: Base directory for organized emails.
            dry_run: If True, only simulate actions without making changes.
            collision_strategy: Strategy for handling filename collisions.
        """
        self.base_path = os.path.abspath(base_path)
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.default_output_format = "eml"
        
        # Initialize processor
        self.processor = EmailProcessor(
            base_path=self.base_path,
            dry_run=dry_run,
            collision_strategy=collision_strategy
        )
        
        # Path builder with default template
        self.path_builder = PathBuilder()
    
    def load_rules(self, rules_path: str) -> List[Rule]:
        """
        Load rules from a YAML configuration file.
        
        Args:
            rules_path: Path to the YAML rules file.
        
        Returns:
            List of loaded Rule objects.
        
        Raises:
            ConfigValidationError: If the rules file is invalid.
        """
        return load_rules_from_yaml(rules_path)
    
    def load_rules_from_dict(self, rules_dict: dict) -> List[Rule]:
        """
        Load rules from a dictionary configuration.
        
        Args:
            rules_dict: Dictionary with rules configuration.
        
        Returns:
            List of loaded Rule objects.
        
        Raises:
            ConfigValidationError: If the rules configuration is invalid.
        """
        return load_rules_from_dict(rules_dict)
    
    def organize_email(
        self,
        email_source: str,
        rules: List[Rule],
        output_format: str = "eml"
    ) -> Dict[str, Any]:
        """
        Organize a single email using the provided rules.
        
        Args:
            email_source: Path to email file or email content.
            rules: List of rules to match against.
            output_format: Output format ('eml', 'md', or 'pdf').
        
        Returns:
            Dictionary with organization results.
        """
        # Parse the email
        email = parse_email_file(email_source) if os.path.isfile(email_source) \
            else parse_email_content(email_source)
        
        # Match against rules
        engine = RuleEngine(rules=rules)
        rule_matches = engine.evaluate(email)
        
        result = {
            "success": False,
            "email_id": email.id,
            "subject": email.subject,
            "from": email.from_addr,
            "date": email.date.isoformat() if email.date else None,
            "matches": [],
            "output_path": None,
            "errors": []
        }
        
        if rule_matches:
            # Get the highest priority match
            best_match = max(rule_matches, key=lambda m: m.priority)
            
            # Build output path
            output_path = self.path_builder.build_path(
                email=email,
                rule=best_match.rule
            )
            
            # Build filename
            filename = self.path_builder.build_filename(
                email=email,
                extension=output_format,
                rule=best_match.rule
            )
            
            # Combine path and filename
            full_path = os.path.join(self.base_path, output_path, filename)
            
            # Create directories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Format and save the email
            formatter = Formatter(email)
            if output_format == "eml":
                content = formatter.to_eml()
            elif output_format == "md":
                content = formatter.to_markdown()
            elif output_format == "pdf":
                # For PDF, we need to save to file
                formatter.to_pdf(full_path)
                result["output_path"] = full_path
                result["success"] = True
                return result
            else:
                result["errors"].append(f"Unknown format: {output_format}")
                return result
            
            if not self.dry_run:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            result["output_path"] = full_path
            result["success"] = True
            result["matches"].append({
                "rule_name": best_match.rule_name,
                "match_type": best_match.match_type,
                "priority": best_match.priority
            })
        else:
            result["errors"].append("No matching rules found")
        
        return result
    
    def organize_directory(
        self,
        source_dir: str,
        rules: List[Rule],
        output_format: str = "eml",
        file_pattern: str = "*.eml"
    ) -> Dict[str, Any]:
        """
        Organize all emails in a directory.
        
        Args:
            source_dir: Directory containing email files.
            rules: List of rules to match against.
            output_format: Output format ('eml', 'md', or 'pdf').
            file_pattern: File pattern to match.
        
        Returns:
            Dictionary with batch organization results.
        """
        import glob
        
        email_files = glob.glob(os.path.join(source_dir, file_pattern))
        
        results = []
        for email_file in email_files:
            result = self.organize_email(email_file, rules, output_format)
            results.append(result)
        
        return {
            "total_processed": len(results),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
    
    def organize_batch(
        self,
        email_sources: List[str],
        rules: List[Rule],
        output_format: str = "eml"
    ) -> Dict[str, Any]:
        """
        Organize multiple emails.
        
        Args:
            email_sources: List of email file paths or content.
            rules: List of rules to match against.
            output_format: Output format ('eml', 'md', or 'pdf').
        
        Returns:
            Dictionary with batch organization results.
        """
        results = []
        
        for source in email_sources:
            result = self.organize_email(source, rules, output_format)
            results.append(result)
        
        return {
            "total_processed": len(results),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics.
        """
        return self.processor.get_stats()
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.processor.reset_stats()
    
    def set_path_template(self, template: str):
        """
        Set the path template for organizing emails.
        
        Args:
            template: Path template string with variable placeholders.
        """
        self.path_builder = PathBuilder(template=template)
    
    def set_output_format(self, format: str):
        """
        Set the default output format.
        
        Args:
            format: Output format ('eml', 'md', or 'pdf').
        """
        if format not in ["eml", "md", "pdf"]:
            raise ValueError(f"Invalid format: {format}. Must be 'eml', 'md', or 'pdf'.")
        self.default_output_format = format


class OrganizerBuilder:
    """
    Builder for constructing email organizers.
    """
    
    def __init__(self):
        """Initialize the organizer builder."""
        self.base_path = "./archive"
        self.dry_run = False
        self.collision_strategy = "rename"
        self.rules: List[Rule] = []
        self.path_template = "{{year}}/{{month}}/{{from_domain}}/{{subject_sanitized}}"
    
    def set_base_path(self, path: str) -> 'OrganizerBuilder':
        """Set the base path for organized emails."""
        self.base_path = path
        return self
    
    def set_dry_run(self, dry_run: bool) -> 'OrganizerBuilder':
        """Set dry run mode."""
        self.dry_run = dry_run
        return self
    
    def set_collision_strategy(self, strategy: str) -> 'OrganizerBuilder':
        """Set collision handling strategy."""
        self.collision_strategy = strategy
        return self
    
    def set_path_template(self, template: str) -> 'OrganizerBuilder':
        """Set the path template."""
        self.path_template = template
        return self
    
    def add_rule(self, rule: Rule) -> 'OrganizerBuilder':
        """Add a rule to the organizer."""
        self.rules.append(rule)
        return self
    
    def add_rules(self, rules: List[Rule]) -> 'OrganizerBuilder':
        """Add multiple rules to the organizer."""
        self.rules.extend(rules)
        return self
    
    def load_rules_from_file(self, rules_path: str) -> 'OrganizerBuilder':
        """
        Load rules from a YAML file.
        
        Args:
            rules_path: Path to the YAML rules file.
        
        Returns:
            Self for method chaining.
        """
        loaded_rules = load_rules_from_yaml(rules_path)
        self.rules.extend(loaded_rules)
        return self
    
    def build(self) -> EmailOrganizer:
        """
        Build the email organizer.
        
        Returns:
            Configured EmailOrganizer instance.
        """
        organizer = EmailOrganizer(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy
        )
        organizer.set_path_template(self.path_template)
        return organizer


def create_organizer(
    base_path: str = "./archive",
    dry_run: bool = False,
    collision_strategy: str = "rename",
    rules_path: Optional[str] = None
) -> EmailOrganizer:
    """
    Factory function to create and configure an email organizer.
    
    Args:
        base_path: Base directory for organized emails.
        dry_run: If True, only simulate actions.
        collision_strategy: Strategy for filename collisions.
        rules_path: Optional path to YAML rules file.
    
    Returns:
        Configured EmailOrganizer instance.
    """
    organizer = EmailOrganizer(
        base_path=base_path,
        dry_run=dry_run,
        collision_strategy=collision_strategy
    )
    
    if rules_path:
        organizer.load_rules(rules_path)
    
    return organizer
