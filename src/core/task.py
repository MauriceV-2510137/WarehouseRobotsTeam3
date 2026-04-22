from dataclasses import dataclass
from enum import Enum, auto

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    DONE = auto()

@dataclass
class Task:
    id: str
    shelf_x: float
    shelf_y: float
    base_x: float
    base_y: float
    status: TaskStatus = TaskStatus.PENDING