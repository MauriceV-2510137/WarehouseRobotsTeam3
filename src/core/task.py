from dataclasses import dataclass
from enum import Enum, auto

class TaskAlreadyAssignedError(Exception):
    pass

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    DONE = auto()
    REJECTED = auto()

@dataclass
class Task:
    id: str
    aisle_id: str

    aisle_pos: tuple[float, float]
    segment_pos: tuple[float, float]

    status: TaskStatus = TaskStatus.PENDING