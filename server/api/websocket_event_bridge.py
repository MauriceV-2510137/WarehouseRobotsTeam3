from server.api.websocket_manager import WebSocketManager
from server.core.events import Event, AisleReleaseEvent, AisleRequestEvent, HeartbeatEvent, TaskStatusEvent

class WebSocketEventBridge:
    """
    Translates domain Events into WebSocket JSON messages.
    """

    def __init__(self, manager: WebSocketManager) -> None:
        self._manager = manager

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------
    def on_event(self, event: Event) -> None:
        message = self._to_message(event)
        if message:
            self._manager.broadcast_sync(message)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def _to_message(self, event: Event) -> dict | None:
        if isinstance(event, HeartbeatEvent):
            return {
                "type": "robot_heartbeat",
                "data": {
                    "robot_id": event.robot_id,
                    "pose": {
                        "x": event.pose.x,
                        "y": event.pose.y,
                        "theta": event.pose.theta,
                    },
                    "task_id": event.task_id,
                },
            }

        if isinstance(event, TaskStatusEvent):
            return {
                "type": "task_status",
                "data": {
                    "robot_id": event.robot_id,
                    "task_id": event.task_id,
                    "status": event.status.name,
                    "reason": event.reason,
                },
            }

        if isinstance(event, AisleRequestEvent):
            return {
                "type": "aisle_request",
                "data": {
                    "robot_id": event.robot_id,
                    "aisle_id": event.aisle_id,
                    "task_id": event.task_id,
                },
            }

        if isinstance(event, AisleReleaseEvent):
            return {
                "type": "aisle_release",
                "data": {
                    "robot_id": event.robot_id,
                    "aisle_id": event.aisle_id,
                },
            }

        return None