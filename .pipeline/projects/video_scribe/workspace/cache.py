import sqlite3
import hashlib
import json
import os
from typing import Optional, Dict, Any

class VLMCache:
    def __init__(self, db_path: str = ".vlm_cache.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS frame_cache (
                    hash TEXT PRIMARY KEY,
                    response TEXT
                )
            ''')

    def _hash_frame(self, frame_bytes: bytes) -> str:
        return hashlib.md5(frame_bytes).hexdigest()

    def get(self, frame_bytes: bytes) -> Optional[Dict[str, Any]]:
        hash_val = self._hash_frame(frame_bytes)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT response FROM frame_cache WHERE hash = ?', (hash_val,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, frame_bytes: bytes, response: Dict[str, Any]):
        hash_val = self._hash_frame(frame_bytes)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO frame_cache (hash, response) VALUES (?, ?)',
                (hash_val, json.dumps(response))
            )
