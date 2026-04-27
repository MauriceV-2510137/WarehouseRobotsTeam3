from __future__ import annotations

from typing import Callable, List

from server.core.event_queue import EventQueue
from server.core.events import Event, HeartbeatEvent, TaskStatusEvent, AisleRequestEvent
from server.core.registry import RobotRegistry, RobotTracker
from server.core.warehouse import WarehouseMap

class Server:

    def __init__(self, comm):
        self.comm = comm
        self._running = True

        self.robot_registry = RobotRegistry()
        self.robot_tracker = RobotTracker(self.robot_registry)
        
        self.event_queue = EventQueue()
        self._event_listeners: List[Callable[[Event], None]] = []
        self._bind_events()

    # -------------------------
    # Lifecycle
    # -------------------------
    def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return self._running

    # -------------------------
    # Wiring
    # -------------------------
    def _bind_events(self):
        self.comm.set_heartbeat_callback(self.event_queue.publish)
        self.comm.set_task_status_callback(self.event_queue.publish)
        self.comm.set_aisle_request_callback(self.event_queue.publish)

    # -------------------------
    # Events
    # -------------------------

    def add_event_listener(self, callback: Callable[[Event], None]) -> None:
            self._event_listeners.append(callback)
    
    def _process_events(self):
        for event in self.event_queue.poll_all():
            self.robot_tracker.handle_event(event)
            self._handle_event(event)

            for callback in self._event_listeners:
                callback(event)

    def _handle_event(self, event):
        if isinstance(event, HeartbeatEvent):
                self._on_heartbeat(event)

        elif isinstance(event, TaskStatusEvent):
            self._on_task_status(event)

        elif isinstance(event, AisleRequestEvent):
            self._on_aisle_request(event)

    # -------------------------
    # LOGIC
    # -------------------------

    def update(self, dt: float):
        self._process_events()
        self.robot_tracker.update()

    def _on_heartbeat(self, event: HeartbeatEvent):
        print(f"[{event.robot_id}] pose={event.pose}")

    def _on_task_status(self, event: TaskStatusEvent):
        print(f"[{event.robot_id}] task={event.task_id} -> {event.status}")

    def _on_aisle_request(self, event: AisleRequestEvent):
        print(f"[{event.robot_id}] requests aisle {event.aisle_id}")

        # placeholder decision (now just accepting every request)
        self.comm.respond_aisle(
            robot_id=event.robot_id,
            aisle_id=event.aisle_id,
            granted=True
        )