from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from server.api.dependencies import get_ws_manager
from server.api.websocket_manager import WebSocketManager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, manager: WebSocketManager = Depends(get_ws_manager)) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)