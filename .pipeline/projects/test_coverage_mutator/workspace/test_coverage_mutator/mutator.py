"""Mutation testing logic."""

import ast

class MutatorVisitor(ast.NodeTransformer):
    """AST visitor that applies basic mutations."""
    
    def __init__(self):
        self.mutations_applied = 0
        
    def visit_Compare(self, node):
        """Mutate comparison operators (e.g., == to !=)."""
        self.generic_visit(node)
        
        # Just swap the first operator for demonstration
        if not node.ops:
            return node
            
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            node.ops[0] = ast.NotEq()
            self.mutations_applied += 1
        elif isinstance(op, ast.NotEq):
            node.ops[0] = ast.Eq()
            self.mutations_applied += 1
        elif isinstance(op, ast.Gt):
            node.ops[0] = ast.LtE()
            self.mutations_applied += 1
        elif isinstance(op, ast.Lt):
            node.ops[0] = ast.GtE()
            self.mutations_applied += 1
            
        return node


def mutate_source_code(source: str) -> str:
    """Parse python source, apply mutations, and unparse back to source."""
    tree = ast.parse(source)
    visitor = MutatorVisitor()
    mutated_tree = visitor.visit(tree)
    
    if visitor.mutations_applied == 0:
        return source
        
    # ast.unparse requires Python 3.9+
    return ast.unparse(mutated_tree)
