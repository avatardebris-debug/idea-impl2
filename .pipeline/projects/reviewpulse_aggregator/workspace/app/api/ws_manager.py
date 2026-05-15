import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Active connections mapped by business_id (or "all" for global admin)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, business_id: str):
        await websocket.accept()
        if business_id not in self.active_connections:
            self.active_connections[business_id] = []
        self.active_connections[business_id].append(websocket)

    def disconnect(self, websocket: WebSocket, business_id: str):
        if business_id in self.active_connections:
            if websocket in self.active_connections[business_id]:
                self.active_connections[business_id].remove(websocket)
            if not self.active_connections[business_id]:
                del self.active_connections[business_id]

    async def broadcast_to_business(self, business_id: str, message: dict):
        if business_id in self.active_connections:
            for connection in self.active_connections[business_id]:
                await connection.send_text(json.dumps(message))

ws_manager = ConnectionManager()
