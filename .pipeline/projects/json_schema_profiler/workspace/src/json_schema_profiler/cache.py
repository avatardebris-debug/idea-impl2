import os
import json
import hashlib
from typing import Optional, Any, Dict

CACHE_DIR = os.path.expanduser("~/.json-schema-profiler/cache")

def _hash_file(filepath: str) -> str:
    """Hash file contents using MD5."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def get_cached_result(filepath: str) -> Optional[Dict[str, Any]]:
    """Get cached schema result if file hasn't changed."""
    if not os.path.exists(filepath):
        return None
        
    try:
        mtime = os.path.getmtime(filepath)
        manifest_path = os.path.join(CACHE_DIR, "manifest.json")
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            entry = manifest.get(filepath)
            if entry and entry["mtime"] == mtime:
                # Mtime matches, check hash
                file_hash = _hash_file(filepath)
                if entry["hash"] == file_hash:
                    # Cache hit
                    cache_file = os.path.join(CACHE_DIR, entry["cache_file"])
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r') as cf:
                            return json.load(cf)
    except Exception:
        pass
    return None

def save_cached_result(filepath: str, result: Dict[str, Any]) -> None:
    """Save schema result to cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        manifest_path = os.path.join(CACHE_DIR, "manifest.json")
        
        manifest = {}
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
        mtime = os.path.getmtime(filepath)
        file_hash = _hash_file(filepath)
        cache_file = f"{file_hash}.json"
        
        manifest[filepath] = {
            "mtime": mtime,
            "hash": file_hash,
            "cache_file": cache_file
        }
        
        with open(os.path.join(CACHE_DIR, cache_file), 'w') as f:
            json.dump(result, f)
            
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
    except Exception:
        pass
