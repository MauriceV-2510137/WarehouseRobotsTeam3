from dataclasses import dataclass
from core.task import TaskStatus
from core.pose import Pose

@dataclass
class Event:
    pass

@dataclass
class HeartbeatEvent(Event):
    robot_id: str
    pose: Pose
    task_id: str | None

@dataclass
class TaskStatusEvent(Event):
    robot_id: str
    task_id: str
    status: TaskStatus
    reason: str | None

@dataclass
class AisleRequestEvent(Event):
    robot_id: str
    aisle_id: str
    task_id: str