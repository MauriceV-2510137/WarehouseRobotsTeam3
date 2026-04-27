from fastapi import Request

from server.core.registry import RobotRegistry
from server.core.server import Server

def get_server(request: Request) -> Server:
    return request.app.state.server

def get_registry(request: Request) -> RobotRegistry:
    return request.app.state.server.robot_registry