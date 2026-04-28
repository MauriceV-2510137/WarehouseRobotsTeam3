from datetime import datetime, timedelta

from server.core.registry.robot_record import RobotRecord
from server.core.registry.robot_registry import RobotRegistry
from server.core.registry.robot_server_status import RobotServerStatus
from server.core.events import HeartbeatEvent, TaskStatusEvent, Event
from core.task import TaskStatus

OFFLINE_CUTOFF_S = 4.0 # x seconds without any hearthbeat -> robot set offline

class RobotTracker:
    def __init__(self, registry: RobotRegistry) -> None:
        self._registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_event(self, event: Event) -> None:
        if isinstance(event, HeartbeatEvent):
            self._on_heartbeat(event)
        elif isinstance(event, TaskStatusEvent):
            self._on_task_status(event)

    def update(self) -> None:
        cutoff = datetime.now() - timedelta(seconds=OFFLINE_CUTOFF_S)

        for record in self._registry.get_all():
            if record.status != RobotServerStatus.OFFLINE and record.last_heartbeat < cutoff:
                record.status = RobotServerStatus.OFFLINE

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_heartbeat(self, event: HeartbeatEvent) -> None:
        record = self._get_or_register(event.robot_id)
        record.pose = event.pose
        record.last_heartbeat = datetime.now()
        record.active_task_id = event.task_id

        # Go back online
        if record.status in (RobotServerStatus.OFFLINE, RobotServerStatus.ONLINE) or event.task_id is None:
            record.status = RobotServerStatus.IDLE if not event.task_id else RobotServerStatus.BUSY

    def _on_task_status(self, event: TaskStatusEvent) -> None:
        record = self._registry.get(event.robot_id)
        if record is None:
            return

        if event.status == TaskStatus.IN_PROGRESS:
            record.status = RobotServerStatus.BUSY
            record.active_task_id = event.task_id

        elif event.status in (TaskStatus.DONE, TaskStatus.REJECTED):
            record.status = RobotServerStatus.IDLE
            record.active_task_id = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_or_register(self, robot_id: str) -> RobotRecord:
        if not self._registry.contains(robot_id):
            self._registry.add(RobotRecord(robot_id=robot_id))
        return self._registry.get(robot_id)