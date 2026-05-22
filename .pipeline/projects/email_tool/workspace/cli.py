#!/usr/bin/env python3
"""
Email Tool - Command Line Interface

A flexible email processing tool that can parse, match, and dispatch
actions on email files based on configurable rules.

Supports YAML configuration via ~/.email_tool/config.yaml
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import yaml

from email_tool.models import Rule, RuleType, ActionType
from email_tool.processor import EmailProcessor, PipelineBuilder, PipelineConfig
from email_tool.organizer import EmailOrganizer, create_organizer
from email_tool.config import load_config, EmailToolConfig, load_rules_from_yaml, validate_rule_config_file
from email_tool.attachment_processor import AttachmentProcessor
from email_tool.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

# Default configuration paths
DEFAULT_CONFIG_DIR = Path.home() / ".email_tool"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_RULES_FILE = Path.cwd() / "rules.yaml"
DEFAULT_ACTIONS_FILE = Path.cwd() / "actions.yaml"


class EmailToolCLI:
    """Command-line interface for Email Tool."""
    
    def __init__(self, config: Optional[EmailToolConfig] = None, verbose: bool = False, debug: bool = False):
        """Initialize CLI.
        
        Args:
            config: Configuration instance. If None, loads from default location.
            verbose: Enable verbose output
            debug: Enable debug output
        """
        self.config = config or EmailToolConfig()
        self.verbose = verbose
        self.debug = debug
        
        # Setup logging
        if debug:
            log_level = logging.DEBUG
        elif verbose:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING
        
        setup_logging(log_level)
        logger.debug("CLI initialized with debug=%s, verbose=%s", debug, verbose)
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI.
        
        Args:
            args: Command line arguments. If None, uses sys.argv[1:]
            
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        if args is None:
            args = sys.argv[1:]
        
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        # Handle global flags
        if hasattr(parsed_args, 'verbose') and parsed_args.verbose:
            self.verbose = True
        if hasattr(parsed_args, 'debug') and parsed_args.debug:
            self.debug = True
        
        # Load config if provided
        if hasattr(parsed_args, 'config') and parsed_args.config:
            config_path = Path(parsed_args.config)
            if config_path.exists():
                self.config = load_config(config_path)
                logger.info("Loaded config from %s", config_path)
        
        # Execute command
        try:
            if parsed_args.command == 'version':
                return self._cmd_version(parsed_args)
            elif parsed_args.command == 'init':
                return self._cmd_init(parsed_args)
            elif parsed_args.command == 'scan':
                return self._cmd_scan(parsed_args)
            elif parsed_args.command == 'organize':
                return self._cmd_organize(parsed_args)
            elif parsed_args.command == 'sync':
                return self._cmd_sync(parsed_args)
            elif parsed_args.command == 'rules':
                return self._cmd_rules(parsed_args)
            elif parsed_args.command == 'summary':
                return self._cmd_summary(parsed_args)
            elif parsed_args.command == 'dry-run':
                return self._cmd_dry_run(parsed_args)
            else:
                parser.print_help()
                return 1
        except Exception as e:
            logger.exception("Error executing command: %s", e)
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog='email_tool',
            description='Email processing tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  email_tool init                    Initialize configuration
  email_tool scan /path/to/emails    Scan emails
  email_tool organize /path/to/emails --output /path/to/output
  email_tool rules --validate rules.yaml
  email_tool summary /path/to/emails
  email_tool dry-run /path/to/emails --rules rules.yaml
            """
        )
        
        # Global options
        parser.add_argument('--config', '-c', type=str, help='Path to configuration file')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
        parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
        
        # Subparsers
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Version command
        subparsers.add_parser('version', help='Show version information')
        
        # Init command
        init_parser = subparsers.add_parser('init', help='Initialize configuration')
        init_parser.add_argument('--config-dir', type=str, default=str(DEFAULT_CONFIG_DIR),
                                help='Configuration directory (default: ~/.email_tool)')
        init_parser.add_argument('--force', '-f', action='store_true',
                                help='Overwrite existing configuration')
        
        # Scan command
        scan_parser = subparsers.add_parser('scan', help='Scan emails')
        scan_parser.add_argument('path', type=str, help='Path to scan')
        scan_parser.add_argument('--rules', '-r', type=str, help='Path to rules file')
        scan_parser.add_argument('--pattern', '-p', type=str, default='*.eml',
                                help='File pattern to match (default: *.eml)')
        scan_parser.add_argument('--output', '-o', type=str, help='Output file for results')
        
        # Organize command
        organize_parser = subparsers.add_parser('organize', help='Organize emails')
        organize_parser.add_argument('path', type=str, help='Path to organize')
        organize_parser.add_argument('--output', '-o', type=str, required=True,
                                    help='Output directory')
        organize_parser.add_argument('--rules', '-r', type=str, help='Path to rules file')
        organize_parser.add_argument('--dry-run', action='store_true',
                                    help='Preview without making changes')
        organize_parser.add_argument('--format', '-f', type=str, default='text',
                                    choices=['text', 'json'], help='Output format')
        
        # Sync command
        sync_parser = subparsers.add_parser('sync', help='Sync emails')
        sync_parser.add_argument('--interval', '-i', type=int, default=300,
                                help='Sync interval in seconds (default: 300)')
        sync_parser.add_argument('--once', action='store_true',
                                help='Run once and exit')
        
        # Rules command
        rules_parser = subparsers.add_parser('rules', help='Rules management')
        rules_parser.add_argument('--list', '-l', action='store_true',
                                 help='List rules')
        rules_parser.add_argument('--validate', '-v', type=str,
                                 help='Validate rules file')
        rules_parser.add_argument('--config', '-c', type=str,
                                 help='Path to configuration file')
        
        # Summary command
        summary_parser = subparsers.add_parser('summary', help='Generate summary')
        summary_parser.add_argument('path', type=str, help='Path to summarize')
        summary_parser.add_argument('--format', '-f', type=str, default='text',
                                   choices=['text', 'json'], help='Output format')
        summary_parser.add_argument('--output', '-o', type=str, help='Output file')
        
        # Dry-run command
        dry_run_parser = subparsers.add_parser('dry-run', help='Preview rule matching')
        dry_run_parser.add_argument('path', type=str, help='Path to scan')
        dry_run_parser.add_argument('--rules', '-r', type=str, help='Path to rules file')
        dry_run_parser.add_argument('--pattern', '-p', type=str, default='*.eml',
                                   help='File pattern to match')
        
        return parser
    
    def _cmd_version(self, args: argparse.Namespace) -> int:
        """Show version information."""
        print("email_tool version 1.0.0")
        return 0
    
    def _cmd_init(self, args: argparse.Namespace) -> int:
        """Initialize configuration."""
        config_dir = Path(args.config_dir)
        
        # Check if directory exists
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created config directory: %s", config_dir)
        
        config_file = config_dir / "config.yaml"
        
        # Check if file exists
        if config_file.exists() and not args.force:
            print(f"Configuration already exists at {config_file}")
            print("Use --force to overwrite")
            return 1
        
        # Create default configuration
        default_config = {
            'log_level': 'INFO',
            'rules': {
                'path': str(DEFAULT_RULES_FILE)
            },
            'actions': {
                'path': str(DEFAULT_ACTIONS_FILE)
            },
            'output': {
                'path': str(Path.cwd() / 'output')
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"Configuration initialized at {config_file}")
        print(f"Log level: {default_config['log_level']}")
        print(f"Rules file: {default_config['rules']['path']}")
        print(f"Actions file: {default_config['actions']['path']}")
        print(f"Output directory: {default_config['output']['path']}")
        
        return 0
    
    def _cmd_scan(self, args: argparse.Namespace) -> int:
        """Scan emails."""
        path = Path(args.path)
        rules_path = Path(args.rules) if args.rules else None
        
        # Load rules
        rules = []
        if rules_path:
            if not rules_path.exists():
                print(f"Error: Rules file not found: {rules_path}")
                return 1
            rules = load_rules_from_yaml(rules_path)
            print(f"Loaded {len(rules)} rules from {rules_path}")
        
        # Create processor
        processor = EmailProcessor(rules=rules)
        
        # Scan directory
        results = processor.scan_directory(path, pattern=args.pattern)
        
        # Output results
        print("\nScan Results:")
        print("=" * 60)
        print(f"Total files: {results.get('total_files', 0)}")
        print(f"Matched files: {results.get('matched_files', 0)}")
        print(f"Unmatched files: {results.get('unmatched_files', 0)}")
        print()
        
        if results.get('matched_files'):
            print("Matched Files:")
            for file_info in results['matched_files']:
                print(f"  {file_info['file']}")
                print(f"    -> {file_info.get('category', 'unknown')}/")
                print(f"    Rule: {file_info['rule_name']}")
            print()
        
        if results.get('unmatched_files'):
            print("Unmatched Files:")
            for file_info in results['unmatched_files']:
                print(f"  {file_info['file']}")
            print()
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")
        
        return 0
    
    def _cmd_organize(self, args: argparse.Namespace) -> int:
        """Organize emails."""
        path = Path(args.path)
        output_path = Path(args.output)
        rules_path = Path(args.rules) if args.rules else None
        
        # Load rules
        rules = []
        if rules_path:
            if not rules_path.exists():
                print(f"Error: Rules file not found: {rules_path}")
                return 1
            rules = load_rules_from_yaml(rules_path)
            print(f"Loaded {len(rules)} rules from {rules_path}")
        
        # Create organizer
        organizer = EmailOrganizer(base_path=str(output_path), dry_run=args.dry_run)
        
        # Organize
        results = organizer.organize_directory(
            str(path),
            rules=rules
        )
        
        # Output results
        print("\nOrganization Results:")
        print("=" * 60)
        print(f"Total files: {results.get('total_processed', 0)}")
        print(f"Organized: {results.get('successful', 0)}")
        print(f"Skipped: {results.get('failed', 0)}")
        print()
        
        if args.dry_run:
            print("Dry run - no changes were made")
        
        return 0
    
    def _cmd_sync(self, args: argparse.Namespace) -> int:
        """Sync emails."""
        # This is a placeholder for future sync functionality
        print("Sync functionality not yet implemented")
        print("Use --once to run a single sync cycle")
        
        if args.once:
            print("Running single sync cycle...")
            # TODO: Implement actual sync logic
            print("Sync complete")
        
        return 0
    
    def _cmd_rules(self, args: argparse.Namespace) -> int:
        """Manage rules."""
        if args.validate:
            # Validate rules file
            rules_path = Path(args.validate)
            if not rules_path.exists():
                print(f"Error: Rules file not found: {rules_path}")
                return 1
            
            try:
                errors = validate_rule_config_file(str(rules_path))
                if errors:
                    print("Validation failed:")
                    for error in errors:
                        print(f"  ✗ {error}")
                    return 1
                
                print(f"Rules file is valid: {rules_path}")
                rules = load_rules_from_yaml(str(rules_path))
                print(f"Loaded {len(rules)} valid rules")
                return 0
            except Exception as e:
                print(f"Validation failed: {e}")
                return 1
        
        if args.list:
            # List rules from config
            rules_path = DEFAULT_RULES_FILE
            if self.config:
                configured_rules_path = self.config.get_rules_path()
                if configured_rules_path:
                    rules_path = Path(configured_rules_path)
            
            if not rules_path.exists():
                print(f"Rules file not found: {rules_path}")
                return 1
            
            rules = load_rules_from_yaml(str(rules_path))
            print(f"Rules from {rules_path}:")
            for rule in rules:
                print(f"  - {rule.name} ({rule.rule_type.value})")
            
            return 0
        
        # Default: show help
        print("Rules management commands:")
        print("  --list, -l    List rules")
        print("  --validate, -v  Validate rules file")
        print("  --config, -c  Path to configuration file")
        
        return 0
    
    def _cmd_summary(self, args: argparse.Namespace) -> int:
        """Generate summary of organized emails."""
        path = Path(args.path)
        
        if not path.exists():
            print(f"Error: Path not found: {path}")
            return 1
        
        # Generate summary
        summary = {
            'path': str(path),
            'generated_at': datetime.now().isoformat(),
            'total_files': 0,
            'categories': {},
            'recent_files': []
        }
        
        # Walk directory and collect stats
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                summary['total_files'] += 1
                
                # Get category from directory name
                category = Path(root).name
                summary['categories'][category] = summary['categories'].get(category, 0) + 1
                
                # Track recent files
                if len(summary['recent_files']) < 10:
                    stat = file_path.stat()
                    summary['recent_files'].append({
                        'file': file,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Output results
        if args.format == 'json':
            output = json.dumps(summary, indent=2)
        else:
            output = self._format_summary(summary)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Summary saved to {args.output}")
        else:
            print(output)
        
        return 0
    
    def _format_summary(self, summary: Dict[str, Any]) -> str:
        """Format summary for text output."""
        lines = []
        lines.append(f"Email Organization Summary")
        lines.append("=" * 60)
        lines.append(f"Path: {summary['path']}")
        lines.append(f"Generated: {summary['generated_at']}")
        lines.append(f"Total files: {summary['total_files']}")
        lines.append("")
        lines.append("Categories:")
        for category, count in sorted(summary['categories'].items()):
            lines.append(f"  {category}: {count}")
        lines.append("")
        lines.append("Recent files:")
        for file_info in summary['recent_files']:
            lines.append(f"  - {file_info['file']} ({file_info['size']} bytes)")
        
        return "\n".join(lines)
    
    def _cmd_dry_run(self, args: argparse.Namespace) -> int:
        """Preview rule matching without changes."""
        path = Path(args.path)
        rules_path = Path(args.rules) if args.rules else None
        
        # Load rules
        rules = []
        if rules_path:
            if not rules_path.exists():
                print(f"Error: Rules file not found: {rules_path}")
                return 1
            rules = load_rules_from_yaml(rules_path)
            print(f"Loaded {len(rules)} rules from {rules_path}")
        
        # Create processor
        processor = EmailProcessor(rules=rules)
        
        # Scan files
        results = processor.scan_directory(path, pattern=args.pattern)
        
        # Output results
        print("\nDry Run Results:")
        print("=" * 60)
        print(f"Total files: {results.get('total_files', 0)}")
        print(f"Matched files: {results.get('matched_files', 0)}")
        print(f"Unmatched files: {results.get('unmatched_files', 0)}")
        print()
        
        if results.get('matched_files'):
            print("Matched Files:")
            for file_info in results['matched_files']:
                print(f"  {file_info['file']}")
                print(f"    -> {file_info.get('category', 'unknown')}/")
                print(f"    Rule: {file_info['rule_name']}")
            print()
        
        if results.get('unmatched_files'):
            print("Unmatched Files:")
            for file_info in results['unmatched_files']:
                print(f"  {file_info['file']}")
            print()
        
        return 0


def main():
    """Main entry point."""
    # Parse global arguments
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument('--config', '-c', type=str)
    global_parser.add_argument('--verbose', '-v', action='store_true')
    global_parser.add_argument('--debug', '-d', action='store_true')
    
    global_args, remaining_args = global_parser.parse_known_args()
    
    # Load config if provided
    config = None
    if global_args.config:
        config = load_config(Path(global_args.config))
    
    # Create CLI instance
    cli = EmailToolCLI(config=config, verbose=global_args.verbose, debug=global_args.debug)
    
    # Run CLI
    return cli.run(remaining_args)


if __name__ == "__main__":
    sys.exit(main())
