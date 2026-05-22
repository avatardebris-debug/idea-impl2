"""Export functionality for SOPs and configurations."""

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .sop_schema import SOP, SOPInput
from .sop_store import SOPStore


class Exporter:
    """Handles exporting SOPs and configurations to various formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the exporter.
        
        Args:
            output_dir: Directory to save exported files. Defaults to current directory.
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_sop_to_json(self, sop: SOP, filename: Optional[str] = None) -> Path:
        """Export a single SOP to JSON format.
        
        Args:
            sop: The SOP to export.
            filename: Optional filename (without .json extension). Defaults to SOP ID.
            
        Returns:
            Path to the exported file.
        """
        if not filename:
            filename = f"{sop.id}_export"
        
        filepath = self.output_dir / f"{filename}.json"
        
        export_data = {
            "id": sop.id,
            "title": sop.title,
            "description": sop.description,
            "version": sop.version,
            "created_at": sop.created_at,
            "updated_at": sop.updated_at,
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "description": step.description,
                    "agent_type": step.agent_type,
                    "input_schema": step.input_schema,
                    "output_schema": step.output_schema,
                    "retry_policy": step.retry_policy,
                }
                for step in sop.steps
            ],
            "input_schema": sop.input_schema,
            "output_schema": sop.output_schema,
        }
        
        filepath.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        return filepath

    def export_sop_to_yaml(self, sop: SOP, filename: Optional[str] = None) -> Path:
        """Export a single SOP to YAML format.
        
        Args:
            sop: The SOP to export.
            filename: Optional filename (without .yaml extension). Defaults to SOP ID.
            
        Returns:
            Path to the exported file.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML export. Install with: pip install pyyaml")
        
        if not filename:
            filename = f"{sop.id}_export"
        
        filepath = self.output_dir / f"{filename}.yaml"
        
        export_data = {
            "id": sop.id,
            "title": sop.title,
            "description": sop.description,
            "version": sop.version,
            "created_at": sop.created_at,
            "updated_at": sop.updated_at,
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "description": step.description,
                    "agent_type": step.agent_type,
                    "input_schema": step.input_schema,
                    "output_schema": step.output_schema,
                    "retry_policy": step.retry_policy,
                }
                for step in sop.steps
            ],
            "input_schema": sop.input_schema,
            "output_schema": sop.output_schema,
        }
        
        filepath.write_text(yaml.dump(export_data, default_flow_style=False, sort_keys=False), encoding="utf-8")
        return filepath

    def export_sop_to_csv(self, sop: SOP, filename: Optional[str] = None) -> Path:
        """Export a single SOP's steps to CSV format.
        
        Args:
            sop: The SOP to export.
            filename: Optional filename (without .csv extension). Defaults to SOP ID.
            
        Returns:
            Path to the exported file.
        """
        if not filename:
            filename = f"{sop.id}_steps"
        
        filepath = self.output_dir / f"{filename}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Step ID', 'Title', 'Description', 'Agent Type', 'Retry Policy'])
            
            for step in sop.steps:
                writer.writerow([
                    step.id,
                    step.title,
                    step.description,
                    step.agent_type,
                    step.retry_policy.get('max_retries', 0) if step.retry_policy else 0
                ])
        
        return filepath

    def export_sop_to_markdown(self, sop: SOP, filename: Optional[str] = None) -> Path:
        """Export a single SOP to Markdown format.
        
        Args:
            sop: The SOP to export.
            filename: Optional filename (without .md extension). Defaults to SOP ID.
            
        Returns:
            Path to the exported file.
        """
        if not filename:
            filename = f"{sop.id}_export"
        
        filepath = self.output_dir / f"{filename}.md"
        
        lines = [
            f"# {sop.title}",
            "",
            f"**ID:** {sop.id}",
            f"**Version:** {sop.version}",
            "",
            f"## Description",
            "",
            sop.description,
            "",
            f"## Input Schema",
            "",
            "```json",
            json.dumps(sop.input_schema, indent=2),
            "```",
            "",
            f"## Output Schema",
            "",
            "```json",
            json.dumps(sop.output_schema, indent=2),
            "```",
            "",
            f"## Steps",
            "",
        ]
        
        for step in sop.steps:
            lines.extend([
                f"### {step.title}",
                "",
                f"**ID:** {step.id}",
                f"**Agent Type:** {step.agent_type}",
                "",
                step.description,
                "",
                f"#### Input Schema",
                "",
                "```json",
                json.dumps(step.input_schema, indent=2),
                "```",
                "",
                f"#### Output Schema",
                "",
                "```json",
                json.dumps(step.output_schema, indent=2),
                "```",
                "",
                f"#### Retry Policy",
                "",
                f"- Max Retries: {step.retry_policy.get('max_retries', 0) if step.retry_policy else 0}",
                f"- Retry Delay: {step.retry_policy.get('retry_delay', 1) if step.retry_policy else 1}s",
                "",
                "---",
                "",
            ])
        
        filepath.write_text('\n'.join(lines), encoding="utf-8")
        return filepath

    def export_all_sops(self, sop_store: SOPStore, format: str = "json", 
                        filename_prefix: Optional[str] = None) -> List[Path]:
        """Export all SOPs from a store to the specified format.
        
        Args:
            sop_store: The SOP store to export from.
            format: Export format ('json', 'yaml', 'csv', 'markdown').
            filename_prefix: Optional prefix for exported filenames.
            
        Returns:
            List of paths to exported files.
        """
        exported_files = []
        sops = sop_store.list_sops()
        
        for sop in sops:
            if format == "json":
                filepath = self.export_sop_to_json(sop, f"{filename_prefix}_{sop.id}" if filename_prefix else None)
            elif format == "yaml":
                filepath = self.export_sop_to_yaml(sop, f"{filename_prefix}_{sop.id}" if filename_prefix else None)
            elif format == "csv":
                filepath = self.export_sop_to_csv(sop, f"{filename_prefix}_{sop.id}" if filename_prefix else None)
            elif format == "markdown":
                filepath = self.export_sop_to_markdown(sop, f"{filename_prefix}_{sop.id}" if filename_prefix else None)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            exported_files.append(filepath)
        
        return exported_files

    def export_results_to_csv(self, results: List[Dict[str, Any]], 
                             filename: Optional[str] = None) -> Path:
        """Export execution results to CSV format.
        
        Args:
            results: List of execution result dictionaries.
            filename: Optional filename (without .csv extension). Defaults to timestamp.
            
        Returns:
            Path to the exported file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}"
        
        filepath = self.output_dir / f"{filename}.csv"
        
        if not results:
            # Create empty file with headers
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['SOP ID', 'Status', 'Started At', 'Completed At', 'Error'])
            return filepath
        
        # Determine all possible keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        fieldnames = ['sop_id', 'status', 'started_at', 'completed_at', 'error']
        fieldnames.extend(sorted(all_keys - set(fieldnames)))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        return filepath

    def export_config_to_json(self, config: Dict[str, Any], 
                             filename: Optional[str] = None) -> Path:
        """Export configuration to JSON format.
        
        Args:
            config: Configuration dictionary to export.
            filename: Optional filename (without .json extension). Defaults to 'config'.
            
        Returns:
            Path to the exported file.
        """
        if not filename:
            filename = "config"
        
        filepath = self.output_dir / f"{filename}.json"
        filepath.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return filepath

    def export_all(self, sop_store: SOPStore, format: str = "json",
                   include_results: bool = False,
                   filename_prefix: Optional[str] = None) -> List[Path]:
        """Export all SOPs and optionally results.
        
        Args:
            sop_store: The SOP store to export from.
            format: Export format ('json', 'yaml', 'csv', 'markdown').
            include_results: Whether to include execution results.
            filename_prefix: Optional prefix for exported filenames.
            
        Returns:
            List of paths to exported files.
        """
        exported_files = self.export_all_sops(sop_store, format, filename_prefix)
        
        if include_results:
            # This would need access to results store
            # For now, just return the SOP exports
            pass
        
        return exported_files
