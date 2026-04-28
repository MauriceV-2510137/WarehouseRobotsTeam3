from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes import robots, tasks, aisles
from server.api.routes.websocket import router as ws_router
from server.api.websocket_manager import WebSocketManager
from server.api.websocket_event_bridge import WebSocketEventBridge
from server.core.server import Server

def create_app(server: Server) -> FastAPI:
    app = FastAPI(title="Warehouse Robot API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.server = server

    ws_manager = WebSocketManager()
    app.state.ws_manager = ws_manager

    bridge = WebSocketEventBridge(ws_manager)
    server.add_event_listener(bridge.on_event)

    app.include_router(robots.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(aisles.router, prefix="/api")
    app.include_router(ws_router)

    return app