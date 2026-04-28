from fastapi import Request

from server.core.registry import RobotRegistry
from server.core.task_dispatcher import TaskDispatcher
from server.core.task_store import TaskStore

def get_registry(request: Request) -> RobotRegistry:
    return request.app.state.server.robot_registry

def get_task_store(request: Request) -> TaskStore:
    return request.app.state.server.task_store

def get_task_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.server.task_dispatcher