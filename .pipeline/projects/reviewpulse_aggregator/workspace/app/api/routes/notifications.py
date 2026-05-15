from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.ws_manager import ws_manager

router = APIRouter()

@router.websocket("/ws/notifications/{business_id}")
async def websocket_endpoint(websocket: WebSocket, business_id: str):
    await ws_manager.connect(websocket, business_id)
    try:
        while True:
            # We don't expect the client to send much, but keep the connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, business_id)
