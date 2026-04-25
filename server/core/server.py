from server.core.event_queue import EventQueue
from server.core.aisle_manager import AisleManager
from server.core.events import (
    HeartbeatEvent,
    TaskStatusEvent,
    AisleRequestEvent,
)

class Server:

    def __init__(self, comm):
        self.comm = comm

        self.event_queue = EventQueue()
        self.aisle_manager = AisleManager(lock_timeout=300)  # 5 minute lock timeout

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
        
        # Periodically clean up expired locks
        self.aisle_manager.cleanup_expired_locks()

    def _on_heartbeat(self, event: HeartbeatEvent):
        print(f"[{event.robot_id}] pose={event.pose}")

    def _on_task_status(self, event: TaskStatusEvent):
        print(f"[{event.robot_id}] task={event.task_id} -> {event.status}")
        
        # If robot finished task, release any aisle locks
        if event.status.name in ["COMPLETED", "FAILED", "CANCELLED"]:
            self.aisle_manager.release_robot(event.robot_id)

    def _on_aisle_request(self, event: AisleRequestEvent):
        print(f"[{event.robot_id}] requests aisle {event.aisle_id}")

        # Use AisleManager to determine if access should be granted
        granted = self.aisle_manager.request_aisle(
            robot_id=event.robot_id,
            aisle_id=event.aisle_id,
            task_id=event.task_id
        )
        
        if granted:
            print(f"[AisleManager] GRANTED aisle {event.aisle_id} to robot {event.robot_id}")
        else:
            print(f"[AisleManager] DENIED aisle {event.aisle_id} to robot {event.robot_id} (already locked)")

        self.comm.respond_aisle(
            robot_id=event.robot_id,
            aisle_id=event.aisle_id,
            granted=granted
        )