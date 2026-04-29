from dataclasses import dataclass
from enum import Enum, auto

class TaskAlreadyAssignedError(Exception):
    pass

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    REJECTED = "REJECTED"

@dataclass
class Task:
    id: str
    aisle_id: str

    aisle_pos: tuple[float, float]
    segment_pos: tuple[float, float]

    status: TaskStatus = TaskStatus.PENDING