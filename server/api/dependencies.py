from fastapi import Request, WebSocket

from server.core.registry import RobotRegistry
from server.core.task_store import TaskStore
from server.core.task_dispatcher import TaskDispatcher
from server.core.aisle.aisle_manager import AisleManager
from server.core.warehouse import WarehouseMap
from server.api.websocket_manager import WebSocketManager

def get_registry(request: Request) -> RobotRegistry:
    return request.app.state.server.robot_registry

def get_task_store(request: Request) -> TaskStore:
    return request.app.state.server.task_store

def get_task_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.server.task_dispatcher

def get_aisle_manager(request: Request) -> AisleManager:
    return request.app.state.server.aisle_manager

def get_warehouse_map(request: Request) -> WarehouseMap:
    return request.app.state.server.warehouse_map

def get_ws_manager(websocket: WebSocket) -> WebSocketManager:
    return websocket.app.state.ws_manager