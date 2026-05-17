"""Python source parser using tree-sitter."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import tree_sitter_python
from tree_sitter import Language, Parser, Node


class PythonParser:
    """Parse Python source files and extract public symbols."""

    LANGUAGES = ["python"]

    def __init__(self):
        self._parser = Parser(Language(tree_sitter_python.language()))

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a Python file and return a list of public symbol dicts."""
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = self._parser.parse(bytes(source, "utf-8"))
        root = tree.root_node

        symbols: List[Dict[str, Any]] = []
        self._extract_symbols(root, source, symbols, kind_prefix="")
        return symbols

    def _extract_symbols(
        self,
        node: Node,
        source: str,
        symbols: List[Dict[str, Any]],
        kind_prefix: str,
    ) -> None:
        """Recursively extract public symbols from the AST."""
        for child in node.children:
            name = child.type

            if name == "class_definition":
                class_name_node = child.child_by_field_name("name")
                if class_name_node and not class_name_node.text.decode("utf-8").startswith("_"):
                    class_name = class_name_node.text.decode("utf-8")
                    symbols.append({
                        "name": class_name,
                        "kind": f"{kind_prefix}class",
                        "params": [],
                        "return_type": "",
                        "docstring": self._get_docstring(child, source),
                        "line_number": child.start_point[0] + 1,
                    })
                    self._extract_symbols(child, source, symbols, kind_prefix=f"{class_name}.")
                continue

            if name == "function_definition":
                func_name_node = child.child_by_field_name("name")
                if func_name_node:
                    func_name = func_name_node.text.decode("utf-8")
                    if not func_name.startswith("_"):
                        params = self._extract_params(child)
                        return_type = self._extract_return_type(child)
                        kind = "method" if kind_prefix else "function"
                        symbols.append({
                            "name": func_name,
                            "kind": kind,
                            "params": params,
                            "return_type": return_type,
                            "docstring": self._get_docstring(child, source),
                            "line_number": child.start_point[0] + 1,
                        })
                continue

            # Recurse into children for nested definitions
            if child.child_count > 0:
                self._extract_symbols(child, source, symbols, kind_prefix)

    def _extract_params(self, func_node: Node) -> List[Dict[str, str]]:
        """Extract parameter list from a function definition."""
        params: List[Dict[str, str]] = []
        params_node = func_node.child_by_field_name("parameters")
        if not params_node:
            return params

        for arg in params_node.children:
            if arg.type == "identifier":
                param_name = arg.text.decode("utf-8")
                if param_name in ("self", "cls"):
                    continue
                params.append({"name": param_name, "type": ""})
            elif arg.type == "typed_parameter":
                # tree-sitter-python: first named child is the identifier (no field name),
                # child_by_field_name("type") returns the type annotation.
                named = arg.named_children
                if not named:
                    continue
                name_node = named[0]  # identifier
                type_node = arg.child_by_field_name("type")
                param_name = name_node.text.decode("utf-8")
                param_type = type_node.text.decode("utf-8") if type_node else ""
                if param_name not in ("self", "cls"):
                    params.append({"name": param_name, "type": param_type})
            elif arg.type == "default_parameter":
                # identifier = first named child; value = second
                named = arg.named_children
                if not named:
                    continue
                param_name = named[0].text.decode("utf-8")
                params.append({"name": param_name, "type": ""})

        return params

    def _extract_return_type(self, func_node: Node) -> str:
        """Extract return type annotation from a function definition."""
        annotation = func_node.child_by_field_name("return_type")
        if annotation:
            return annotation.text.decode("utf-8")
        return ""

    def _get_docstring(self, node: Node, source: str) -> str:
        """Extract docstring from a function or class definition."""
        # The first child after the function/class header is typically the docstring
        body = node.child_by_field_name("body")
        if not body:
            return ""

        # Look for a string literal as the first statement in the body
        if body.type == "block":
            first_stmt = body.children[0] if body.children else None
            if first_stmt and first_stmt.type == "expression_statement":
                expr = first_stmt.children[0] if first_stmt.children else None
                if expr and expr.type in ("string", "concatenated_string"):
                    # Extract the raw text
                    text = expr.text.decode("utf-8")
                    # Remove surrounding quotes
                    if (text.startswith('"""') and text.endswith('"""')) or \
                       (text.startswith("'''") and text.endswith("'''")):
                        return text[3:-3].strip()
                    elif (text.startswith('"') and text.endswith('"')) or \
                         (text.startswith("'") and text.endswith("'")):
                        return text[1:-1].strip()
                    return text.strip()

        return ""
