import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    # -------------------------
    # Lifecycle
    # -------------------------
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("[WS] Client connected (total=%d)", self.connection_count)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("[WS] Client disconnected (total=%d)", self.connection_count)

    # -------------------------
    # Broadcasting
    # -------------------------
    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            connections = list(self._connections)

        if not connections:
            return

        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning("[WS] Failed sending to client: %s", e)
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    def broadcast_sync(self, message: dict) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))  # create_task is thread-safe
        except RuntimeError:
            logger.debug("[WS] No running event loop; skipping broadcast")

    # -------------------------
    # Helpers
    # -------------------------
    @property
    def connection_count(self) -> int:
        return len(self._connections)