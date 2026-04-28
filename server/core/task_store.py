from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from core.task import TaskStatus
from server.core.events import Event, TaskStatusEvent

@dataclass
class TaskRecord:
    task_id: str
    aisle: int
    shelf: int
    status: TaskStatus = field(default=TaskStatus.PENDING)
    robot_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class TaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}

    def add(self, record: TaskRecord) -> None:
        self._tasks[record.task_id] = record

    def get(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)

    def get_all(self) -> List[TaskRecord]:
        return list(self._tasks.values())

    def handle_event(self, event: Event) -> None:
        if not isinstance(event, TaskStatusEvent):
            return
        record = self._tasks.get(event.task_id)
        if record:
            record.status = event.status
            record.updated_at = datetime.now()