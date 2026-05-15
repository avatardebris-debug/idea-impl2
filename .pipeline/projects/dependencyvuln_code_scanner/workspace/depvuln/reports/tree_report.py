from typing import Any

class TreeReporter:
    """Renders the dependency tree as an ASCII tree or Graphviz DOT format."""
    
    def generate_ascii(self, tree: dict[str, Any], indent: str = "", is_last: bool = True) -> str:
        """Generate an ASCII representation of the dependency tree."""
        if tree["name"] == "root":
            result = "Project Dependencies\n"
            for i, child in enumerate(tree.get("children", [])):
                is_last_child = i == len(tree["children"]) - 1
                result += self.generate_ascii(child, "", is_last_child)
            return result

        marker = "└── " if is_last else "├── "
        line = f"{indent}{marker}{tree['name']}@{tree['version']}"
        
        # Add vulnerability badges if any
        if "vulns" in tree and tree["vulns"]:
            severities = [v.get("severity", "UNKNOWN") for v in tree["vulns"]]
            if "CRITICAL" in severities:
                line += " [!CRITICAL]"
            elif "HIGH" in severities:
                line += " [!HIGH]"
            elif "MEDIUM" in severities:
                line += " [!MEDIUM]"
            else:
                line += " [!LOW]"
                
        result = line + "\n"
        
        child_indent = indent + ("    " if is_last else "│   ")
        for i, child in enumerate(tree.get("children", [])):
            is_last_child = i == len(tree["children"]) - 1
            result += self.generate_ascii(child, child_indent, is_last_child)
            
        return result
        
    def generate_dot(self, tree: dict[str, Any]) -> str:
        """Generate a Graphviz DOT representation of the dependency tree."""
        lines = ["digraph Dependencies {", '  node [shape=box, style=filled, fillcolor="white"];']
        
        def safe_name(name):
            return name.replace("-", "_").replace(".", "_")
            
        def traverse(node):
            node_id = safe_name(node["name"])
            
            fillcolor = "white"
            if "vulns" in node and node["vulns"]:
                severities = [v.get("severity", "UNKNOWN") for v in node["vulns"]]
                if "CRITICAL" in severities: fillcolor = "red"
                elif "HIGH" in severities: fillcolor = "orange"
                elif "MEDIUM" in severities: fillcolor = "yellow"
                else: fillcolor = "lightyellow"
                
            if node["name"] != "root":
                label = f"{node['name']}\\n{node['version']}"
                lines.append(f'  "{node_id}" [label="{label}", fillcolor="{fillcolor}"];')
                
            for child in node.get("children", []):
                child_id = safe_name(child["name"])
                if node["name"] != "root":
                    lines.append(f'  "{node_id}" -> "{child_id}";')
                traverse(child)
                
        traverse(tree)
        lines.append("}")
        return "\n".join(lines)
