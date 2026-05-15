from typing import Any, Dict, List

def compare_schemas(schema_a: Dict[str, Any], schema_b: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two JSON schemas and return a dictionary of differences."""
    
    props_a = schema_a.get("properties", {})
    props_b = schema_b.get("properties", {})
    
    added_fields = []
    removed_fields = []
    changed_fields = []
    
    # Check for removed and changed fields
    for field, spec_a in props_a.items():
        if field not in props_b:
            removed_fields.append(field)
        else:
            spec_b = props_b[field]
            if spec_a != spec_b:
                changed_fields.append({
                    "field": field,
                    "old": spec_a,
                    "new": spec_b
                })
                
    # Check for added fields
    for field in props_b.keys():
        if field not in props_a:
            added_fields.append(field)
            
    return {
        "added": added_fields,
        "removed": removed_fields,
        "changed": changed_fields
    }
