import json
from typing import Any, Dict

def to_jsonschema(schema: Dict[str, Any], anomalies: Dict[str, Any]) -> str:
    """Return a JSON schema with anomalies embedded."""
    # Deep copy to avoid mutating original
    import copy
    output = copy.deepcopy(schema)
    
    if anomalies:
        output["x-anomalies"] = anomalies
        
    return json.dumps(output, indent=2, ensure_ascii=False)

def to_yaml(schema: Dict[str, Any], anomalies: Dict[str, Any]) -> str:
    """Return a YAML string with schema and anomalies."""
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml is required. Install with `pip install .[yaml]`")
        
    output = {
        "schema": schema,
        "anomalies": anomalies
    }
    
    return yaml.dump(output, default_flow_style=False, sort_keys=False)

def to_pydantic(schema: Dict[str, Any], anomalies: Dict[str, Any]) -> str:
    """Generate a Pydantic model representation."""
    lines = [
        "from typing import Optional, List, Dict, Any",
        "from pydantic import BaseModel, Field",
        "",
        "class InferredModel(BaseModel):"
    ]
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    if not properties:
        lines.append("    pass")
        return "\n".join(lines)
        
    for field, field_schema in properties.items():
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]",
            "null": "Any"
        }
        
        # Handle multiple types
        types = field_schema.get("type", "Any")
        if isinstance(types, list):
            types = [t for t in types if t != "null"]
            py_type = type_mapping.get(types[0], "Any") if types else "Any"
        else:
            py_type = type_mapping.get(types, "Any")
            
        is_req = field in required
        if not is_req:
            py_type = f"Optional[{py_type}]"
            
        field_args = []
        if not is_req:
            field_args.append("default=None")
            
        if "description" in field_schema:
            field_args.append(f'description="{field_schema["description"]}"')
            
        field_str = f"Field({', '.join(field_args)})" if field_args else ""
        
        if field_str:
            lines.append(f"    {field}: {py_type} = {field_str}")
        else:
            lines.append(f"    {field}: {py_type}")
            
    return "\n".join(lines)
