from typing import Callable

from server.core.event_queue import EventQueue
from server.core.events import Event, HeartbeatEvent, TaskStatusEvent, AisleRequestEvent, AisleReleaseEvent
from server.core.registry import RobotRegistry, RobotTracker
from server.core.warehouse import WarehouseMap
from server.core.task_dispatcher import TaskDispatcher
from server.core.task_store import TaskStore
from server.core.aisle.aisle_manager import AisleManager
from server.interfaces.server_comm import IServerComm

class Server:

    def __init__(self, comm: IServerComm) -> None:
        self.comm = comm

        self._running = True

        self.robot_registry = RobotRegistry()
        self.robot_tracker = RobotTracker(self.robot_registry)

        self.task_store = TaskStore()
        self.warehouse_map = WarehouseMap()
        self.task_dispatcher = TaskDispatcher(self.robot_registry, self.task_store, self.comm, self.warehouse_map)

        self.aisle_manager = AisleManager(self.comm)
        
        self.event_queue = EventQueue()
        self._event_listeners: list[Callable[[Event], None]] = []
        self._bind_events()
    
    # -------------------------
    # Lifecycle
    # -------------------------
    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    # -------------------------
    # Wiring
    # -------------------------
    def _bind_events(self) -> None:
        self.comm.set_heartbeat_callback(self.event_queue.publish)
        self.comm.set_task_status_callback(self.event_queue.publish)
        self.comm.set_aisle_request_callback(self.event_queue.publish)
        self.comm.set_aisle_release_callback(self.event_queue.publish)

    # -------------------------
    # Events
    # -------------------------
    def add_event_listener(self, callback: Callable[[Event], None]) -> None:
        self._event_listeners.append(callback)
    
    def _process_events(self) -> None:
        for event in self.event_queue.poll_all():
            self.robot_tracker.handle_event(event)
            self.task_store.handle_event(event)
            self.aisle_manager.handle_event(event)
            self._handle_event(event)

            for callback in self._event_listeners:
                callback(event)

    def _handle_event(self, event: Event) -> None:
        if isinstance(event, HeartbeatEvent):
            self._on_heartbeat(event)
        elif isinstance(event, TaskStatusEvent):
            self._on_task_status(event)
        elif isinstance(event, AisleRequestEvent):
            self._on_aisle_request(event)
        elif isinstance(event, AisleReleaseEvent):
            self._on_aisle_release(event)

    # -------------------------
    # LOGIC
    # -------------------------
    def _on_heartbeat(self, event: HeartbeatEvent) -> None:
        print(f"[{event.robot_id}] pose = {event.pose}")

    def _on_task_status(self, event: TaskStatusEvent) -> None:
        print(f"[{event.robot_id}] task = {event.task_id} -> {event.status}")

    def _on_aisle_request(self, event: AisleRequestEvent) -> None:
        print(f"[{event.robot_id}] aisle requested = {event.aisle_id}")

    def _on_aisle_release(self, event: AisleReleaseEvent) -> None:
        print(f"[{event.robot_id}] aisle released = {event.aisle_id}")

    # -------------------------
    # Main loop
    # -------------------------
    def update(self, dt: float) -> None:
        self._process_events()
        self.robot_tracker.update()
        self.aisle_manager.update()
        self.task_dispatcher.try_dispatch()