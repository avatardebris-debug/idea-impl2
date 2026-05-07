"""API spec generator that produces YAML/JSON output from parsed AST data."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import yaml

from docsai.generators.base import BaseGenerator


class ApiSpecGenerator(BaseGenerator):
    """Generate structured API specs in YAML or JSON format."""

    def generate(
        self,
        symbols: List[Dict[str, Any]],
        output_format: str = "yaml",
        project_name: str = "unknown",
        language: str = "unknown",
    ) -> str:
        """Generate an API spec document.

        Args:
            symbols: List of parsed symbol dicts.
            output_format: 'yaml' or 'json'.
            project_name: Name of the project.
            language: Primary language of the project.

        Returns:
            A string containing the formatted API spec.
        """
        spec: Dict[str, Any] = {
            "project_name": project_name,
            "language": language,
            "symbols": symbols,
            "metadata": {
                "file_count": len(set(s.get("file", "") for s in symbols)),
                "total_symbols": len(symbols),
            },
        }

        if output_format == "json":
            return json.dumps(spec, indent=2, ensure_ascii=False)
        else:
            return yaml.dump(spec, default_flow_style=False, allow_unicode=True, sort_keys=False)
