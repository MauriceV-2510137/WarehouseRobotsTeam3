from server.core.event_queue import EventQueue
from server.core.robot_registry import RobotRegistry
from server.core.events import (
    HeartbeatEvent,
    TaskStatusEvent,
    AisleRequestEvent,
)

class Server:

    def __init__(self, comm):
        self.comm = comm

        self.event_queue = EventQueue()
        self.robot_registry = RobotRegistry()

        self._running = True

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
    def _process_events(self):
        for event in self.event_queue.poll_all():

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

    def _on_heartbeat(self, event: HeartbeatEvent):
        self.robot_registry.update_heartbeat(event.robot_id, event.pose, event.task_id)
        print(f"[{event.robot_id}] pose={event.pose}")

    def _on_task_status(self, event: TaskStatusEvent):
        self.robot_registry.update_task_status(event.robot_id, event.task_id, event.status.name)
        print(f"[{event.robot_id}] task={event.task_id} -> {event.status}")

    def _on_aisle_request(self, event: AisleRequestEvent):
        print(f"[{event.robot_id}] requests aisle {event.aisle_id}")

        # placeholder decision (now just accepting every request)
        granted = True
        if granted:
            self.robot_registry.set_aisle(event.robot_id, event.aisle_id)

        self.comm.respond_aisle(
            robot_id=event.robot_id,
            aisle_id=event.aisle_id,
            granted=granted
        )