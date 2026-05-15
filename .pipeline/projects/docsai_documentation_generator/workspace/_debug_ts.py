import sys
sys.path.insert(0, r'.pipeline\projects\docsai_documentation_generator\workspace')
import tree_sitter_typescript
from tree_sitter import Language, Parser

lang = Language(tree_sitter_typescript.language_typescript())
parser = Parser(lang)

with open(r'.pipeline\projects\docsai_documentation_generator\workspace\tests\sample_project\sample_typescript.ts', 'rb') as f:
    src = f.read()

tree = parser.parse(src)
root = tree.root_node

def dump(node, depth=0, max_depth=6):
    if depth > max_depth:
        return
    text = node.text[:40] if node.text and len(node.text) < 40 else b"..."
    print("  " * depth + str(node.type) + " -> " + repr(text))
    for c in node.children:
        dump(c, depth + 1, max_depth)

# Find the greet function
for child in root.children:
    if child.type == "export_statement":
        for c in child.children:
            if c.type == "function_declaration":
                name_node = c.child_by_field_name("name")
                if name_node and name_node.text == b"greet":
                    print("=== greet ===")
                    dump(c, max_depth=4)
                    print()
                    params = c.child_by_field_name("parameters")
                    if params:
                        print("Params:")
                        for p in params.children:
                            print("  param type:", p.type, "text:", p.text[:30])
                            for nc in p.named_children:
                                print("    nc:", nc.type, nc.text[:30])
                            n = p.child_by_field_name("name")
                            t = p.child_by_field_name("type")
                            print("    field name:", n, "field type:", t)
