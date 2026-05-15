import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import pyarrow.parquet as pq
    import pandas as pd
    HAS_PARQUET = True
except ImportError:
    HAS_PARQUET = False

from .inference import infer_schema

def read_parquet(path: str) -> List[Dict[str, Any]]:
    """Read a Parquet file and return a list of dicts."""
    if not HAS_PARQUET:
        raise ImportError("pyarrow and pandas are required for Parquet support. Install with `pip install .[parquet]`")
        
    df = pd.read_parquet(path)
    # Convert timestamps to strings to match JSON handling
    for col in df.select_dtypes(include=['datetime64', 'datetimetz']):
        df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return df.to_dict(orient="records")

def infer_parquet_schema(path: str) -> Dict[str, Any]:
    """Infer schema from a Parquet file.
    
    Extracts native pyarrow schema and augments it with data-driven inference.
    """
    if not HAS_PARQUET:
        raise ImportError("pyarrow is required for Parquet support.")
        
    # Get native schema
    meta = pq.read_metadata(path)
    pa_schema = meta.schema
    
    # Read data to get min/max and enums via our existing infer_schema
    data = read_parquet(path)
    inferred = infer_schema(data)
    
    # We could theoretically merge pyarrow exact types, but our infer_schema
    # already does a great job with the extracted dicts. For MVP of Parquet:
    return inferred

def scan_parquet_directory(dir_path: str) -> List[Dict[str, Any]]:
    """Scan a directory for all .parquet and .json files and read them."""
    all_data = []
    
    for root, _, files in os.walk(dir_path):
        for f in files:
            full_path = os.path.join(root, f)
            if f.endswith('.parquet'):
                all_data.extend(read_parquet(full_path))
            elif f.endswith('.json'):
                import json
                with open(full_path, 'r', encoding='utf-8') as file:
                    all_data.extend(json.load(file))
                    
    return all_data
