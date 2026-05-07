"""TypeScript source parser using tree-sitter."""

from __future__ import annotations

from typing import Any, Dict, List

import tree_sitter_typescript
from tree_sitter import Language, Parser, Node


class TypeScriptParser:
    """Parse TypeScript source files and extract public symbols."""

    LANGUAGES = ["typescript", "tsx"]

    def __init__(self):
        lang = tree_sitter_typescript.language_typescript()
        self._parser = Parser(Language(lang))

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a TypeScript file and return a list of public symbol dicts."""
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = self._parser.parse(bytes(source, "utf-8"))
        root = tree.root_node

        symbols: List[Dict[str, Any]] = []
        self._extract_symbols(root, source, symbols, kind_prefix="")
        return symbols

    def _is_exported(self, node: Node) -> bool:
        """Check if a node is exported by looking at ancestors."""
        current = node
        while current:
            if current.type == "export_statement":
                return True
            current = current.parent
        return False

    def _is_public_name(self, name: str) -> bool:
        """Check if a name is public (not starting with _)."""
        return not name.startswith("_")

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

            if name == "function_declaration":
                self._handle_function(child, source, symbols, kind_prefix)
            elif name == "class_declaration":
                self._handle_class(child, source, symbols, kind_prefix)
            elif name == "interface_declaration":
                self._handle_interface(child, source, symbols, kind_prefix)
            elif name == "type_alias_declaration":
                self._handle_type_alias(child, source, symbols, kind_prefix)
            elif name == "enum_declaration":
                self._handle_enum(child, source, symbols, kind_prefix)
            elif name == "variable_declarator":
                self._handle_variable(child, source, symbols, kind_prefix)
            elif name == "export_statement":
                # Recurse into export to find the exported declaration
                self._extract_symbols(child, source, symbols, kind_prefix)
            elif name == "import_statement":
                pass  # Skip imports
            else:
                # Recurse into other nodes
                self._extract_symbols(child, source, symbols, kind_prefix)

    def _handle_function(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if not self._is_public_name(name):
            return
        if not self._is_exported(node):
            return

        params = self._extract_params(node)
        return_type = self._extract_return_type(node)
        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}function",
            "params": params,
            "return_type": return_type,
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_class(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if not self._is_public_name(name):
            return
        if not self._is_exported(node):
            return

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}class",
            "params": [],
            "return_type": "",
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

        # Extract class members
        body = node.child_by_field_name("body")
        if body:
            for member in body.children:
                if member.type == "method_definition":
                    self._handle_method(member, source, symbols, f"{name}.")
                elif member.type == "public_field_definition":
                    self._handle_field(member, source, symbols, f"{name}.")

    def _handle_method(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if name.startswith("_"):
            return

        params = self._extract_params(node)
        return_type = self._extract_return_type(node)
        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}method",
            "params": params,
            "return_type": return_type,
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_interface(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if not self._is_public_name(name):
            return
        if not self._is_exported(node):
            return

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}interface",
            "params": [],
            "return_type": "",
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_type_alias(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if not self._is_public_name(name):
            return
        if not self._is_exported(node):
            return

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}type",
            "params": [],
            "return_type": "",
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_enum(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if not self._is_public_name(name):
            return
        if not self._is_exported(node):
            return

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}enum",
            "params": [],
            "return_type": "",
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_variable(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if name.startswith("_"):
            return
        if not self._is_exported(node):
            return

        type_node = node.child_by_field_name("type")
        return_type = type_node.text.decode("utf-8") if type_node else ""

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}variable",
            "params": [],
            "return_type": return_type,
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _handle_field(
        self, node: Node, source: str, symbols: List[Dict[str, Any]], kind_prefix: str
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        if name.startswith("_"):
            return

        type_node = node.child_by_field_name("type")
        field_type = type_node.text.decode("utf-8") if type_node else ""

        symbols.append({
            "name": name,
            "kind": f"{kind_prefix}field",
            "params": [],
            "return_type": field_type,
            "docstring": self._get_docstring(node, source),
            "line_number": node.start_point[0] + 1,
        })

    def _extract_params(self, func_node: Node) -> List[Dict[str, str]]:
        """Extract parameter list from a function/method definition."""
        params: List[Dict[str, str]] = []
        params_node = func_node.child_by_field_name("parameters")
        if not params_node:
            return params

        for param in params_node.children:
            if param.type == "identifier":
                name = param.text.decode("utf-8")
                if name not in ("self", "this"):
                    params.append({"name": name, "type": ""})
            elif param.type in ("optional_parameter", "rest_parameter"):
                name_node = param.child_by_field_name("name")
                type_node = param.child_by_field_name("type")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    type_str = type_node.text.decode("utf-8") if type_node else ""
                    params.append({"name": name, "type": type_str})
            elif param.type == "typed_parameter":
                name_node = param.child_by_field_name("name")
                type_node = param.child_by_field_name("type")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    type_str = type_node.text.decode("utf-8") if type_node else ""
                    params.append({"name": name, "type": type_str})
            elif param.type == "pair":
                key = param.child_by_field_name("key")
                value = param.child_by_field_name("value")
                if key and value:
                    name = key.text.decode("utf-8")
                    type_str = value.text.decode("utf-8")
                    params.append({"name": name, "type": type_str})

        return params

    def _extract_return_type(self, func_node: Node) -> str:
        """Extract return type annotation."""
        annotation = func_node.child_by_field_name("return_type")
        if annotation:
            return annotation.text.decode("utf-8")
        return ""

    def _get_docstring(self, node: Node, source: str) -> str:
        """Extract JSDoc comment from a node."""
        prev = node.prev_named_sibling
        if prev and prev.type == "comment":
            text = prev.text.decode("utf-8", errors="replace")
            lines = text.split("\n")
            cleaned = []
            for line in lines:
                line = line.strip()
                if line.startswith("*"):
                    line = line[1:].strip()
                if line.startswith("//"):
                    line = line[2:].strip()
                if line.startswith("/**"):
                    line = line[3:].strip()
                if line:
                    cleaned.append(line)
            return "\n".join(cleaned).strip()
        return ""
